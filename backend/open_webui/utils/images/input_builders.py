# import json
# import logging
#
# from open_webui.env import SRC_LOG_LEVELS
#
# log = logging.getLogger(__name__)
# log.setLevel(SRC_LOG_LEVELS["IMAGES"])
#
#
# def build_model_input(model_slug: str, payload_json: str, file_urls: dict) -> dict:
#     log.debug(f"Building model input for {model_slug}")
#     payload = json.loads(payload_json) if payload_json else {}
#     if model_slug == "ideogram-ai/ideogram-v3-turbo":
#         if "style_reference_images" in file_urls:
#             log.debug("Adding style_reference_images to payload")
#             payload["style_reference_images"] = file_urls["style_reference_images"]
#     elif model_slug == "runwayml/gen4-image":
#         if "reference_images" in file_urls:
#             log.debug("Adding reference_images to payload")
#             payload["reference_images"] = file_urls["reference_images"]
#     elif model_slug == "openai/gpt-image-1":
#         if "image" in file_urls:
#             log.debug("Adding image to payload")
#             payload["image"] = file_urls["image"]
#     else:
#         payload.update(file_urls)
#         if file_urls:
#             log.debug("Added generic file URLs to payload")
#     log.debug(f"Final built input: {payload}")
#     return payload
# ---- input_builders.py ----

import json
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel

# --------------------
# Shared Enums
# --------------------

AspectRatio = Literal["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "9:21", "2:1", "1:2", "match_input_image"]
Resolution = Literal["720p", "1080p", "None", "512x1536", "1536x640"]
StyleType = Literal["None", "Auto", "General", "Realistic", "Design"]
Background = Literal["auto", "transparent", "opaque"]
OutputFormat = Literal["webp", "jpg", "png", "jpeg"]
ContentModeration = Literal["auto", "low"]

# --------------------
# Pydantic Payload Schemas
# --------------------

class RunwayGen4Payload(BaseModel):
    prompt: str
    seed: Optional[int] = None
    aspect_ratio: Optional[AspectRatio] = "16:9"
    resolution: Optional[Resolution] = "1080p"
    reference_images: Optional[List[str]] = []
    reference_tags: Optional[List[str]] = []

class Imagen4Payload(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[AspectRatio] = "1:1"
    safety_filter_level: Optional[str] = "block_only_high"

class IdeogramV3TurboPayload(BaseModel):
    prompt: str
    aspect_ratio: Optional[AspectRatio] = "1:1"
    resolution: Optional[Resolution] = "None"
    magic_prompt_option: Optional[str] = "Auto"
    style_type: Optional[StyleType] = "None"
    image: Optional[str] = None
    mask: Optional[str] = None
    style_reference_images: Optional[List[str]] = []
    seed: Optional[int] = None

class GPTImage1Payload(BaseModel):
    openai_api_key: str
    prompt: str
    quality: Optional[str] = "auto"
    aspect_ratio: Optional[AspectRatio] = "1:1"
    input_images: Optional[List[str]] = []
    number_of_images: Optional[int] = 1
    background: Optional[Background] = "auto"
    output_compression: Optional[int] = 90
    output_format: Optional[OutputFormat] = "webp"
    moderation: Optional[ContentModeration] = "auto"
    user_id: Optional[str] = None

class FluxSchnellPayload(BaseModel):
    prompt: str
    aspect_ratio: Optional[AspectRatio] = "1:1"
    num_outputs: Optional[int] = 1
    num_inference_steps: Optional[int] = 4
    seed: Optional[int] = None
    output_format: Optional[OutputFormat] = "webp"
    output_quality: Optional[int] = 80
    disable_safety_checker: Optional[bool] = False
    go_fast: Optional[bool] = True
    lora_weights: Optional[str] = None
    lora_scale: Optional[float] = None
    megapixels: Optional[str] = "1"

class FluxKontextProPayload(BaseModel):
    prompt: str
    input_image: str
    aspect_ratio: Optional[AspectRatio] = "match_input_image"
    prompt_upsampling: Optional[bool] = False
    seed: Optional[int] = None
    output_format: Optional[OutputFormat] = "png"
    safety_tolerance: Optional[int] = 2

# --------------------
# Input Builder
# --------------------

def build_model_input(model_slug: str, payload_json: str, file_urls: Dict[str, Any]) -> Dict:
    payload = json.loads(payload_json)

    if model_slug == "runwayml/gen4-image":
        parsed = RunwayGen4Payload(**payload)
        return {
            **parsed.model_dump(),
            "reference_images": file_urls.get("reference_images", [])
        }

    elif model_slug == "google/imagen-4":
        parsed = Imagen4Payload(**payload)
        return parsed.model_dump()

    elif model_slug == "ideogram-ai/ideogram-v3-turbo":
        parsed = IdeogramV3TurboPayload(**payload)
        return {
            **parsed.model_dump(),
            "style_reference_images": file_urls.get("style_reference_images", []),
            "image": file_urls.get("image"),
            "mask": file_urls.get("mask"),
        }

    elif model_slug == "openai/gpt-image-1":
        parsed = GPTImage1Payload(**payload)
        return parsed.model_dump()

    elif model_slug == "black-forest-labs/flux-schnell":
        parsed = FluxSchnellPayload(**payload)
        return parsed.model_dump()

    elif model_slug == "black-forest-labs/flux-kontext-pro":
        parsed = FluxKontextProPayload(**payload)
        return parsed.model_dump()

    raise ValueError(f"Unsupported model_slug: {model_slug}")

