# syntax=docker/dockerfile:1.6

# Use python image with uv already installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Copy the latest uv binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set UTF-8 locale to avoid encoding issues (especially with accented characters)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# UV settings
# Enable python bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy the cache instead of linking since it is a mounted image
ENV UV_LINK_MODE=copy

# Install project dependencies using lockfile with layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy application code (separate from dependencies for optimal layer caching)
COPY . /app

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Ensure all binaries in the virtual environment are found by default
ENV PATH="/app/.venv/bin:$PATH"


# Expose port (make it configurable via environment variable)
EXPOSE 8080

# Start the application with configurable port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]