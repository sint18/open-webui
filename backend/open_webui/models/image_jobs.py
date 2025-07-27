import enum
import time
from typing import Optional, Literal
import uuid

from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column,
    String,
    Text,
    BigInteger,
    Integer,
    Float,
    Enum as SAEnum, ForeignKey
)

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
    output_url = Column(Text)
    predict_time = Column(Float)
    usd_cost = Column(Float)
    credits_spent = Column(Integer)
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
            return ImageJobModel.model_validate(job)


ImageJobs = ImageJobsTable()
