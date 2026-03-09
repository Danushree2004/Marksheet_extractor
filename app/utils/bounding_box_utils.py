from typing import List, Dict, Any, Optional

def find_best_bbox(target_text: str, ocr_metadata: List[Dict[str, Any]]) -> Optional[List[List[float]]]:
    """
    Tries to find the bounding box in the OCR metadata that most likely corresponds 
    to the target_text extracted by the LLM.
    """
    if not target_text or not ocr_metadata:
        return None
        
    target_text = target_text.lower().strip()
    
    # 1. Exact match
    for item in ocr_metadata:
        if target_text == item["text"].lower().strip():
            return item["bbox"]
            
    # 2. Substring match
    for item in ocr_metadata:
        if target_text in item["text"].lower().strip() or item["text"].lower().strip() in target_text:
            return item["bbox"]
            
    # 3. Fuzzy match (very basic)
    # If the target is long, it might be split across multiple OCR boxes.
    # For now, we just return the first one that matches any significant part.
    if len(target_text) > 3:
        for item in ocr_metadata:
            # Check if at least 50% of the target text is in the OCR box
            if item["text"].lower().strip() in target_text and len(item["text"]) > 3:
                return item["bbox"]

    return None

def apply_bounding_boxes(structured_data: Dict[str, Any], ocr_metadata: List[Dict[str, Any]]):
    """
    Recursively steps through the structured JSON and adds bounding boxes 
    by matching values against raw OCR metadata.
    """
    # 1. Handle Candidate Details
    candidate_details = structured_data.get("candidate_details", {})
    for key, field_data in candidate_details.items():
        if isinstance(field_data, dict) and "value" in field_data:
            field_data["bounding_box"] = find_best_bbox(field_data["value"], ocr_metadata)

    # 2. Handle Academic Details (Subjects)
    academic_details = structured_data.get("academic_details", {})
    subjects = academic_details.get("subjects", [])
    for subject_row in subjects:
        for key, field_data in subject_row.items():
            if isinstance(field_data, dict) and "value" in field_data:
                field_data["bounding_box"] = find_best_bbox(field_data["value"], ocr_metadata)
    
    # 3. Handle Overall Summary
    for key, field_data in academic_details.items():
        if key != "subjects" and isinstance(field_data, dict) and "value" in field_data:
            field_data["bounding_box"] = find_best_bbox(field_data["value"], ocr_metadata)
