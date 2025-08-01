FROM python:3.11-slim

# Create non-root user
RUN adduser --disabled-password --gecos '' app
USER app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_CACHE_DIR=/wheels-cache \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    ENTRYPOINT=/session/app.py

EXPOSE 8501


# ─── run the preview ──────────────────────────────────────────────
# keep everything you already had, but drive Streamlit with $ENTRYPOINT
CMD ["/bin/sh","-lc", "\
  python3 -m venv /session/.venv && \
  . /session/.venv/bin/activate && \
  pip install --upgrade pip && \
  pip install --no-input --cache-dir \"$PIP_CACHE_DIR\" -r /session/requirements.txt && \
  streamlit run \"$ENTRYPOINT\" \
      --server.port 8501 \
      --server.headless true \
      --server.baseUrlPath \"${BASE_PATH:-/}\" \
"]
