import mimetypes
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response

from open_webui.config import UPLOAD_DIR
from open_webui.storage.provider import Storage
from open_webui.utils.auth import get_admin_user

router = APIRouter()

@router.get("/{path:path}")
async def get_file(path: str, admin=Depends(get_admin_user)):
    """Serve files from storage with authentication"""
    try:
        # Get file path from storage provider
        file_path = Storage.get_file(path)

        # If file_path doesn't start with UPLOAD_DIR, construct the full path
        if not str(file_path).startswith(str(UPLOAD_DIR)):
            file_path = os.path.join(UPLOAD_DIR, os.path.basename(file_path))

        # Convert to Path object and resolve to absolute path
        file_path = Path(file_path).resolve()

        # Verify file exists and is within UPLOAD_DIR
        upload_dir = Path(UPLOAD_DIR).resolve()
        if not file_path.is_file() or not str(file_path).startswith(str(upload_dir)):
            raise FileNotFoundError(f"File not found: {path}")

        # Read file contents
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except OSError as e:
            raise IOError(f"Error reading file {path}: {e}")

        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(path)
        if not content_type:
            content_type = "application/octet-stream"

        return Response(content=content, media_type=content_type)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except Exception as e:
        print(f"Error serving file {path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
