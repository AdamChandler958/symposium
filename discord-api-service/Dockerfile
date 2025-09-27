FROM python:3.13-slim AS builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN uv venv
RUN uv sync 


FROM python:3.13-slim
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:$PYTHONPATH"


CMD ["python", "main.py"]