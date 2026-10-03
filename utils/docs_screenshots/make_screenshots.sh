#!/usr/bin/env bash
# Regenerate the documentation screenshots (docs/img/*.png). See README.md in this directory.
#
#   utils/docs_screenshots/make_screenshots.sh [name ...]
#
# Recreates the database $DOCS_DB_NAME (default netbox_docs), migrates and seeds it, runs NetBox on $DOCS_PORT
# (default 8001) and captures the screenshots with headless Chromium. The development database is not touched.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NETBOX_DIR="${NETBOX_DIR:-$(cd "$REPO/../netbox" && pwd)}"
NETBOX_PYTHON="${NETBOX_PYTHON:-$NETBOX_DIR/venv/bin/python}"
MANAGE="$NETBOX_DIR/netbox/manage.py"
PORT="${DOCS_PORT:-8001}"
OUT="${DOCS_OUT:-$REPO/docs/img}"
WORK="$(mktemp -d)"

export DOCS_DB_NAME="${DOCS_DB_NAME:-netbox_docs}"
export NETBOX_CONFIGURATION=docs_configuration
export PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}"
export DOCS_IDS_FILE="$WORK/ids.json"

SERVER_PID=
cleanup() {
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
    rm -rf "$WORK"
}
trap cleanup EXIT

echo "==> Playwright (in $HERE/.venv)"
if [ ! -x "$HERE/.venv/bin/playwright" ]; then
    python3 -m venv "$HERE/.venv"
    "$HERE/.venv/bin/pip" install --quiet playwright
fi
"$HERE/.venv/bin/playwright" install chromium

echo "==> Recreating database $DOCS_DB_NAME"
(cd "$NETBOX_DIR/netbox" && "$NETBOX_PYTHON" - <<'EOF'
import os
import psycopg
from netbox.configuration import DATABASES

db = DATABASES['default']
name = os.environ['DOCS_DB_NAME']
if name == db['NAME']:
    raise SystemExit(f'DOCS_DB_NAME must differ from the development database ({name})')
with psycopg.connect(host=db.get('HOST') or None, port=db.get('PORT') or None, user=db['USER'],
                     password=db['PASSWORD'], dbname='postgres', autocommit=True) as conn:
    conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    conn.execute(f'CREATE DATABASE "{name}" OWNER "{db["USER"]}"')
EOF
)

echo "==> Migrating"
"$NETBOX_PYTHON" "$MANAGE" migrate --no-input >"$WORK/migrate.log" || { cat "$WORK/migrate.log"; exit 1; }
"$NETBOX_PYTHON" "$MANAGE" shell --no-imports -c "from django.core.cache import cache; cache.clear()"

echo "==> Seeding"
"$NETBOX_PYTHON" "$MANAGE" shell --no-imports <"$HERE/seed.py"

echo "==> Starting NetBox on port $PORT"
"$NETBOX_PYTHON" "$MANAGE" runserver --insecure --noreload "127.0.0.1:$PORT" >"$WORK/server.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 60); do
    curl -sf -o /dev/null "http://127.0.0.1:$PORT/login/" && break
    kill -0 "$SERVER_PID" 2>/dev/null || { cat "$WORK/server.log"; exit 1; }
    sleep 1
done

echo "==> Capturing into $OUT"
"$HERE/.venv/bin/python" "$HERE/capture.py" --ids "$DOCS_IDS_FILE" --out "$OUT" \
    --base-url "http://127.0.0.1:$PORT" "$@"
