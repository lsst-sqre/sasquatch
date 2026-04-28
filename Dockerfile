# This Dockerfile builds the main Sasquatch application image.
#
# The backup and restore utility image is intentionally separate and lives at
# backup/Dockerfile because it needs InfluxDB-specific operational tooling that
# does not belong in the web application's runtime image.
#
# This Dockerfile has three stages:
#
# base-image
#   Updates the base Python image with security patches and common system
#   packages. This image becomes the base of all other images.
# install-image
#   Installs dependencies and the application into a virtual environment.
#   This virtual environment is ideal for copying across build stages.
# runtime-image
#   - Copies the virtual environment into place.
#   - Runs a non-root user.
#   - Sets up the entrypoint and port.

FROM python:3.14.2-slim-trixie AS base-image

# Update system packages.
COPY scripts/install-base-packages.sh .
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    ./install-base-packages.sh && rm ./install-base-packages.sh

FROM base-image AS install-image

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv

# Install system packages only needed for building dependencies.
COPY scripts/install-dependency-packages.sh .
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    ./install-dependency-packages.sh

# Disable hard links during uv package installation since we're using a
# cache on a separate file system.
ENV UV_LINK_MODE=copy

# Force use of system Python so that the Python version is controlled by
# the Docker base image version, not by whatever uv decides to install.
ENV UV_PYTHON_PREFERENCE=only-system

# Install the dependencies.
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-default-groups --compile-bytecode --no-install-project

# Install the application itself.
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --compile-bytecode --no-editable

FROM base-image AS influx-tools-image

# Download the InfluxDB OSS tooling needed by migration commands.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get -y install --no-install-recommends curl ca-certificates && \
    mkdir influxdb-1.12.3 && \
    curl -LO "https://dl.influxdata.com/influxdb/releases/v1.12.3/influxdb-1.12.3_linux_amd64.tar.gz" && \
    tar xf influxdb-1.12.3_linux_amd64.tar.gz -C influxdb-1.12.3 && \
    mv "$(find influxdb-1.12.3 -type f -name influx_inspect | head -n 1)" /usr/local/bin/ && \
    rm -rf influxdb-1.12.3 influxdb-1.12.3_linux_amd64.tar.gz /var/lib/apt/lists/*

FROM base-image AS runtime-image

# Create a non-root user.
RUN useradd --create-home appuser

# Copy the virtualenv.
COPY --from=install-image /app/.venv /app/.venv

# Copy the InfluxDB inspection tool used by migration commands.
COPY --from=influx-tools-image /usr/local/bin/influx_inspect /usr/local/bin/influx_inspect

# Switch to the non-root user.
USER appuser

# Expose the port.
EXPOSE 8080

# Make sure we use the virtualenv.
ENV PATH="/app/.venv/bin:$PATH"

# Run the application.
CMD ["uvicorn", "sasquatch.main:app", "--host", "0.0.0.0", "--port", "8080"]
