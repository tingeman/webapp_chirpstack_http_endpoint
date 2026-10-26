# webapp_chirpstack_http_endpoint

Receives ChirpStack HTTP integration events (`POST /event?event=up|join|ack|txack|log|status|location|integration`,
protobuf or JSON), stores each event as a row in the SQLite file `/var/www/app/data/events.sqlite`, inside the
data volume. With `WRITE_JSON_FILES=true` it also writes each event as a JSON file under
`/var/www/app/data/json/` (off by default; no page reads these files).

Pages: `GET /` (index), `GET /last-messages?n=5&event=up`, `GET /health`.
There is no endpoint that deletes data.

## Image

- Base image `python:3.12-slim`, pinned by digest in the `Dockerfile`.
- Python packages are hash-locked: `requirements.in` lists what the app needs, `requirements.txt`
  is generated and installed with `pip install --require-hashes`.
- Runs as user `web` (UID 30000), which owns the files of the data volume. No `sudo` or
  editors in the image.
- `HEALTHCHECK` calls `/health`. gunicorn logs at `info` level to stdout/stderr (`docker logs`).
- `WRITE_JSON_FILES` (default `false`, set in the `Dockerfile`) switches the JSON file copies on. With it
  off, the `json/` directory is never created. Set it with `-e WRITE_JSON_FILES=true`.
- `DB_FILE` and `JSON_OUTPUT_DIR` are set in the `Dockerfile` (and as defaults in `app/config.py`)
  to paths inside the data volume. Environment variables take precedence over `app/.env.production`.

## Build and run

```
docker build -t http_endpoint:local .
docker volume create http_endpoint_data
docker run -d --name http_endpoint -p 8060:8050 -v http_endpoint_data:/var/www/app/data http_endpoint:local
curl http://localhost:8060/health
```

(`docker-compose.yml` does the same, building from source, for local development. The
production host does not build: the image is built with `scripts/build_image.sh` in the
dtu_sus_data02 repository, shipped as a release bundle and loaded by its playbook.)

## Tests

Behaviour tests that run against a built image (docker only, no network, temporary
containers and volume removed afterwards):

```
tests/run.sh http_endpoint:local
```

They check the image contents, health, that a protobuf-encoded uplink is stored in SQLite
inside the data volume (and as a JSON file only with `WRITE_JSON_FILES=true`), that `/clear_messages` is gone, and that data survives a
new container. `scripts/build_image.sh` runs them automatically.

## Changing the Python packages

Edit `requirements.in` and regenerate the lock inside the pinned base image, so that it
matches the image's Python:

```
docker run --rm -v "$PWD":/w -w /w python:3.12-slim@sha256:<digest from Dockerfile> \
  sh -c 'pip install pip-tools && pip-compile --generate-hashes -o requirements.txt requirements.in'
```
