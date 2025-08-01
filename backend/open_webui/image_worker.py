import os
import logging

from replicate.client import Client

from open_webui.config import WEBUI_URL, REPLICATE_API_KEY, REPLICATE_API_BASE_URL
from open_webui.internal.db import get_db
from open_webui.models.image_jobs import ImageJobs, JobStatusEnum

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def run_prediction(job_id: str, payload: dict) -> None:
    log.info(f"Starting Replicate prediction for job {job_id}")
    job = ImageJobs.get_image_job_by_job_id(job_id)
    if not job:
        log.error(f"Job record {job_id} not found in DB")
        return

    # Look up the exact version string from your config
    model_slug = job.model_name

    # webhook_url = f"{WEBUI_URL}/api/v1/images/webhook/{job_id}"
    webhook_url = f"https://c581a16c87c4.ngrok-free.app/api/v1/images/webhook/{job_id}"
    try:
        client = Client(api_token=REPLICATE_API_KEY,
                        base_url=REPLICATE_API_BASE_URL)
        model = client.models.get(model_slug)
        if not model:
            log.error(f"Model {model_slug} not found")
            raise Exception(f"Model {model_slug} not found")


        prediction = client.predictions.create(
            model=model,
            input=payload,
            webhook=webhook_url,
            webhook_events_filter=["completed"],
        )  # async, with webhook :contentReference[oaicite:9]{index=9}

        # Persist Replicate’s ID and metadata
        ImageJobs.update_image_job_by_id(job_id, {
                "replicate_id": prediction.id,
                "meta": prediction.__dict__,
            })

        log.info(f"Replicate prediction enqueued: {prediction.id}")

    except Exception as e:
        log.error(f"Failed to start prediction for {job_id}: {e}")
        ImageJobs.update_image_job_by_id(job_id, {
            "status": JobStatusEnum.failed,
            "meta": {"error": str(e)},
        })