FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/worker/pyproject.toml .
RUN pip install --no-cache-dir .

COPY packages/ /packages
RUN pip install --no-cache-dir /packages/*/

COPY apps/worker/src/ ./src/

CMD ["python", "-m", "src.main"]
