FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
COPY ../../../../domain /domain

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8001
