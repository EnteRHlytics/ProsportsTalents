#!/bin/bash
set -euo pipefail

BACKUP_DIR=${1:-backups}
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL environment variable is not set" >&2
  exit 1
fi

pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
echo "Database backed up to $BACKUP_FILE"
