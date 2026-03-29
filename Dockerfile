FROM python:3.11-slim

# Create app user
RUN useradd --create-home --shell /bin/bash app || true
WORKDIR /home/app/oobir

# Install system dependencies needed for some Python wheels
# Note: cp trick works around BuildKit read-only /etc/resolv.conf
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
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /home/app/oobir/requirements.txt

# Copy project files
COPY . /home/app/oobir
RUN chown -R app:app /home/app/oobir

USER app
ENV PATH="/home/app/.local/bin:${PATH}"
ENV OLLAMA_HOST=http://ollama:11434

# Helper script location
ENV APP_RUNNER=/home/app/oobir/run-tests.sh

EXPOSE 8000

# Default to running the FastAPI server
# Can be overridden to run CLI or tests
CMD ["python", "-m", "uvicorn", "flow_api:app", "--host", "0.0.0.0", "--port", "8000"]


