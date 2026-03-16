import os
import re

from fastapi import UploadFile, HTTPException

from config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


async def save_upload(file: UploadFile) -> str:
    """Sanitize filename, validate size, write to disk. Returns filepath."""
    filename = re.sub(r'[^\w\s\-.]', '', file.filename).strip()
    if not filename:
        filename = 'upload'
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail='File too large. Maximum size is 100MB.')

    with open(filepath, 'wb') as f:
        f.write(content)

    return filepath
