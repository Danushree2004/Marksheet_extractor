import os
import tempfile
from fastapi import UploadFile, HTTPException
from app.config import MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS

# This utility file handles the boring stuff: 
# making sure the file is okay and saving it to a temp folder so we can process it.

def validate_file(my_file: UploadFile) -> None:
    """
    Check if the uploaded file is valid.
    I'm checking both the extension and the file size.
    """
    # 1. Check Extension
    filename = my_file.filename or ""
    extension = filename.split(".")[-1].lower()
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Sorry, only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
        )
    
    # 2. Check File Size
    # I'm using seek(0, 2) to jump to the end of the file to calculate its size.
    # Then seek(0) to reset it so it can be read later.
    my_file.file.seek(0, 2)
    current_size = my_file.file.tell()
    my_file.file.seek(0)
    
    if current_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File is too big! Please keep it under {max_mb:.0f}MB."
        )
    
    print(f"[FILE OK] {filename} is valid. Size: {current_size / 1024:.1f} KB")


def save_upload_file_tmp(upload_file: UploadFile) -> str:
    """
    Saves the file to a temporary location so EasyOCR can read it.
    """
    try:
        ext = upload_file.filename.split(".")[-1].lower()
        
        # Using tempfile.NamedTemporaryFile so the OS handles creating a unique name
        # delete=False because we want to keep it until we manually unlink it
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        
        # Read the upload and write to the temp file
        file_bytes = upload_file.file.read()
        temp.write(file_bytes)
        temp.close()
        
        print(f"[TEMP] File saved at: {temp.name}")
        return temp.name
        
    except Exception as err:
        print(f"[ERROR] Failed to save temp file: {str(err)}")
        raise HTTPException(status_code=500, detail="Could not save file internally.")


def cleanup_temp_file(path_to_delete: str) -> None:
    """
    Deletes the temp file. 
    It's important to call this so we don't leak files on the server.
    Includes retry mechanism for Windows file locking issues.
    """
    import time
    
    max_retries = 3
    retry_delay = 0.5  # seconds
    
    for attempt in range(max_retries):
        try:
            if os.path.exists(path_to_delete):
                os.remove(path_to_delete)
                print(f"[CLEANUP] Deleted temp file: {path_to_delete}")
                return  # Success, exit
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"[CLEANUP] File locked, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print(f"[WARNING] Manual cleanup failed after {max_retries} attempts: {path_to_delete}")
        except Exception as e:
            print(f"[WARNING] Manual cleanup failed for {path_to_delete}: {e}")
            return


def get_file_type(fname: str) -> str:
    """
    Simple helper to check if we are dealing with a PDF or an Image.
    """
    e = fname.split(".")[-1].lower()
    if e == "pdf":
        return "pdf"
    elif e in ["jpg", "jpeg", "png"]:
        return "image"
    return "unknown"
