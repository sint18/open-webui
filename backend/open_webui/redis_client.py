
import os
from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_conn = Redis.from_url(REDIS_URL)
standard_queue = Queue("image_standard", connection=redis_conn)
hires_queue = Queue("image_hires", connection=redis_conn)