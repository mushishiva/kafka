FROM python:3.13-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ADD . /app
WORKDIR /app
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
