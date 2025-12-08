#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/sefaz/docfinance"
SERVICE_NAME="docfinance-compose.service"
COMPOSE="/usr/local/bin/docker-compose -f ${APP_DIR}/docker-compose.yml -f ${APP_DIR}/docker-compose.prod.yml"

BOT_TOKEN="8370580581:AAHUgDfmCxk5s1Tkt2fOjgOb0IfRcGCFfjk"
CHAT_ID="6118776516"

notify() {
  local msg="$1"
  curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    -d parse_mode="Markdown" \
    --data-urlencode text="${msg}" >/dev/null
}

cd "$APP_DIR"

CURRENT_COMMIT=$(git rev-parse --short HEAD || echo "unknown")
notify "🚀 Iniciando deploy do *docfinance* (commit atual: ${CURRENT_COMMIT})..."

if git fetch --all && git reset --hard origin/main; then
  notify "✅ Código atualizado com sucesso."
else
  notify "❌ Falha ao atualizar código."
fi

NEW_COMMIT=$(git rev-parse --short HEAD)

BACKUP_DIR="${APP_DIR}/backups"
mkdir -p "$BACKUP_DIR"
STAMP=$(date +"%Y-%m-%d_%H%M")

sudo $COMPOSE up -d postgres

sudo docker exec docfinance-postgres sh -lc "pg_dump -U docfinance -d docfinance -Fc -Z 9 -f /tmp/docfinance_${STAMP}.dump && pg_dump -U docfinance -d docfinance -f /tmp/docfinance_${STAMP}.sql" || true
sudo docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.dump "$BACKUP_DIR/docfinance_${STAMP}.dump" || true
sudo docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.sql "$BACKUP_DIR/docfinance_${STAMP}.sql" || true

sudo $COMPOSE up -d backend
sudo $COMPOSE exec -T backend python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output /tmp/backup_fixture_${STAMP}.json || true
sudo docker cp docfinance-backend:/tmp/backup_fixture_${STAMP}.json "$BACKUP_DIR/backup_fixture_${STAMP}.json" || true

ls -t "$BACKUP_DIR"/docfinance_*.dump 2>/dev/null | tail -n +4 | xargs -r rm -f
ls -t "$BACKUP_DIR"/docfinance_*.sql 2>/dev/null | tail -n +4 | xargs -r rm -f
ls -t "$BACKUP_DIR"/backup_fixture_*.json 2>/dev/null | tail -n +4 | xargs -r rm -f

if sudo systemctl restart "${SERVICE_NAME}"; then
  notify "✅ Stack atualizado pelo systemd."
else
  notify "❌ Falha ao atualizar stack pelo systemd."
fi

if sudo $COMPOSE exec -T backend python manage.py migrate --noinput; then
  notify "✅ Migrações aplicadas."
else
  notify "❌ Erro ao aplicar migrações."
fi

if sudo $COMPOSE exec -T backend python manage.py collectstatic --noinput; then
  notify "✅ Arquivos estáticos coletados."
else
  notify "❌ Erro ao coletar estáticos."
fi

notify "✅🎉 Deploy concluído: ${NEW_COMMIT} (antes: ${CURRENT_COMMIT}). Stack atualizado."
