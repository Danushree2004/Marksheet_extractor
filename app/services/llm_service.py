import json
import warnings
from typing import Dict, Any, Optional
from PIL import Image

# Suppress deprecation warning BEFORE importing
warnings.filterwarnings("ignore", category=DeprecationWarning)
import google.generativeai as genai  # type: ignore

from app.config import GEMINI_API_KEY, GEMINI_TEMPERATURE
GEMINI_MODEL = "gemini-flash-latest"

# Setting up the Gemini API key
genai.configure(api_key=GEMINI_API_KEY)  # type: ignore


def create_prompt(messy_text: str) -> str:
    """
    This is where I define the instructions for Gemini.
    I'm telling it exactly what fields I need and how the JSON should look.
    """
    
    # Using a clear, structured prompt to get better results from the model.
    # I found that giving it a specific JSON template works best.
    prompt = f"""TASK: You are an expert at extracting data from academic marksheets/answer sheets. 
Extract ALL educational information from the image and OCR text below.

===== CRITICAL EXTRACTION RULES =====

1. ROLL NUMBER / REGISTRATION NUMBER (CRITICAL - MUST FIND):
   - Search for: "Roll No", "Reg No", "REG NO", "Register No", "Register", "Enrollment", "ID", "Registration"
   - This field often appears in a table with spaced-out characters (e.g., "2 5 M C R 0 1 9" = "25MCR019")
   - Look for ANY identifier number - could be 6-12 digits/characters, or alphanumeric
   - Check RIGHT side of document, in header tables, and all margins
   - If you see spaced numbers/letters, COMBINE THEM: "2 5 M C R" = "25MCR"
   - Extract BOTH the combined form and spaces - capture the actual value
   - If found in OCR as spaced characters, reconstruct into single string
   - Even partial numbers with high confidence are better than "null"

2. MARKS EXTRACTION (MOST IMPORTANT - MUST BE COMPLETE):
   - Look for question labels in PART-A: 1, 2, 3... 10. Extract marks from the column "Obtained Marks".
   - Look for question labels in PART-B: 11, 12, 13, 14, 15, 16. 
   - Note that Part B questions can have sub-parts (i, ii). Extract and sum them for the question total.
   - For example, if Q11 has i) 10, then Q11 total is 10. If Q16 has i) 5 and ii) 5, Q16 total is 10.
   - If a cell contains a DASH "-" or EM DASH "—", return that dash exactly as "-" (NOT as 0 or empty)
   - The frontend will convert dashes to empty cells automatically
   - Search for totals: "TOTAL", "Grand Total", "Total Marks in Words" followed by numbers
   - Part A marks: Q1-Q10 (Max 2 each, Total 20)
   - Part B marks: Q11-Q16 (Max 10 each, but note that the "TOTAL" for Part B is often capped or summed differently - extract what is written in the "TOTAL" box for Part B)
   - In the attached image, Part B Questions are 11, 12, 13, 14, 15, 16
   - CRITICAL: Extract EVERY question mark - do NOT skip any - even if it's a dash "-"
   - Return dashes as "-" string, NOT as null or 0

3. TOTALS ANALYSIS:
   - "TOTAL" for PART-A: Look for the value below Q10 (e.g., "20")
   - "TOTAL" for PART-B: Look for the value in the "TOTAL" box in the Part B section (e.g., "30")
   - "Grand Total": Look for the value next to "Grand Total" (e.g., "50")
   - Check the circled number (e.g., "50") as it usually represents the confirmed Grand Total

4. STUDENT NAME: Extract the student's full name (e.g., "V.S.Danushree")

5. REGISTER NUMBER: Extract accurately (e.g., "25MCR019")

6. INSTITUTION: Extract college/university/school name

===== OCR TEXT TO ANALYZE =====
{messy_text}

===== EXTRACTION STRATEGY =====
- For ROLL NUMBER: Extract even if unclear or spaced - remove spaces and combine. Set confidence to 0.9-1.0 for clear numbers.
- For MARKS: Extract EVERY question Q1-Q10 (Part A) and Q11-Q16 (Part B) found - MUST return ALL 16 positions.
  - If a question is not visible/found in the marksheet, put "-" for that question's obtained_marks.
  - For Part B, sum sub-parts (i, ii) if applicable to get the question total.
  - ARITHMETIC: If marks are written as an addition like "6+1" or "5+2", you MUST calculate the sum (e.g., "7") and return only the final sum.
  - Example: [Q11:8, Q12:"-", Q13:7, Q14:"-"] - all positions returned even if some are dashes.
- For DASHES: If OCR shows "-" or "—", return it as "-" string (NOT 0, NOT empty string, NOT null).
- For TOTALS: Always search for sum, total, obtained marks values (Part A Total, Part B Total, Grand Total).
- CRITICAL: All 10 Part A questions MUST be in array, all 6 Part B questions MUST be in array - never omit.
- If unsure about a value, extract your best guess with confidence 0.6-0.8 rather than leaving out the question entirely.
- NEVER omit a question position from the array - always return complete fixed-length arrays.

===== REQUIRED JSON OUTPUT (EXACT FORMAT) =====
{{
  "candidate_details": {{
    "name": {{"value": "EXTRACT STUDENT NAME", "confidence": 0.9}},
    "roll_number": {{"value": "EXTRACT REGISTER NO", "confidence": 0.7}},
    "register_number": {{"value": "EXTRACT REGISTER NO", "confidence": 0.7}},
    "programme": {{"value": "e.g. MCA", "confidence": 0.0}},
    "branch_semester": {{"value": "e.g. Computer Applications & I", "confidence": 0.0}},
    "institution": {{"value": "EXTRACT COLLEGE NAME", "confidence": 0.9}}
  }},
  "exam_marks": {{
    "part_a": {{
      "max_marks": {{"value": "20", "confidence": 1.0}},
      "obtained_marks": {{"value": "PART A TOTAL", "confidence": 0.8}},
      "questions": [
        {{"question_no": {{"value": "1", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q1 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "2", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q2 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "3", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q3 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "4", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q4 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "5", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q5 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "6", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q6 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "7", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q7 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "8", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q8 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "9", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q9 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "10", "confidence": 1.0}}, "max_marks": {{"value": "2", "confidence": 1.0}}, "obtained_marks": {{"value": "Q10 MARKS", "confidence": 0.7}}}}
      ]
    }},
    "part_b": {{
      "max_marks": {{"value": "40", "confidence": 1.0}},
      "obtained_marks": {{"value": "PART B TOTAL (SUM OF Q11-Q16 OR WRITTEN TOTAL)", "confidence": 0.8}},
      "questions": [
        {{"question_no": {{"value": "11", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q11 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "12", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q12 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "13", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q13 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "14", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q14 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "15", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q15 MARKS", "confidence": 0.7}}}},
        {{"question_no": {{"value": "16", "confidence": 1.0}}, "max_marks": {{"value": "10", "confidence": 1.0}}, "obtained_marks": {{"value": "Q16 MARKS", "confidence": 0.7}}}}
      ]
    }}
  }},
  "exam_totals": {{
    "part_a_total": {{"value": "SUM OF Q1-Q10", "confidence": 0.8}},
    "part_b_total": {{"value": "WRITTEN TOTAL FOR PART B", "confidence": 0.8}},
    "grand_total": {{"value": "SUM OF PART A + PART B", "confidence": 0.8}},
    "max_marks": {{"value": "50", "confidence": 1.0}}
Start with {{ and end with }} 
Each string value must be in quotes. Use null only if absolutely no data found.
"""
    return prompt


