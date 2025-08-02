import os
import uuid
import mimetypes
from typing import BinaryIO

from open_webui.storage.provider import Storage
from open_webui.models.files import FileForm, FileModel, Files

def save_bytes_as_file(
    data: BinaryIO,
    original_filename: str,
    content_type: str,
    metadata: dict,
    user,
) -> FileModel:
    # derive extension and sanitized name
    ext = mimetypes.guess_extension(content_type) or ""
    name = os.path.basename(original_filename)
    file_id = str(uuid.uuid4())
    stored_name = f"{file_id}_{name}"

    # tags for S3/Blob metadata
    tags = {
        "OpenWebUI-User-Email": user.email,
        "OpenWebUI-User-Id": user.id,
        "OpenWebUI-User-Name": user.name,
        "OpenWebUI-File-Id": file_id,
    }

    # upload raw bytes
    contents, path = Storage.upload_file(data, stored_name, tags)

    # insert DB record
    file_item = Files.insert_new_file(
        user.id,
        FileForm(
            **{
                "id": file_id,
                "filename": name,
                "path": path,
                "meta": {
                    "name": name,
                    "content_type": content_type,
                    "size": len(contents),
                    "data": metadata,
                },
            }
        ),
    )
    return file_item
