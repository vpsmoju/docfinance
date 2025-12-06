#!/bin/sh
set -e
STAMP=$(date +%Y-%m-%d_%H%M)
DIR="$(pwd)/backups"
mkdir -p "$DIR"
docker exec docfinance-postgres sh -lc "pg_dump -U docfinance -d docfinance -Fc -Z 9 -f /tmp/docfinance_${STAMP}.dump && pg_dump -U docfinance -d docfinance -f /tmp/docfinance_${STAMP}.sql"
docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.dump "$DIR/docfinance_${STAMP}.dump"
docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.sql "$DIR/docfinance_${STAMP}.sql"
docker compose exec -T backend python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output "$DIR/backup_fixture_${STAMP}.json"
ls -t "$DIR"/docfinance_*.dump | tail -n +4 | xargs -r rm -f
ls -t "$DIR"/docfinance_*.sql | tail -n +4 | xargs -r rm -f
ls -t "$DIR"/backup_fixture_*.json | tail -n +4 | xargs -r rm -f
