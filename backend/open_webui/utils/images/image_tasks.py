import json
import logging
from open_webui.env import SRC_LOG_LEVELS
from open_webui.image_worker import run_prediction
from redis_client import hires_queue, standard_queue, redis_conn

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["IMAGES"])


HIRES_MODELS = {"runwayml/gen4-image", "openai/gpt-image-1"}


def route_image_job(user, input: dict) -> str:
    """Return the queue name for the given job input."""
    if input.get("resolution") in ["4K", "2048x2048"]:
        log.debug("Routing to hires queue due to resolution")
        return "hires"
    if input.get("model") in HIRES_MODELS:
        log.debug("Routing to hires queue due to model")
        return "hires"
    log.debug("Routing to standard queue")
    return "standard"

def enqueue_prediction_job(job_id: str, payload: dict, user=None) -> str:
    """Enqueue a prediction job and return the RQ job id."""
    try:
        queue_name = route_image_job(user, payload)
        log.info(f"Enqueuing job {job_id} on {queue_name} queue")
        q = hires_queue if queue_name == "hires" else standard_queue
        rq_job = q.enqueue(run_prediction, job_id, payload)
        log.debug(f"RQ job {rq_job.id} created for {job_id}")
        return rq_job.id
    except Exception as e:
        log.error(f"Failed to enqueue job {job_id}: {e}")
        raise
