import io
from pathlib import Path
from open_webui.model_configs import MODEL_CONFIGS
from open_webui.models.files import Files
from storage.provider import Storage

def hydrate_payload_files(model_slug: str, payload: dict) -> dict:
    """
    Replace each MODEL_CONFIGS[model_slug]['file_fields'] entry
    from a dict or list of dicts → BytesIO file‐objects.
    """
    cfg = MODEL_CONFIGS.get(model_slug, {})

    def load_one(file_model: dict):
        file_id = file_model.get("id")
        if not file_id:
            raise ValueError(f"Missing file id for '{field}'")
        rec = Files.get_file_by_id(file_id)
        if not rec:
            raise RuntimeError(f"File {file_id} not found")
        disk_path = Storage.get_file(rec.path)
        bio = io.BytesIO(Path(disk_path).read_bytes())
        bio.name = Path(rec.filename).name
        return bio

    for field in cfg.get("file_fields", []):
        raw = payload.get(field)
        if not raw:
            continue

        if isinstance(raw, list):
            payload[field] = [ load_one(m) for m in raw ]
        else:
            payload[field] = load_one(raw)

    for field in cfg.get("single_file_fields", []):
        raw = payload.get(field)
        if not raw:
            continue

        if isinstance(raw, list):
            payload[field] = load_one(raw[0])
        else:
            payload[field] = load_one(raw)

    return payload
