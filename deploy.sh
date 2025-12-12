#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/sefaz/docfinance"
SERVICE_NAME="docfinance-compose.service"
COMPOSE="/usr/local/bin/docker-compose -f ${APP_DIR}/docker-compose.yml -f ${APP_DIR}/docker-compose.prod.yml"

BOT_TOKEN="8370580581:AAHUgDfmCxk5s1Tkt2fOjgOb0IfRcGCFfjk"
CHAT_ID="6118776516"
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
CURL_BIN="$(command -v curl || echo /usr/bin/curl)"

notify() {
  local msg="$1"
  "$CURL_BIN" -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    -d parse_mode="Markdown" \
    --data-urlencode text="${msg}" >/dev/null 2>&1 || true
}

cd "$APP_DIR"

BEFORE=$(git rev-parse --short HEAD || echo "unknown")
REMOTE=$(git rev-parse --short origin/main 2>/dev/null || echo "unknown")
HOSTNAME="$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo "unknown")"
START_TS="$(date +%s)"
notify "🚀 Iniciando deploy do *docfinance* em *${HOSTNAME}* (local: ${BEFORE}; remoto: ${REMOTE})..."

UPDATED=0
FETCH_TS="$(date +%s)"
if git fetch --all; then
  REMOTE=$(git rev-parse --short origin/main || echo "unknown")
  if [ "$BEFORE" != "$REMOTE" ]; then
    if git reset --hard origin/main; then
      UPDATED=1
      DUR="$(( $(date +%s) - FETCH_TS ))"
      notify "✅ Código atualizado para ${REMOTE} (antes: ${BEFORE}) em ${DUR}s."
    else
      notify "❌ Falha ao aplicar atualização para ${REMOTE}."
    fi
  else
    DUR="$(( $(date +%s) - FETCH_TS ))"
    notify "ℹ️ Código já está em ${BEFORE} em ${DUR}s."
  fi
else
  notify "❌ Falha ao buscar remotos."
fi

AFTER=$(git rev-parse --short HEAD || echo "unknown")

BACKUP_DIR="${APP_DIR}/backups"
mkdir -p "$BACKUP_DIR"
STAMP=$(date +"%Y-%m-%d_%H%M")
INCOMING_DIR="${BACKUP_DIR}/incoming"
mkdir -p "$INCOMING_DIR"
sudo chown -R sefaz:sefaz "$BACKUP_DIR"
sudo chmod -R 755 "$BACKUP_DIR"

sudo mkdir -p "${APP_DIR}/staticfiles" "${APP_DIR}/media"
sudo chown -R sefaz:sefaz "${APP_DIR}/staticfiles" "${APP_DIR}/media"
sudo chmod -R 755 "${APP_DIR}/staticfiles" "${APP_DIR}/media"

sudo $COMPOSE up -d postgres

BK_TS="$(date +%s)"
sudo docker exec docfinance-postgres sh -lc "pg_dump -U docfinance -d docfinance -Fc -Z 9 -f /tmp/docfinance_${STAMP}.dump && pg_dump -U docfinance -d docfinance -f /tmp/docfinance_${STAMP}.sql" || true
sudo docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.dump "$BACKUP_DIR/docfinance_${STAMP}.dump" || true
sudo docker cp docfinance-postgres:/tmp/docfinance_${STAMP}.sql "$BACKUP_DIR/docfinance_${STAMP}.sql" || true
notify "🗄️ Backup gerado: ${STAMP} em $(( $(date +%s) - BK_TS ))s."

sudo $COMPOSE up -d backend
sudo $COMPOSE exec -T backend python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output /tmp/backup_fixture_${STAMP}.json || true
sudo docker cp docfinance-backend:/tmp/backup_fixture_${STAMP}.json "$BACKUP_DIR/backup_fixture_${STAMP}.json" || true
notify "🧾 Fixture gerada: backup_fixture_${STAMP}.json."

ls -t "$BACKUP_DIR"/docfinance_*.dump 2>/dev/null | tail -n +4 | xargs -r rm -f
ls -t "$BACKUP_DIR"/docfinance_*.sql 2>/dev/null | tail -n +4 | xargs -r rm -f
ls -t "$BACKUP_DIR"/backup_fixture_*.json 2>/dev/null | tail -n +4 | xargs -r rm -f

