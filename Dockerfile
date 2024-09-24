FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . .

RUN mkdir -p logs

ENV PYTHONPATH=/app

CMD ["poetry", "run", "python", "src/main.py"]
