import logging
import time
import requests
import replicate

from open_webui.internal.db import get_db
from open_webui.models.image_jobs import ImageJob, JobStatusEnum
from open_webui.models.billing import CreditTransactions, CreditTransactionForm, UserCredits
from open_webui.models.users import Users
from open_webui.config import WEBUI_URL, REPLICATE_API_BASE_URL, REPLICATE_API_KEY
from open_webui.model_configs import MODEL_CONFIGS
from open_webui.env import SRC_LOG_LEVELS

from sqlalchemy.orm import Session

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["IMAGES"])


def run_prediction(job_id: str, payload: dict) -> None:
    log.info(f"Running prediction for job {job_id}")
    with get_db() as db:
        job: ImageJob | None = db.query(ImageJob).filter(ImageJob.id == job_id).first()
        if not job:
            log.error(f"Job {job_id} not found")
            return
        job.status = JobStatusEnum.running
        db.commit()
        db.refresh(job)
        log.debug(f"Job {job_id} marked as running")

    model_slug = job.model_name
    version = MODEL_CONFIGS.get(model_slug)
    if not version:
        log.error(f"No version configured for {model_slug}")
        with get_db() as db:
            db.query(ImageJob).filter_by(id=job_id).update({"status": JobStatusEnum.failed})
            db.commit()
        return

    webhook_url = f"{WEBUI_URL}/api/v1/images/webhook/{job_id}"
    try:
        client = replicate.Client(api_token=REPLICATE_API_KEY, base_url=REPLICATE_API_BASE_URL)
        prediction = client.predictions.create(
            version=version,
            input=payload,
            webhook=webhook_url,
            webhook_events_filter=["completed"],
        )
        with get_db() as db:
            db.query(ImageJob).filter_by(id=job_id).update({
                "replicate_id": prediction.id,
                "meta": prediction.__dict__,
            })
            db.commit()
        log.info(f"Prediction started for job {job_id}: {prediction.id}")
    except Exception as e:
        log.error(f"Prediction failed to start for job {job_id}: {e}")
        with get_db() as db:
            db.query(ImageJob).filter_by(id=job_id).update({
                "status": JobStatusEnum.failed,
                "meta": {"error": str(e)},
            })
            db.commit()
        return

