# syntax=docker/dockerfile:1.6

# Use of python image with uv already installed.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

#Copy the latest uv binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# UV settings
# Enable python bytecode compilation for faster build up
ENV UV_COMPILE_BYTECODE=1
#  Copy the cache instead of linking since it is a mounted image.
ENV UV_LINK_MODE=copy

#Installation of the project dependencies using lockfile. It uses layer caching for faster rebuilds and changes in the code
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
# Installation of the rest of the code. We separate this from its dependecies for optimal layer catching in case of CD/CI
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Ensuring all binaries present in the virtual enviroment are found by default.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

ENTRYPOINT []

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
