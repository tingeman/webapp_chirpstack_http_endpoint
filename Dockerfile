# Base image: python:3.12-slim, pinned by digest (index digest, multi-arch).
# To update: docker buildx imagetools inspect python:3.12-slim, then regenerate the
# lock file inside the same base image (see README).
FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

ENV DASH_DEBUG_MODE=False \
    APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    DB_FILE=/var/www/app/data/events.sqlite \
    JSON_OUTPUT_DIR=/var/www/app/data/json/

# The web user keeps UID 30000, which owns the files in the existing data volume.
RUN adduser --disabled-password --no-create-home --uid 30000 web

# Data directory = mount point of the data volume (SQLite file and JSON files live here).
RUN mkdir -p /var/www/app/data \
    && chown -R web:web /var/www/app \
    && chmod -R 755 /var/www/app

WORKDIR /var/www/app

COPY ./requirements.txt ./requirements.txt
RUN set -ex && \
    python -m pip install --no-cache-dir --require-hashes -r ./requirements.txt

USER web
COPY --chown=web:web ./app /var/www/app/

EXPOSE 8050

# Healthy = the app answers /health (no curl in the image). start-interval (Docker Engine
# 25+) checks every 2 s during the start period, so `docker compose up --wait` does not
# wait a full interval.
HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --start-interval=2s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8050/health', timeout=5).status == 200 else 1)"]

# Logs go to stdout/stderr (the container log). No control socket: the web user has no home
# directory to put it in.
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--worker-class", "gevent", "--workers", "3", "--log-level", "info", "--no-control-socket", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
