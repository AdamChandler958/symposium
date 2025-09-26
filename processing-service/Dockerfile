FROM python:3.13-slim AS builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN uv venv
RUN uv sync 


FROM python:3.13-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:$PYTHONPATH"

EXPOSE 3020

CMD ["python", "main.py"]