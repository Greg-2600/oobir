#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy_remote.sh [user@host] [remote_path]
# Default: greg@192.168.1.248 ~/oobir

REMOTE=${1:-greg@192.168.1.248}
REMOTE_PATH=${2:-'~/oobir'}

echo "Deploying workspace to ${REMOTE}:${REMOTE_PATH}"
echo "=================================================="

# Prepare remote path. If the user provided a path starting with '~', use $HOME on the remote host
if [[ "${REMOTE_PATH}" == ~* ]]; then
  # keep a literal $HOME so it expands on the remote side
  # Remove the ~ and append to $HOME
  tail="${REMOTE_PATH#\~}"
  if [ -z "$tail" ]; then
    REMOTE_PATH_REMOTE="\$HOME"
  else
    REMOTE_PATH_REMOTE="\$HOME${tail}"
  fi
elif [[ "${REMOTE_PATH}" == /* ]]; then
  # User passed an absolute path (likely expanded locally). Map common local home paths
  # like /Users/<user>/... to remote $HOME/...
  if [[ "${REMOTE_PATH}" =~ ^/Users/[^/]+(/.*)?$ ]]; then
    tail="${BASH_REMATCH[1]:-}"
    REMOTE_PATH_REMOTE="\$HOME${tail}"
  else
    # fallback: place basename under remote $HOME
    base=$(basename "${REMOTE_PATH}")
    REMOTE_PATH_REMOTE="\$HOME/${base}"
  fi
else
  REMOTE_PATH_REMOTE="${REMOTE_PATH}"
fi

# We'll create a tarball excluding unwanted files, copy it with scp, and extract on the remote host.
TAR_EXCLUDES=(--exclude 'venv' --exclude '.git' --exclude '__pycache__' --exclude 'Reports' --exclude '*.report')

TMP_ARCHIVE="/tmp/oobir_deploy_$$.tar.gz"
echo "Creating archive ${TMP_ARCHIVE} (this may take a moment)"
tar czf "${TMP_ARCHIVE}" "${TAR_EXCLUDES[@]}" .

echo "Copying archive to ${REMOTE}:${TMP_ARCHIVE}"
scp "${TMP_ARCHIVE}" "${REMOTE}:${TMP_ARCHIVE}"

echo "Extracting on remote host into ${REMOTE_PATH_REMOTE}"
ssh ${REMOTE} "mkdir -p '${REMOTE_PATH_REMOTE}' && tar xzf '${TMP_ARCHIVE}' -C '${REMOTE_PATH_REMOTE}' && rm -f '${TMP_ARCHIVE}' || true"

# clean up local temporary archive
rm -f "${TMP_ARCHIVE}"

echo "Running remote setup on ${REMOTE}"
ssh ${REMOTE} bash -s -- "${REMOTE_PATH_REMOTE}" <<'ENDSSH'
set -euo pipefail

# $1 will be the expanded remote path passed as an argument to this ssh session
REMOTE_PATH="$1"
echo "Remote working path: ${REMOTE_PATH}"
mkdir -p "${REMOTE_PATH}"
cd "${REMOTE_PATH}"

echo '1) Ensure Docker is installed (may prompt for sudo)'
if ! command -v docker >/dev/null 2>&1; then
  echo 'Installing Docker via get.docker.com script (requires sudo)'
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  rm -f get-docker.sh
fi

echo '2) Ensure docker-compose (docker compose) is available'
if ! docker compose version >/dev/null 2>&1; then
  echo 'docker compose not available; please ensure Docker Engine with Compose plugin is installed.'
fi

echo '3) Start Ollama container (docker compose)'
if [ -f docker-compose.yml ]; then
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose pull || true
    docker compose up -d --build --force-recreate || true
    # Pull both canonical and alias model names to satisfy runtime lookups
    docker compose exec ollama ollama pull huihui_ai/llama3.2-abliterate:3b || true
    docker compose exec ollama ollama pull llama3.2:1b || true
    # Ensure web assets are present inside nginx docroot (handles root-owned host dir)
    if docker compose ps web >/dev/null 2>&1; then
      docker compose cp web/. web:/usr/share/nginx/html/ || true
    fi
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose pull || true
    docker-compose up -d --build --force-recreate || true
    docker exec -i ollama ollama pull huihui_ai/llama3.2-abliterate:3b || true
    docker exec -i ollama ollama pull llama3.2:1b || true
    # Ensure web assets are present inside nginx docroot (handles root-owned host dir)
    if docker ps --format '{{.Names}}' | grep -q '^oobir_web$'; then
      docker cp web/. oobir_web:/usr/share/nginx/html/ || true
    fi
  else
    echo 'No docker compose available; skipping container start'
  fi
else
  echo "No docker-compose.yml found in ${REMOTE_PATH}; skipping container start"
fi

echo '4) Create Python venv and install requirements'
if [ ! -d venv ]; then
  python3 -m venv venv
fi
. venv/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

echo '5) Run unit tests in the project venv'
python -m unittest discover -v || true

echo '6) (optional) Run a demo flow.py invocation against local Ollama (host port 11435)'
python flow.py --host http://localhost:11435 AAPL get_ai_fundamental_analysis || true
exit 0
ENDSSH

echo "Deployment finished. Check the remote logs or run the script again locally."
echo "=================================================="
echo "Next steps:"
echo "  - SSH to remote: ssh ${REMOTE}"
echo "  - Navigate to: ${REMOTE_PATH_REMOTE}"
echo "  - Start API: docker compose up or python flow_api.py"
echo "  - Check logs: docker compose logs -f or tail -f *.log" 
