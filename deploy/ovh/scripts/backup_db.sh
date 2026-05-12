#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$DEPLOY_DIR/backups/db}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

docker compose -f "$DEPLOY_DIR/docker-compose.prod.yml" --env-file "$DEPLOY_DIR/.env.vps" \
  exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/apitool_${TIMESTAMP}.sql"

echo "Backup creado en $BACKUP_DIR/apitool_${TIMESTAMP}.sql"
