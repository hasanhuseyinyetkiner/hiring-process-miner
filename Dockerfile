FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
WORKDIR /srv/app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
# Hatchling reads project.readme during editable install; must exist before this sync.
COPY README.md ./
RUN uv sync --frozen --no-dev

ENV PATH="/srv/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_ENV=demo \
    HOST=0.0.0.0 \
    PORT=8102 \
    ALLOW_NETWORK_BIND=true \
    DATABASE_URL=postgresql+psycopg://hpm:hpm@db:5432/hpm \
    SEED_ON_STARTUP=true \
    CORS_ORIGINS=http://127.0.0.1:5102,http://localhost:5102

EXPOSE 8102
CMD ["hpm"]
