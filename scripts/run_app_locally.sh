#!/bin/bash

# Check if APP_NAME was provided as a parameter
if [ $# -eq 0 ]; then
  echo "Error: No app name provided"
  echo "Usage: $0 <app_name>"
  exit 1
fi

# Configuration
APP_NAME="$1"
APP_DIR="./apps/${APP_NAME}"
SERVICE_DIR="${APP_DIR}/service"
UI_DIR="${APP_DIR}/ui"
PORT=8181

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
  echo "Error: App directory '$APP_DIR' not found"
  exit 1
fi

# Determine build context and Dockerfile path
if [ -f "${APP_DIR}/Containerfile" ]; then
  DOCKERFILE_PATH="${APP_DIR}/Containerfile"
  BUILD_CONTEXT="${APP_DIR}"
elif [ -f "${SERVICE_DIR}/Containerfile" ]; then
  DOCKERFILE_PATH="${SERVICE_DIR}/Containerfile"
  BUILD_CONTEXT="${SERVICE_DIR}"
elif [ -f "${APP_DIR}/Dockerfile" ]; then
  DOCKERFILE_PATH="${APP_DIR}/Dockerfile"
  BUILD_CONTEXT="${APP_DIR}"
elif [ -f "${SERVICE_DIR}/Dockerfile" ]; then
  DOCKERFILE_PATH="${SERVICE_DIR}/Dockerfile"
  BUILD_CONTEXT="${SERVICE_DIR}"
else
  echo "Error: No Containerfile or Dockerfile found for ${APP_NAME}"
  exit 1
fi
echo "Using Dockerfile: ${DOCKERFILE_PATH}"
echo "Build context: ${BUILD_CONTEXT}"

# Prepare .env file if needed
if [ -f "${BUILD_CONTEXT}/.env.sample" ] && [ ! -f "${BUILD_CONTEXT}/.env" ]; then
  echo "Creating .env from .env.sample"
  cp "${BUILD_CONTEXT}/.env.sample" "${BUILD_CONTEXT}/.env"

  echo "APP_ENV=development" >> "${BUILD_CONTEXT}/.env"
  echo "DEBUG=true" >> "${BUILD_CONTEXT}/.env"
fi

# Build the frontend if the ui directory exists
if [ -d "$UI_DIR" ]; then
  echo "Entering ${UI_DIR} and running 'pnpm build'..."
  pushd "$UI_DIR" > /dev/null || exit;
  pnpm build
  if [ $? -ne 0 ]; then
    echo "Error: 'pnpm build' failed in ${UI_DIR}"
    popd > /dev/null || exit;
    exit 1
  fi
  popd > /dev/null || exit;
else
  echo "Warning: UI directory '$UI_DIR' not found. Skipping frontend build."
fi

# Choose between docker or podman
if command -v podman &> /dev/null; then
  CMD="podman"
elif command -v docker &> /dev/null; then
  CMD="docker"
else
  echo "Error: Neither docker nor podman found. Please install one of them."
  exit 1
fi

# Build the image
echo "Building image..."
$CMD build -f "${DOCKERFILE_PATH}" -t "${APP_NAME}:local" "${BUILD_CONTEXT}"

# Special handling for law_monitoring app - start postgres first
POSTGRES_STARTED=false
if [ "$APP_NAME" == "law_monitoring" ]; then
  echo "Starting postgres service for law_monitoring app..."
  if [ -f "${SERVICE_DIR}/docker-compose.yml" ]; then
    pushd "${SERVICE_DIR}" > /dev/null || exit
    
    # Start postgres service
    if command -v docker-compose &> /dev/null; then
      docker-compose up -d postgres
    elif command -v docker &> /dev/null; then
      docker compose up -d postgres
    else
      echo "Error: docker-compose or docker compose not found"
      popd > /dev/null || exit
      exit 1
    fi
    
    echo "Waiting for postgres to be ready..."
    sleep 5
    
    # Verify postgres is running
    if command -v docker-compose &> /dev/null; then
      COMPOSE_CMD="docker-compose"
    else
      COMPOSE_CMD="docker compose"
    fi
    
    if ! $COMPOSE_CMD ps postgres | grep -q "Up"; then
      echo "❌ Postgres failed to start"
      $COMPOSE_CMD logs postgres
      $COMPOSE_CMD down
      popd > /dev/null || exit
      exit 1
    fi
    
    echo "✅ Postgres started successfully"
    POSTGRES_STARTED=true
    popd > /dev/null || exit
  else
    echo "Warning: docker-compose.yml not found in ${SERVICE_DIR}"
  fi
fi

# Function to cleanup postgres if it was started
cleanup_postgres() {
  if [ "$POSTGRES_STARTED" = true ]; then
    echo "Stopping postgres service..."
    pushd "${SERVICE_DIR}" > /dev/null || exit
    if command -v docker-compose &> /dev/null; then
      docker-compose down
    else
      docker compose down
    fi
    popd > /dev/null || exit
  fi
}

# Set trap to cleanup postgres on script exit
trap cleanup_postgres EXIT

# Run the container
echo "Running container on port ${PORT}..."
echo "Set the server url on the Assistant's dev mode to 'http://localhost:${PORT}' to preview the local app."

# For law_monitoring, use host networking so it can connect to postgres
if [ "$APP_NAME" == "law_monitoring" ]; then
  echo "Using host networking for law_monitoring to connect to postgres..."
  $CMD run -it --rm --network host -p ${PORT}:8080 "${APP_NAME}:local"
else
  $CMD run -it --rm -p ${PORT}:8080 "${APP_NAME}:local"
fi
