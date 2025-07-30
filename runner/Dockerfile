FROM python:3.11-slim

# Create non-root user
RUN adduser --disabled-password --gecos '' app
USER app
WORKDIR /app

# Helpful env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_CACHE_DIR=/wheels-cache \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

# Use POSIX shell; no need for bash
SHELL ["/bin/sh", "-lc"]

CMD 'python -m venv /session/.venv && \
     . /session/.venv/bin/activate && \
     python -m pip install --upgrade pip && \
     pip install --no-input --cache-dir "$PIP_CACHE_DIR" -r /session/requirements.txt && \
     streamlit run /session/app.py \
       --server.port 8501 \
       --server.headless true \
       --server.baseUrlPath "${BASE_PATH:-/}"'
