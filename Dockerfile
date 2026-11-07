# E4A 1.0 reference service.
# NOTE: this image runs the service from the repository layout. The
# installable Python package is finalized in the packaging phase; the
# container is the supported local deployment until then.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app:/app/sdk/python \
    E4A_DB_PATH=/data/e4a-v1.db \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "api.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
