FROM python:3.12-slim

WORKDIR /app

# Poetry
RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
COPY . .
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Tests
RUN poetry run pytest tests/

CMD ["python", "main.py"]