def structure_data_with_llm(ocr_output: str,
                            image_path: Optional[str] = None
                            ) -> Dict[str, Any]:
    """
    This function sends the data to Gemini for organization.
    If image_path is provided, we use Gemini's Vision capabilities for
    better accuracy.
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)  # type: ignore
        
        # 1. Prepare visual/textual input
        # If we have the image, we send it directly to Gemini.
        # This solves the "messy OCR" problem because the AI sees
        # the layout itself.
        prompt_with_instructions = create_prompt(ocr_output)
        
        content_items: list[Any] = [prompt_with_instructions]
        
        if image_path:
            img = Image.open(image_path)
            
            # --- AGGRESSIVE OPTIMIZATION FOR 20s RESPONSE ---
            # EasyOCR is likely the bottleneck. We'll skip manual OCR and 
            # let Gemini Vision do everything if we have the image.
            # Downsample image more aggressively for faster API transmission
            max_width = 1024 
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)),
                                  Image.Resampling.LANCZOS)
            
            # Convert to RGB (Gemini requirement) and optimize quality
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            content_items.append(img)
            
            msg = (f"[AI] Calling Gemini Vision ({GEMINI_MODEL}) FAST mode...")
            print(msg)
            
            # 2. Call the API WHILE THE IMAGE IS OPEN
            # Try 1.5-flash first (higher quota), then 2.5-flash as fallback
            try:
                raw_response = model.generate_content(
                    content_items,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1, # Lower temperature for faster/more consistent results
                    )
                )
            except Exception as api_err:
                error_str = str(api_err).lower()
                if "429" in error_str or "quota" in error_str:
                    # If 1.5 flash failed, and it's 1.5, try 1.0 or another variant?
                    # Actually, if the current model is 1.5, we should stay 1.5 but maybe inform user.
                    # If user is hitting 20 request limit, they are likely using 2.5 or 2.0 experimental.
                    raise api_err
                raise api_err
            
            # Close the image AFTER the API call returns
            try:
                img.close()
            except:
                pass
        else:
            msg = (f"[AI] Calling Gemini Text ({GEMINI_MODEL}) "
                   "for data structuring...")
            print(msg)

            # 2. Call the API for text-only
            raw_response = model.generate_content(
                content_items,
                generation_config=genai.types.GenerationConfig(  # type: ignore
                    temperature=GEMINI_TEMPERATURE,
                )
            )
        
        text_result = raw_response.text.strip()
        
        # Clean up Markdown wrapper
        if "```json" in text_result:
            text_result = text_result.split("```json")[1].split("```")[0].strip()
        elif "```" in text_result:
            text_result = text_result.split("```")[1].split("```")[0].strip()
            
        final_data = json.loads(text_result)
        
        print("[AI] Data extracted successfully from image context.")
        print(f"[DEBUG] Extracted keys: {final_data.keys()}")
        if "exam_marks" in final_data:
            print(f"[DEBUG] exam_marks found with keys: {final_data.get('exam_marks', {}).keys()}")
        else:
            print("[DEBUG] exam_marks NOT found in response!")
        
        return final_data
        
    except json.JSONDecodeError:
        print("[AI ERROR] Gemini didn't return valid JSON.")
        raise Exception("Failed to parse AI response into JSON.")
        
    except Exception as e:
        error_str = str(e)
        print(f"[AI ERROR] Gemini API call failed: {error_str}")
        
        # Check for quota errors
        if "429" in error_str or "quota" in error_str.lower():
            raise Exception(
                "❌ API QUOTA EXCEEDED: Your Gemini API has reached "
                "its daily limit (20 requests). To continue:\n"
                "1. ENABLE BILLING: "
                "https://console.cloud.google.com/billing\n"
                "2. OR wait until tomorrow for quota reset\n"
                "Paid plans have higher limits and cost only a few cents."
            )
        elif "401" in error_str or "unauthorized" in error_str.lower():
            raise Exception(
                "❌ INVALID API KEY: Your GEMINI_API_KEY in .env "
                "is invalid or expired. "
                "Get a new one from https://aistudio.google.com/"
            )
        
        raise Exception(f"AI Extraction Error: {error_str}")
