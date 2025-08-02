# open_webui/utils/input_builders.py

import io
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError

from open_webui.model_configs import MODEL_CONFIGS
from open_webui.models.files import Files, FileModel
from storage.provider import Storage

def build_model_input(
    model_slug: str,
    raw_payload: Dict[str, Any],
    file_urls: Dict[str, List[FileModel]],
) -> Dict[str, Any]:
    """
    1) Validate & canonicalize scalars via the Pydantic schema.
    2) Hydrate any file-fields (both list and single) into the final payload.
    """
    cfg = MODEL_CONFIGS.get(model_slug)
    if not cfg:
        raise ValueError(f"Unsupported model_slug: {model_slug}")

    schema = cfg["schema"]
    try:
        parsed: BaseModel = schema(**raw_payload)
    except ValidationError as ve:
        # bubble up to your router so it returns a 422
        raise

    output: Dict[str, Any] = parsed.model_dump()

    # 1) List‐of‐files fields
    for field in cfg.get("file_fields", []):
        files = file_urls.get(field, [])
        # turn [FileModel,...] into [dict,...]
        output[field] = [f.model_dump() for f in files]

    # 2) Single‐file fields
    for field in cfg.get("single_file_fields", []):
        files = file_urls.get(field, [])
        if files:
            output[field] = files[0].model_dump()
        else:
            output.pop(field, None)

    return output
