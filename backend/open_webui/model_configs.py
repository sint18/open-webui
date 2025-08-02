
import json
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel

# --------------------
# Shared Enums
# --------------------

AspectRatio = Literal[
    "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "9:21", "2:1", "1:2", "match_input_image"]
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
    reference_images: Optional[List[dict]] = []
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
    image: Optional[dict] = None
    mask: Optional[dict] = None
    style_reference_images: Optional[List[dict]] = []
    seed: Optional[int] = None


class GPTImage1Payload(BaseModel):
    openai_api_key: str
    prompt: str
    quality: Optional[str] = "auto"
    aspect_ratio: Optional[AspectRatio] = "1:1"
    input_images: Optional[List[dict]] = []
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
    megapixels: Optional[str] = "1"


class FluxKontextProPayload(BaseModel):
    prompt: str
    input_image: dict
    aspect_ratio: Optional[AspectRatio] = "match_input_image"
    prompt_upsampling: Optional[bool] = False
    seed: Optional[int] = None
    output_format: Optional[OutputFormat] = "png"
    safety_tolerance: Optional[int] = 2



MODEL_CONFIGS = {
    "runwayml/gen4-image": {
        "schema": RunwayGen4Payload,
        "file_fields": ["reference_images"],
        "single_file_fields": [],
        "price_per_image_usd": 0.05,
    },
    "google/imagen-4": {
        "schema": Imagen4Payload,
        "file_fields": [],
        "single_file_fields": [],
        "price_per_image_usd": 0.05,
    },
    "ideogram-ai/ideogram-v3-turbo": {
        "schema": IdeogramV3TurboPayload,
        "file_fields": ["style_reference_images"],
        "single_file_fields": ["image", "mask"],
        "price_per_image_usd": 0.04,
    },
    "openai/gpt-image-1": {
        "schema": GPTImage1Payload,
        "file_fields": ["input_images"],
        "single_file_fields": [],
        "price_per_image_usd": 0.05,
    },
    "black-forest-labs/flux-schnell": {
        "schema": FluxSchnellPayload,
        "file_fields": [],
        "single_file_fields": [],
        "price_per_image_usd": 0.01,
    },
    "black-forest-labs/flux-kontext-pro": {
        "schema": FluxKontextProPayload,
        "file_fields": [],
        "single_file_fields": ["input_image"],
        "price_per_image_usd": 0.05,
    },
}
