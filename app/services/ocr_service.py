import easyocr
import numpy as np
from PIL import Image
from typing import Tuple, List, Dict, Any
from app.config import OCR_LANGUAGES

# --- Global OCR Reader ---
# Creating the reader once at the start because it's heavy to load.
# This will trigger the model download (~100MB) on first run.
_reader = None


def get_ocr_reader():
    """
    Returns the EasyOCR reader.
    Using 'global' so we don't reload the models for every request.
    """
    global _reader
    if _reader is None:
        print("[PROCESS] Initializing EasyOCR engine...")
        # Forcing gpu=False so it works on everyone's laptop.
        _reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        print("[SUCCESS] EasyOCR is ready to go.")
    return _reader


def extract_text_from_image(
    image_file_path: str
) -> Tuple[str, float, List[Dict[str, Any]]]:
    """
    Takes an image, runs OCR, and returns:
    1. Full reconstructed text (str)
    2. Average confidence (float)
    3. Raw metadata like bounding boxes (List[Dict])
    """
    try:
        reader = get_ocr_reader()
        
        # Load the image
        img = Image.open(image_file_path)
        
        # --- Optimize image size for faster processing ---
        # Resize if image is too large (maintaining aspect ratio)
        max_width = 2400
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # --- Image Pre-processing for better OCR ---
        # 1. Convert to Grayscale
        img = img.convert('L')
        
        # 2. Enhance Contrast (helps remove light watermarks)
        from PIL import ImageEnhance
        img = ImageEnhance.Contrast(img).enhance(1.5)
        
        # Convert to numpy array (EasyOCR expects this)
        img_array = np.array(img)
        
        # Close the image to release the file handle
        img.close()
        
        # Perform OCR - optimized for speed
        # Each result is [bbox_coords, text, confidence]
        raw_results: Any = reader.readtext(img_array, detail=1, contrast_ths=0.1)
        
        if not raw_results:
            return "", 0.0, []
            
        # Format raw results for downstream use
        metadata: List[Dict[str, Any]] = []
        for res in raw_results:
            bbox_coords = res[0]  # type: ignore
            text = res[1]  # type: ignore
            confidence = res[2]  # type: ignore
            metadata.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": [[float(p[0]), float(p[1])] for p in bbox_coords]
            })
            
        # --- Robust Line Reconstruction ---
        # Sort by top coordinate first
        raw_results.sort(key=lambda x: x[0][0][1])  # type: ignore
        
        test_lines: List[str] = []
        if raw_results:
            current_line = [raw_results[0]]
            for i in range(1, len(raw_results)):
                # Increased buffer to 30px for high-res images
                # Check vertical distance between block and line
                avg_top = (
                    sum([res[0][0][1] for res in current_line])  # type: ignore
                    / len(current_line)
                )
                if abs(raw_results[i][0][0][1] - avg_top) < 30:  # type: ignore
                    current_line.append(raw_results[i])
                else:
                    # Sort the completed line by X-coordinate
                    current_line.sort(key=lambda x: x[0][0][0])  # type: ignore
                    line_text = "  |  ".join(
                        [res[1] for res in current_line]  # type: ignore
                    )
                    test_lines.append(line_text)
                    current_line = [raw_results[i]]
            
            # Catch the remaining line
            current_line.sort(key=lambda x: x[0][0][0])  # type: ignore
            test_lines.append("  |  ".join([res[1] for res in current_line]))  # type: ignore

        full_document_text = "\n".join(test_lines)
        
        # Calculate scores
        conf_scores = [float(res[2]) for res in raw_results]  # type: ignore
        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 0.0
        
        print(f"[OCR] Reconstructed {len(test_lines)} logical lines of text.")
        return full_document_text, avg_conf, metadata
        
    except Exception as e:
        msg = f"[OCR ERROR] Failed reading image: {str(e)}"
        print(msg)
        raise Exception(f"Image OCR failed: {str(e)}")


def extract_text_from_pdf(
    pdf_file_path: str
) -> Tuple[str, float, List[Dict[str, Any]]]:
    """
    EasyOCR doesn't read PDFs, so convert PDF to image first.
    Only process first page (marksheets are usually one page).
    """
    from pdf2image import convert_from_path
    import tempfile
    import os
    
    try:
        print("[PDF] Converting first page of PDF to image...")
        
        # Converting page 1 only
        pages = convert_from_path(pdf_file_path, first_page=1, last_page=1)
        
        if not pages:
            msg = "PDF conversion failed - file may be corrupt"
            raise Exception(msg)
        
        # Saving the page as a temporary PNG so we can run OCR on it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp_img_path = tmp.name
            pages[0].save(tmp_img_path, 'PNG')
        
        # Run the standard image OCR
        text, confidence, metadata = extract_text_from_image(tmp_img_path)
        
        # Cleanup the temp image so we don't leave junk on the computer
        if os.path.exists(tmp_img_path):
            os.remove(tmp_img_path)
            
        return text, confidence, metadata
        
    except Exception as e:
        print(f"[PDF ERROR] Failed to process PDF: {str(e)}")
        raise Exception(f"PDF OCR failed: {str(e)}")
