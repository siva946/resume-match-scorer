import magic
from fastapi import UploadFile, HTTPException
from config import settings
from logger import logger

async def validate_pdf_upload(file: UploadFile) -> bytes:
    """Validate PDF file upload with security checks"""
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Check MIME type using python-magic
    try:
        mime = magic.from_buffer(content, mime=True)
        if mime not in settings.allowed_file_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {mime}")
    except Exception as e:
        logger.error(f"MIME type validation failed: {e}")
        raise HTTPException(status_code=400, detail="Could not validate file type")
    
    # Check for malicious content (basic check)
    if b'<script' in content.lower() or b'javascript:' in content.lower():
        raise HTTPException(status_code=400, detail="Potentially malicious content detected")
    
    return content

def sanitize_string(text: str, max_length: int = 10000) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_email(email: str) -> str:
    """Basic email validation"""
    email = email.strip().lower()
    if '@' not in email or '.' not in email.split('@')[1]:
        raise HTTPException(status_code=400, detail="Invalid email format")
    if len(email) > 255:
        raise HTTPException(status_code=400, detail="Email too long")
    return email
