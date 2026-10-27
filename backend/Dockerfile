FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
COPY backend/pyproject.toml backend/poetry.lock ./

FROM base AS dev
RUN poetry install --with dev --no-root
COPY backend/app ./app
COPY backend/maos_examples ./maos_examples
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
CMD ["pytest"]

FROM base AS requirements
RUN poetry export --only main --format requirements.txt --output /requirements.txt

# Same supported, digest-pinned Debian/Python base. No mutable apt upgrade.
FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f AS runtime-os
# The application never mounts filesystems. Purge just this non-essential tool;
# preserve Essential packages, OS package metadata and dependency libraries.
RUN apt-get purge --yes mount

FROM runtime-os AS runtime-dependencies
COPY --from=requirements /requirements.txt /requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /requirements.txt \
    && python -m pip uninstall --yes pip

COPY scripts/ops/license_inventory.py /tmp/license_inventory.py
COPY release/third-party /tmp/third-party
RUN python /tmp/license_inventory.py --output /licenses --supplements /tmp/third-party

FROM base AS release-source
COPY backend/app ./app
RUN rm -rf app/tests

FROM runtime-os AS runtime
# Installers belong to build stages. Preserve Python and all locked app packages.
RUN python -m pip uninstall --yes pip \
    && python -c "import pathlib, shutil, sysconfig; shutil.rmtree(pathlib.Path(sysconfig.get_path('stdlib')) / 'ensurepip')"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=runtime-dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=runtime-dependencies /usr/local/bin /usr/local/bin
RUN groupadd --system app && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app
COPY --from=release-source --chown=app:app /app/app ./app
COPY --chown=app:app backend/maos_examples ./maos_examples
COPY --chown=app:app backend/alembic.ini ./
COPY --chown=app:app backend/alembic ./alembic
COPY --from=runtime-dependencies --chown=app:app /licenses ./licenses
COPY --chown=app:app LICENSE NOTICE ./licenses/project/
ARG VCS_REF
LABEL org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source="https://github.com/hzjanuary/multi-agent-system"
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
