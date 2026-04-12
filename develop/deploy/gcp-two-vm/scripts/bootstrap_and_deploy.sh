#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:?service is required: backend or ai}"
ARCHIVE_PATH="${2:-/tmp/healthmate-deploy.tar.gz}"
APP_ROOT="/opt/healthmate"
STAGE_DIR="/tmp/healthmate-stage"
TARGET_DIR="${APP_ROOT}/${SERVICE}"

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return
  fi

  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg lsb-release
  sudo install -m 0755 -d /etc/apt/keyrings

  if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
  fi

  ARCH="$(dpkg --print-architecture)"
  CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"

  echo \
    "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable docker
  sudo systemctl start docker
}

deploy_service() {
  rm -rf "${STAGE_DIR}"
  mkdir -p "${STAGE_DIR}"
  tar -xzf "${ARCHIVE_PATH}" -C "${STAGE_DIR}"

  sudo mkdir -p "${APP_ROOT}"
  sudo rm -rf "${TARGET_DIR}"
  sudo mkdir -p "${TARGET_DIR}"
  sudo cp -a "${STAGE_DIR}"/. "${TARGET_DIR}"/
  sudo chown -R "${USER}:${USER}" "${TARGET_DIR}"

  case "${SERVICE}" in
    backend)
      COMPOSE_DIR="${TARGET_DIR}/develop/deploy/gcp-two-vm/backend"
      HEALTH_URL="http://127.0.0.1:8080/api/health"
      ;;
    ai)
      COMPOSE_DIR="${TARGET_DIR}/develop/deploy/gcp-two-vm/ai"
      HEALTH_URL="http://127.0.0.1:8000/health"
      ;;
    *)
      echo "Unknown service: ${SERVICE}" >&2
      exit 1
      ;;
  esac

  cd "${COMPOSE_DIR}"
  sudo docker compose up -d --build --remove-orphans
  sudo docker compose ps

  if command -v curl >/dev/null 2>&1; then
    curl -fsS "${HEALTH_URL}" || true
  fi
}

install_docker
deploy_service
