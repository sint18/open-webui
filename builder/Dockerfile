############################
# builder/Dockerfile
############################
FROM python:3.11-slim

#—Basic runtime hygiene———————————————————————————————
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# gcc is needed occasionally for wheels with native code; skip it if you know you won't need it.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

#—Dependencies———————————————————————————————————————
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#—Application code———————————————————————————————————
COPY main.py .

#—Entrypoint———————————————————————————————————————
#  • Uvicorn serves the FastAPI ‘/launch’ endpoint on port 8000
#  • The builder talks to the Docker daemon inside the same host/container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
