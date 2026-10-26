FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
COPY pyproject.toml poetry.lock ./

FROM base AS dev
RUN poetry install --with dev --no-root
COPY app ./app
COPY maos_examples ./maos_examples
COPY alembic.ini ./
COPY alembic ./alembic
CMD ["pytest"]

FROM base AS requirements
RUN poetry export --only main --format requirements.txt --output /requirements.txt

FROM python:3.12-slim AS runtime-dependencies
COPY --from=requirements /requirements.txt /requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /requirements.txt

FROM base AS release-source
COPY app ./app
RUN rm -rf app/tests

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=runtime-dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=runtime-dependencies /usr/local/bin /usr/local/bin
RUN groupadd --system app && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app
COPY --from=release-source --chown=app:app /app/app ./app
COPY --chown=app:app maos_examples ./maos_examples
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
