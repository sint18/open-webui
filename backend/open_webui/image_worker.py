import json
import logging
import time
import uuid
import requests
from replicate.client import Client
import io
from pathlib import Path
from open_webui.config import REPLICATE_API_KEY, REPLICATE_API_BASE_URL
from open_webui.models.image_jobs import ImageJobs, JobStatusEnum
from open_webui.models.users import Users
from open_webui.models.billing import CreditTransactions, CreditTransactionForm, UserCredits
from open_webui.model_configs import MODEL_CONFIGS
from open_webui.telegram_bot import send_telegram_message
from open_webui.utils.image_helpers import upload_image, fetch_output_streams
from redis_client import redis_conn
from storage.provider import Storage
from open_webui.utils.images.file_hydrator import hydrate_payload_files

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def get_file_bytesio(filepath: str) -> io.BytesIO:
    """
    Read the file at `filepath` and return its contents as an io.BytesIO stream.

    Args:
        filepath: Path to the file on disk.

    Returns:
        An io.BytesIO instance containing the file’s binary data.

    Raises:
        FileNotFoundError: if the file does not exist.
        IOError: on read errors.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {filepath}")
    data = path.read_bytes()
    return io.BytesIO(data)


def publish_progress(job_id: str, status: str, extra: dict = None):
    msg = {"status": status}
    if extra:
        msg.update(extra)
    redis_conn.publish(f"image_job:{job_id}", json.dumps(msg))


def run_prediction(job_id: str, raw_payload: dict) -> None:
    log.info(f"[Job {job_id}] Starting synchronous Replicate prediction")
    job = ImageJobs.get_image_job_by_job_id(job_id)
    publish_progress(job_id, "started")
    if not job:
        log.error(f"[Job {job_id}] Job record not found in DB")
        return

    model_slug = job.model_name

    try:

        payload = hydrate_payload_files(model_slug, raw_payload)

        publish_progress(job_id, "queued")

        # Initialize Replicate client
        client = Client(api_token=REPLICATE_API_KEY, base_url=REPLICATE_API_BASE_URL)
        model = client.models.get(model_slug)
        if not model:
            raise Exception(f"Model {model_slug} not found")

        # Create prediction synchronously (blocks until done)
        prediction = client.predictions.create(model=model, input=payload)

        publish_progress(job_id, "running", {"generation_id": prediction.id})

        prediction.wait()
        log.info(f"[Job {job_id}] Prediction {prediction.id} completed with status {prediction.status}")

        # Determine status and timing from prediction metadata
        status = prediction.status
        # Duration provided in seconds by Replicate prediction metadata
        duration = prediction.metrics.get("predict_time", 0.0)

        if status == "failed":
            error_msg = getattr(prediction, 'error', 'Unknown error')
            log.error(f"[Job {job_id}] Prediction failed: {error_msg}")
            ImageJobs.update_image_job_by_id(job_id, {
                "status": JobStatusEnum.failed,
                "meta": prediction.__dict__,
                "completed_at": int(time.time()),
            })
            publish_progress(job_id, "failed", {"error": error_msg})

            raise Exception(f"Prediction failed: {error_msg}")

        # Save replicate metadata
        ImageJobs.update_image_job_by_id(job_id, {
            "replicate_id": prediction.id,
            "meta": prediction.__dict__,
        })
        log.info(f"[Job {job_id}] Saved replicate metadata")

        user = Users.get_user_by_id(job.user_id)
        print(prediction.output)
        print(type(prediction.output))
        # Download and upload images from file objects
        output_files = prediction.output
        saved_urls = []
        metadata = payload

        if prediction.output is None:
            log.info(f"[Job {job_id}] No output files found")
            ImageJobs.update_image_job_by_id(job_id, {
                "status": JobStatusEnum.succeeded,
                "completed_at": int(time.time()),
            })
            return

        # Ensure output is iterable
        if not isinstance(output_files, list):
            output_files = [output_files]

        output_files = fetch_output_streams(output_files)

        for file_obj in output_files:
            try:
                log.info(f"[Job {job_id}] Processing {file_obj.name} ({file_obj.content_type})")
                img_data = file_obj.stream.read()
                saved_url = upload_image(img_data, file_obj.content_type, metadata, user)
                saved_urls.append(saved_url)
                log.info(f"[Job {job_id}] Uploaded image to {saved_url}")
            except Exception as fn_e:
                log.error(f"[Job {job_id}] Failed processing file {file_obj.name}: {fn_e}")

        # Billing: use price_per_image_usd from MODEL_CONFIGS
        config = MODEL_CONFIGS[job.model_name]
        price_usd = config["price_per_image_usd"]
        num_outputs = len(output_files or [])
        usd_cost = price_usd * num_outputs
        # convert to credits however you like, e.g. 1 credit = $0.0015
        credits = int(usd_cost / config.get("credit_rate", 0.0015))

        primary_url = saved_urls[0] if saved_urls else None

        publish_progress(job_id, "finished", {"urls": saved_urls})

        # Update job record as succeeded
        ImageJobs.update_image_job_by_id(job_id, {
            "output_url": primary_url,
            "status": JobStatusEnum.succeeded,
            "predict_time": duration,
            "usd_cost": usd_cost,
            "credits_spent": credits,
            "completed_at": int(time.time()),
        })
        log.info(f"[Job {job_id}] Job record updated with output and billing")

        # Record credit transaction and update user credits
        txn = CreditTransactionForm(
            tx_id=str(uuid.uuid4()),
            delta=-credits,
            usd_spend=usd_cost,
            model_name=job.model_name,
            resource_type=f"image:{prediction.model}",
            reference_id=job.id,
            meta=metadata,
        )
        CreditTransactions.insert_transaction(user.id, txn)
        credits_record = UserCredits.update_credits(user.id, -credits)

        # Notify user if credits exhausted
        if credits_record and credits_record.credit_balance <= 0 and user and getattr(user, "telegram_chat_id", None):
            send_telegram_message(user.telegram_chat_id, "⚠️ You've reached your credit limit. Upgrade to keep creating great images!")

        log.info(f"[Job {job_id}] Completed successfully")

    except Exception as e:
        log.error(f"[Job {job_id}] Error during prediction: {e}")
        ImageJobs.update_image_job_by_id(job_id, {
            "status": JobStatusEnum.failed,
            "meta": {"error": str(e)},
            "completed_at": int(time.time()),
        })
        publish_progress(job_id, "failed", {"error": "Something went wrong, please try again later!"})
