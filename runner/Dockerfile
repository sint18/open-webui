FROM python:3.11-slim

RUN adduser --disabled-password --gecos '' app
USER app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

EXPOSE 8501
CMD bash -lc '\
  python -m venv /session/.venv && \
  . /session/.venv/bin/activate && \
  pip install --no-cache-dir -r /session/requirements.txt && \
  streamlit run /session/app.py --server.port 8501 --server.headless=true'
