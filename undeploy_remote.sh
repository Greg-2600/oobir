#!/usr/bin/env bash
set -euo pipefail

# Usage: ./undeploy_remote.sh [user@host] [remote_path]
# Default: greg@192.168.1.248 ~/oobir

REMOTE=${1:-greg@192.168.1.248}
REMOTE_PATH=${2:-'~/oobir'}

echo "==============================================="
echo "Undeploying OOBIR from ${REMOTE}:${REMOTE_PATH}"
echo "==============================================="

# Prepare remote path expansion
if [[ "${REMOTE_PATH}" == ~* ]]; then
  # Strip the tilde and use $HOME on remote side
  REMOTE_PATH_REMOTE="\$HOME${REMOTE_PATH:1}"
elif [[ "${REMOTE_PATH}" == /* ]]; then
  if [[ "${REMOTE_PATH}" =~ ^/Users/[^/]+(/.*)?$ ]]; then
    tail="${BASH_REMATCH[1]:-}"
    REMOTE_PATH_REMOTE="\$HOME${tail}"
  else
    base=$(basename "${REMOTE_PATH}")
    REMOTE_PATH_REMOTE="\$HOME/${base}"
  fi
else
  REMOTE_PATH_REMOTE="${REMOTE_PATH}"
fi

echo "Remote working path: ${REMOTE_PATH_REMOTE}"

# Execute cleanup on remote host
ssh ${REMOTE} bash -s -- "${REMOTE_PATH_REMOTE}" <<'ENDSSH'
set -euo pipefail

REMOTE_PATH="$1"
echo ""
echo "Step 1: Navigating to ${REMOTE_PATH}"
if [ ! -d "${REMOTE_PATH}" ]; then
  echo "Warning: Directory ${REMOTE_PATH} does not exist. Nothing to undeploy."
  exit 0
fi

cd "${REMOTE_PATH}"

echo ""
echo "Step 2: Stopping and removing containers"
if [ -f docker-compose.yml ]; then
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "  - Using 'docker compose' command"
    docker compose down --remove-orphans || echo "Warning: docker compose down failed"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "  - Using 'docker-compose' command"
    docker-compose down --remove-orphans || echo "Warning: docker-compose down failed"
  else
    echo "Warning: No docker compose command available"
  fi
else
  echo "  - No docker-compose.yml found, skipping container removal"
fi

echo ""
echo "Step 3: Removing Docker volumes"
if command -v docker >/dev/null 2>&1; then
  # Find volumes associated with this project (oobir prefix)
  VOLUMES=$(docker volume ls -q | grep -E '^oobir' || true)
  if [ -n "$VOLUMES" ]; then
    echo "  - Found volumes to remove:"
    echo "$VOLUMES" | sed 's/^/    /'
    echo "$VOLUMES" | xargs docker volume rm || echo "Warning: Some volumes could not be removed"
  else
    echo "  - No oobir volumes found"
  fi
else
  echo "Warning: Docker not available, skipping volume removal"
fi

echo ""
echo "Step 4: Removing Docker images"
if command -v docker >/dev/null 2>&1; then
  # Remove oobir app image
  if docker images | grep -q 'oobir'; then
    echo "  - Removing oobir images"
    docker images | grep 'oobir' | awk '{print $3}' | xargs docker rmi -f || echo "Warning: Some images could not be removed"
  else
    echo "  - No oobir images found"
  fi
  
  # Optionally remove ollama image (commented out by default to preserve model data)
  # Uncomment the next 4 lines if you want to remove ollama image too
  # if docker images | grep -q 'ollama/ollama'; then
  #   echo "  - Removing ollama/ollama images"
  #   docker images | grep 'ollama/ollama' | awk '{print $3}' | xargs docker rmi -f || echo "Warning: Ollama image could not be removed"
  # fi
else
  echo "Warning: Docker not available, skipping image removal"
fi

echo ""
echo "Step 5: Removing project directory (optional)"
if [ -t 0 ]; then
  # Interactive mode: prompt for confirmation
  read -p "Remove project directory ${REMOTE_PATH}? [y/N]: " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ..
    rm -rf "${REMOTE_PATH}"
    echo "  - Project directory removed"
  else
    echo "  - Project directory preserved"
  fi
else
  # Non-interactive mode: preserve directory by default
  echo "  - Running in non-interactive mode, preserving project directory"
fi

echo ""
echo "Step 6: Cleaning up dangling resources"
if command -v docker >/dev/null 2>&1; then
  echo "  - Pruning unused Docker resources"
  docker system prune -f || echo "Warning: Docker prune failed"
fi

echo ""
echo "✅ Undeployment complete!"
echo ""
echo "Summary:"
echo "  - Containers: stopped and removed"
echo "  - Volumes: removed (oobir_*)"
echo "  - Images: oobir images removed"
echo "  - Ollama image: preserved (contains model data)"
echo ""
echo "To redeploy, run: ./deploy_remote.sh <user@host> <remote_path>"

exit 0
ENDSSH

echo ""
echo "==============================================="
echo "✅ Remote undeployment finished"
echo "==============================================="
