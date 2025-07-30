import os

MODEL_CONFIGS = {
    "ideogram-ai/ideogram-v3-turbo": os.getenv("IDEOGRAM_V3_TURBO_VERSION", ""),
    "runwayml/gen4-image": os.getenv("RUNWAYML_GEN4_IMAGE_VERSION", ""),
    "openai/gpt-image-1": os.getenv("GPT_IMAGE_1_VERSION", ""),
}
