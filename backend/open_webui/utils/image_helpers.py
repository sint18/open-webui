import asyncio
import mimetypes
from fastapi import UploadFile
from open_webui.routers.files import router as files_router
from utils.file_helpers import save_bytes_as_file
import io
import logging
from typing import List, Union
import requests
from dataclasses import dataclass

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def upload_image(image_data: bytes, content_type, metadata, user):
    image_format = mimetypes.guess_extension(content_type)
    file = UploadFile(
        file=io.BytesIO(image_data),
        filename=f"LabyAI-Lucid-generated-image{image_format}",  # will be converted to a unique ID on upload_file
        headers={
            "content-type": content_type,
        },
    )
    # Handle both sync and async upload_file functions
    # result = upload_file(request, file, metadata=metadata, internal=True, user=user)
    result = save_bytes_as_file(file.file, metadata=metadata, user=user, content_type=file.content_type, original_filename=file.filename)
    if asyncio.iscoroutine(result):
        # It's a coroutine, we need to run it
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            file_item = asyncio.run_coroutine_threadsafe(result, loop).result()
        except RuntimeError:
            # No event loop running, use asyncio.run
            file_item = asyncio.run(result)
    else:
        file_item = result

    url = files_router.url_path_for("get_file_content_by_id", id=file_item.id)
    return url


@dataclass
class OutputFile:
    stream: io.BytesIO
    content_type: str
    name: str

def fetch_output_streams(
    outputs: Union[List, object],
    api_token: str = None
) -> List[OutputFile]:
    """
     Normalize Replicate prediction output into a list of BytesIO streams.

    - If `outputs` is a single file‐like (has .read()), wraps its bytes.
    - If it's a list of file‐likes, does the same for each.
    - If it's a string URL (or list of URLs), does an HTTP GET (with optional Bearer).
    - Logs successes and failures per item.

    Returns:
        List[OutputFile] where each .name is set to the original filename or URL basename.
    """
    items = outputs if isinstance(outputs, (list, tuple)) else [outputs]
    result: List[OutputFile] = []

    for idx, item in enumerate(items):
        try:
            # file‐like object from Replicate
            if hasattr(item, "read"):
                log.info(f"[fetch] file‐like at index {idx}")
                data = item.read()
                # replicate.File objects often have `.name` and `.headers`
                ctype = getattr(item, "headers", {}).get("content-type", None)
                name  = getattr(item, "name", None)

            # URL string
            elif isinstance(item, str):
                log.info(f"[fetch] downloading URL at index {idx}: {item}")
                headers = {}
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                resp = requests.get(item, headers=headers)
                resp.raise_for_status()
                data  = resp.content
                ctype = resp.headers.get("content-type")
                name  = item.rsplit("/", 1)[-1]

            else:
                raise TypeError(f"Unsupported type: {type(item)}")

            # fallback ctype from filename if still unknown
            if not ctype:
                ctype = mimetypes.guess_type(name or "")[0] or "application/octet-stream"

            # wrap bytes
            bio = io.BytesIO(data)
            bio.name = name or f"output_{idx}"
            result.append(OutputFile(stream=bio, content_type=ctype, name=bio.name))

        except Exception as e:
            log.error(f"[fetch] failed index {idx}: {e}")

    return result

