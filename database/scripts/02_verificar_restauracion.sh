#!/usr/bin/env bash
set -euo pipefail
# Ejecutar EN Ubuntu WSL2. Restaura en BD separada; nunca toca gestion_personas.
if [[ $# -ne 1 || ! -s "$1" ]]; then
  echo 'Uso: bash database/scripts/02_verificar_restauracion.sh /ruta/backup.dump' >&2
  exit 2
fi
BACKUP="$(realpath "$1")"
COMPOSE_DIR="${COMPOSE_DIR:-$HOME/gestion-datos-personales/infra/postgres}"
TEST_DB='gestion_personas_restauracion'
cd "$COMPOSE_DIR"
EXISTE="$(sudo docker compose exec -T db psql -U gestion_admin -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${TEST_DB}'")"
if [[ "$EXISTE" == '1' ]]; then
  echo "ABORTADO: ${TEST_DB} ya existe. No se sobreescribio ninguna base." >&2
  echo 'Si confirmas que es una base de pruebas prescindible, elimínala manualmente y repite.' >&2
  exit 1
fi
sudo docker compose exec -T db createdb -U gestion_admin "$TEST_DB"
echo "Restaurando archivo EN: $TEST_DB"
sudo docker compose exec -T db pg_restore --exit-on-error --no-owner --no-acl -U gestion_admin -d "$TEST_DB" < "$BACKUP"
echo 'Conteos en el respaldo restaurado:'
RESTAURADO="$(sudo docker compose exec -T db psql -U gestion_admin -d "$TEST_DB" -tAc 'SELECT (SELECT COUNT(*) FROM public.persona), (SELECT COUNT(*) FROM public.auditoria)')"
echo "$RESTAURADO"
echo 'Conteos actuales en la base original (pueden haber cambiado desde el backup):'
ORIGINAL="$(sudo docker compose exec -T db psql -U gestion_admin -d gestion_personas -tAc 'SELECT (SELECT COUNT(*) FROM public.persona), (SELECT COUNT(*) FROM public.auditoria)')"
echo "$ORIGINAL"
echo "Verificacion: tablas restauradas. Base de prueba conservada: $TEST_DB"
echo 'Eliminación MANUAL posterior, solo si deseas borrarla:'
echo "sudo docker compose exec -T db dropdb -U gestion_admin '$TEST_DB'"