# Restauração opcional de dump vindo do ambiente local
INC_DUMP=$(ls -t "$INCOMING_DIR"/*.dump 2>/dev/null | head -n1 || true)
INC_SQL=$(ls -t "$INCOMING_DIR"/*.sql 2>/dev/null | head -n1 || true)
if [ -n "$INC_DUMP" ] || [ -n "$INC_SQL" ]; then
  sudo $COMPOSE stop backend || true
  if [ -n "$INC_DUMP" ]; then
    sudo docker cp "$INC_DUMP" docfinance-postgres:/tmp/incoming.dump
    sudo docker exec docfinance-postgres sh -lc "pg_restore -U docfinance -d docfinance --clean --if-exists -j 2 /tmp/incoming.dump"
    sudo docker exec docfinance-postgres sh -lc "rm -f /tmp/incoming.dump"
    sudo rm -f "$INC_DUMP"
    notify "✅ Banco restaurado a partir do dump (custom)."
  elif [ -n "$INC_SQL" ]; then
    sudo docker cp "$INC_SQL" docfinance-postgres:/tmp/incoming.sql
    sudo docker exec docfinance-postgres sh -lc "psql -U docfinance -d docfinance -f /tmp/incoming.sql"
    sudo docker exec docfinance-postgres sh -lc "rm -f /tmp/incoming.sql"
    sudo rm -f "$INC_SQL"
    notify "✅ Banco restaurado a partir do SQL."
  fi
  sudo $COMPOSE up -d backend
fi

ls -t "$INCOMING_DIR"/*.dump 2>/dev/null | tail -n +2 | xargs -r sudo rm -f
ls -t "$INCOMING_DIR"/*.sql 2>/dev/null | tail -n +2 | xargs -r sudo rm -f

SYS_TS="$(date +%s)"
if sudo systemctl restart "${SERVICE_NAME}"; then
  notify "✅ Stack atualizado pelo systemd em $(( $(date +%s) - SYS_TS ))s."
else
  notify "❌ Falha ao atualizar stack pelo systemd."
fi

MIG_TS="$(date +%s)"
if sudo $COMPOSE exec -T backend python manage.py migrate --noinput; then
  notify "✅ Migrações aplicadas em $(( $(date +%s) - MIG_TS ))s."
else
  notify "❌ Erro ao aplicar migrações."
fi

COL_TS="$(date +%s)"
if sudo $COMPOSE exec -T backend python manage.py collectstatic --noinput; then
  notify "✅ Arquivos estáticos coletados em $(( $(date +%s) - COL_TS ))s."
else
  notify "❌ Erro ao coletar estáticos."
fi

COUNT=$(sudo docker exec docfinance-postgres sh -lc "psql -U docfinance -d docfinance -t -c 'SELECT COUNT(*) FROM auth_user;'" | tr -d '[:space:]')
if [ -z "$COUNT" ] || [ "$COUNT" = "0" ]; then
  FIX="${APP_DIR}/backup_docfinance_2025-11-29_0054.json"
  if [ -f "$FIX" ]; then
    sudo docker cp "$FIX" docfinance-backend:/tmp/fixture.json || true
    sudo $COMPOSE exec -T backend python manage.py loaddata /tmp/fixture.json || true
    notify "✅ Dados iniciais carregados."
  else
    notify "ℹ️ Fixture não encontrada em $FIX; pulando carga."
  fi
fi

TOTAL="$(( $(date +%s) - START_TS ))"
UP_COUNT="$(sudo docker ps --format '{{.Names}}' | wc -l | tr -d '[:space:]')"
if [ "$UPDATED" = "1" ]; then
  notify "✅🎉 Deploy concluído: ${AFTER} (antes: ${BEFORE}; aplicado: ${REMOTE}). Tempo: ${TOTAL}s. Contêineres ativos: ${UP_COUNT}."
else
  notify "✅🎉 Deploy concluído: ${AFTER} (sem alterações; remoto: ${REMOTE}). Tempo: ${TOTAL}s. Contêineres ativos: ${UP_COUNT}."
fi
