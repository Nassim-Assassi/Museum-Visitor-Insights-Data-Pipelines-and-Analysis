#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

psql "host=$DATABASE_HOST port=$DATABASE_PORT dbname=$DATABASE_DB user=$DATABASE_USER password=$DATABASE_PASSWORD" -c "TRUNCATE TABLE kiosk_output;"
