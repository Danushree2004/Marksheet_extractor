import re

# This file contains some helper functions to clean up the text before
# we send it to Gemini. OCR output is often very messy with extra spaces.

def clean_ocr_text(original_text: str) -> str:
    """
    Cleans up the text from EasyOCR. 
    I'm not doing anything too aggressive here because I want to keep 
    the original context for the LLM.
    """
    if not original_text:
        return ""
    
    # 1. Getting rid of multiple spaces (EasyOCR often adds these for margins)
    text = re.sub(r' +', ' ', original_text)
    
    # 2. Cleaning up common noisy symbols like vertical pipes '|' 
    # Replacing with space so we don't accidentally join two numbers together
    text = text.replace('|', ' ')
    
    # 3. Fixing extra newlines but keeping some structure
    # I'm replacing 3+ newlines with just 2 so it doesn't waste prompt space.
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # 4. Tidying up lines
    # Stripping whitespace from the start/end of every line
    lines = [l.strip() for l in text.split('\n')]
    
    # Join them back and strip the whole document
    cleaned_result = '\n'.join(lines).strip()
    
    # NOTE: I decided not to fix things like '0' vs 'O' or '1' vs 'l' manually 
    # because Gemini is actually better at understanding the context 
    # (e.g., if it's in a Roll Number vs a Name).
    
    return cleaned_result


def extract_text_snippet(full_text: str, chars: int = 150) -> str:
    """
    Just a helper to show a little bit of the text in the console logs.
    It prevents thousands of lines of text from flooding the terminal.
    """
    if len(full_text) <= chars:
        return full_text
    
    return full_text[:chars].replace('\n', ' ') + "..."
