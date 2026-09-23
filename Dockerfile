FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render (and similar platforms) inject the listen port as $PORT. Default
# keeps plain `docker build`/`docker run` behavior identical to before.
# Local compose overrides this command with --reload on :8000 (see
# docker-compose.yml), so the dev workflow is unaffected.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
