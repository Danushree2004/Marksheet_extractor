import os
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.llm_service import structure_data_with_llm
from app.utils.file_handler import (
    validate_file, save_upload_file_tmp, cleanup_temp_file
)
from app.utils.excel_exporter import export_to_excel, export_multiple_to_excel
from app import app

router = APIRouter()

@app.post("/extract")
async def extract_marksheet(file: UploadFile = File(...)):
    """Extract data from a single marksheet image."""
    temp_path = None
    try:
        validate_file(file)
        temp_path = save_upload_file_tmp(file)
        print(f"[PROCESS] Starting FAST extraction (20s target)...")
        # We pass an empty string for ocr_output because we are letting 
        # Gemini Vision handle the image directly to save time.
        extracted_data = structure_data_with_llm("", temp_path)
        return extracted_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Extraction failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        )
    finally:
        if temp_path:
            cleanup_temp_file(temp_path)

@app.post("/export-excel")
async def export_excel_endpoint(data: dict = Body(...)):
    """Export extracted marksheet data to an Excel file."""
    try:
        excel_io = export_to_excel(data)
        temp_filename = "marksheet_data.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(excel_io.read())
        return FileResponse(
            path=temp_filename, filename=temp_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export-batch-excel")
async def export_batch_endpoint(data_list: List[dict] = Body(...)):
    """Export multiple marksheets to a single Excel file."""
    try:
        print(f"[EXPORT] Generating Excel for {len(data_list)} items...")
        excel_io = export_multiple_to_excel(data_list)
        temp_filename = "marksheet_batch_data.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(excel_io.read())
        return FileResponse(
            path=temp_filename, filename=temp_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )

if os.path.exists("frontend"):
    app.mount(
        "/", StaticFiles(directory="frontend", html=True), name="frontend"
    )
