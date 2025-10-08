podman-compose down
podman-compose up -d

uv run src/service/clear_filesystem_cache.py