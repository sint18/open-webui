import json
import logging

from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["IMAGES"])


def build_model_input(model_slug: str, payload_json: str, file_urls: dict) -> dict:
    log.debug(f"Building model input for {model_slug}")
    payload = json.loads(payload_json) if payload_json else {}
    if model_slug == "ideogram-ai/ideogram-v3-turbo":
        if "style_reference_images" in file_urls:
            log.debug("Adding style_reference_images to payload")
            payload["style_reference_images"] = file_urls["style_reference_images"]
    elif model_slug == "runwayml/gen4-image":
        if "reference_images" in file_urls:
            log.debug("Adding reference_images to payload")
            payload["reference_images"] = file_urls["reference_images"]
    elif model_slug == "openai/gpt-image-1":
        if "image" in file_urls:
            log.debug("Adding image to payload")
            payload["image"] = file_urls["image"]
    else:
        payload.update(file_urls)
        if file_urls:
            log.debug("Added generic file URLs to payload")
    log.debug(f"Final built input: {payload}")
    return payload
