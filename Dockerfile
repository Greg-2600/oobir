FROM python:3.15-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Create app user
RUN useradd --uid 10001 --create-home --shell /bin/bash app
WORKDIR /home/app/oobir

# Install system dependencies needed for some Python wheels
# Note: cp trick works around BuildKit read-only /etc/resolv.conf
# hadolint ignore=DL3008  # Base image package versions are intentionally unpinned.
RUN cp /etc/resolv.conf /tmp/resolv.conf.bak || true \
  && (echo "nameserver 8.8.8.8" | tee /etc/resolv.conf 2>/dev/null || true) \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /home/app/oobir/requirements.txt
# hadolint ignore=DL3013  # Tooling bootstrap intentionally tracks latest.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r /home/app/oobir/requirements.txt

# Copy project files
COPY . /home/app/oobir
RUN chown -R app:app /home/app/oobir

USER 10001
ENV PATH="/home/app/.local/bin:${PATH}"
ENV OLLAMA_HOST=http://oobir_ollama:11434

# Helper script location
ENV APP_RUNNER=/home/app/oobir/run-tests.sh

EXPOSE 2009

# Default to running the FastAPI server
# Can be overridden to run CLI or tests
CMD ["python", "-m", "uvicorn", "flow_api:app", "--host", "0.0.0.0", "--port", "2009"]


