import mimetypes
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
