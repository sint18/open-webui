import enum
import time
import logging
from typing import Optional, Literal
import uuid

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column,
    String,
    Text,
    BigInteger,
    Integer,
    Float,
    Enum as SAEnum,
    ForeignKey,
    JSON,
)

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

# Status enum for ImageJob
class JobStatusEnum(enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class ImageJob(Base):
    __tablename__ = "image_job"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    model_name = Column(String)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text)
    status = Column(SAEnum(JobStatusEnum, name="image_job_status_enum"), default=JobStatusEnum.queued, nullable=False)
    replicate_id = Column(String, unique=True)
    # TODO: Change to 'output_urls' and make it a list
    output_url = Column(Text)
    predict_time = Column(Float)
    usd_cost = Column(Float)
    credits_spent = Column(Integer)
    meta = Column(JSON)
    attempts = Column(Integer, default=0)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    completed_at = Column(BigInteger)


class ImageJobModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    model_name: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    status: JobStatusEnum
    replicate_id: Optional[str] = None
    output_url: Optional[str] = None
    predict_time: Optional[float] = None
    usd_cost: Optional[float] = None
    credits_spent: Optional[int] = None
    meta: Optional[dict] = None
    attempts: int
    created_at: int
    completed_at: Optional[int] = None


class ImageJobsTable:
    def __init__(self):
        pass

    def insert_new_job(
        self,
        user_id: str,
        prompt: str,
        model_name: str,
        negative_prompt: Optional[str] = None,
    ) -> ImageJobModel:
        log.info(f"Inserting new image job for user {user_id}")
        with get_db() as db:
            job = ImageJob(
                user_id=user_id,
                prompt=prompt,
                model_name=model_name,
                negative_prompt=negative_prompt,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            log.debug(f"Inserted job {job.id}")
            return ImageJobModel.model_validate(job)

    def get_image_job_by_job_id(self, job_id: str) -> Optional[ImageJobModel]:
        try:
            with get_db() as db:
                job = db.query(ImageJob).filter_by(id=job_id).first()
                if job:
                    log.debug(f"Fetched job {job_id}")
                    return ImageJobModel.model_validate(job)
                log.debug(f"Job {job_id} not found")
                return None
        except Exception as e:
            log.error(f"Error fetching job {job_id}: {e}")
            return None

    def update_image_job_by_id(self, job_id: str, updates: dict) -> Optional[ImageJobModel]:
        """Update an ImageJob and return the updated model."""
        try:
            with get_db() as db:
                job = db.query(ImageJob).filter_by(id=job_id).first()
                if not job:
                    log.warning(f"Attempted to update missing job {job_id}")
                    return None

                for key, value in updates.items():
                    setattr(job, key, value)

                db.commit()
                db.refresh(job)
                log.debug(f"Updated job {job_id} with {updates}")
                return ImageJobModel.model_validate(job)
        except Exception as e:
            log.error(f"Error updating job {job_id}: {e}")
            return None


ImageJobs = ImageJobsTable()
