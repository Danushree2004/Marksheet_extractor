import uvicorn
from app.routes import app  # noqa: F401

# This is the main starting point of the application
# I'm keeping this file very simple and putting the logic in the 'app' folder
if __name__ == "__main__":
    # Starting the server with hot-reload disabled
    # PyTorch/EasyOCR don't work well with uvicorn's hot-reload on Windows
    print("Starting the Marksheet Extraction API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
