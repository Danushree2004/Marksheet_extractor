import os
from typing import List
from datetime import datetime
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Body, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Marksheet Extractor API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

from app.services.llm_service import structure_data_with_llm
from app.utils.file_handler import (
    validate_file, save_upload_file_tmp, cleanup_temp_file
)
from app.utils.excel_exporter import export_to_excel, export_multiple_to_excel
from app.auth import (
    users_collection, history_collection, UserCreate, UserLogin, 
    get_password_hash, verify_password, create_access_token, get_current_user
)

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    await users_collection.insert_one(user_dict)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/user/me")
async def get_me(current_email: str = Depends(get_current_user)):
    user = await users_collection.find_one({"email": current_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user["username"],
        "email": user["email"]
    }

@router.get("/history")
async def get_history(current_email: str = Depends(get_current_user)):
    cursor = history_collection.find({"user_email": current_email}).sort("timestamp", -1)
    results = await cursor.to_list(length=100)
    for res in results:
        res["_id"] = str(res["_id"])
    return results

@router.post("/extract")
async def extract_marksheet(
    file: UploadFile = File(...),
    current_email: str = Depends(get_current_user)
):
    temp_path = None
    try:
        validate_file(file)
        temp_path = save_upload_file_tmp(file)
        print(f"[PROCESS] Starting FAST extraction for {current_email}...")
        
        extracted_data = structure_data_with_llm("", temp_path)
        
        # Save to history with user email
        history_entry = {
            "user_email": current_email,
            "data": extracted_data,
            "filename": file.filename,
            "timestamp": datetime.utcnow()
        }
        await history_collection.insert_one(history_entry)
        
        return extracted_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)

@router.post("/export-excel")
async def export_excel_endpoint(data: dict = Body(...), current_email: str = Depends(get_current_user)):
    try:
        excel_io = export_to_excel(data)
        temp_filename = f"marksheet_{datetime.now().timestamp()}.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(excel_io.read())
        return FileResponse(
            path=temp_filename, filename=temp_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    # Optional: minimal fallback if frontend is missing
    @app.get("/")
    async def root():
        return {"message": "Marksheet Extractor API"}
