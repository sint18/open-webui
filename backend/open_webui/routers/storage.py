from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from open_webui.storage.provider import Storage
from open_webui.utils.auth import get_admin_user

router = APIRouter()

@router.get("/{path:path}")
async def get_file(path: str, admin=Depends(get_admin_user)):
    """Serve files from storage with authentication"""
    try:
        content = Storage.get_file(path)
        print(content)
        # Determine content type (you might want to store this with the file)
        content_type = "image/jpeg"  # Or use mimetypes library to guess
        return Response(content=content, media_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )