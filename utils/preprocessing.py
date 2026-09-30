import re

MAX_INPUT_LENGTH = 500  # Character limit to prevent API abuse/memory overflow

def validate_and_sanitize_input(text: str) -> dict:
    """
    Validates and sanitizes raw input text from the user/API request.
    
    Returns:
        dict: {"valid": bool, "sanitized_text": str, "error": str or None}
    """
    if text is None:
        return {"valid": False, "sanitized_text": "", "error": "Input text cannot be null."}
    
    # Strip leading/trailing whitespace
    sanitized = text.strip()
    
    if not sanitized:
        return {"valid": False, "sanitized_text": "", "error": "Please enter some text to convert."}
    
    if len(sanitized) > MAX_INPUT_LENGTH:
        return {
            "valid": False, 
            "sanitized_text": "", 
            "error": f"Input exceeds maximum allowed length of {MAX_INPUT_LENGTH} characters."
        }
    
    # Normalize multiple internal spaces/newlines to a single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    return {"valid": True, "sanitized_text": sanitized, "error": None}