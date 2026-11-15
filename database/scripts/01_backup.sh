#!/usr/bin/env bash
set -euo pipefail
# Ejecutar EN Ubuntu WSL2 de CotesPC. No requiere PostgreSQL instalado en Ubuntu.
COMPOSE_DIR="${COMPOSE_DIR:-$HOME/gestion-datos-personales/infra/postgres}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/respaldos-postgres}"
cd "$COMPOSE_DIR"
umask 077
mkdir -p "$BACKUP_DIR"
DESTINO="$BACKUP_DIR/gestion_personas_$(date -u +%Y%m%d_%H%M%S)_UTC.dump"
printf 'Creando backup en %s\n' "$DESTINO"
if ! sudo docker compose exec -T db pg_dump -U gestion_admin -d gestion_personas -Fc > "$DESTINO"; then
  rm -f "$DESTINO"
  echo 'ERROR: pg_dump no termino correctamente.' >&2
  exit 1
fi
if [[ ! -s "$DESTINO" ]]; then
  echo 'ERROR: archivo vacio.' >&2
  rm -f "$DESTINO"
  exit 1
fi
# Verificar que al menos se puede leer el catalogo del archivo.
sudo docker compose exec -T db pg_restore -l < "$DESTINO" > /dev/null
sha256sum "$DESTINO" > "${DESTINO}.sha256"
printf '\nBACKUP=%s\n' "$DESTINO"
ls -lh "$DESTINO" "${DESTINO}.sha256"
echo 'IMPORTANTE: lleva una copia cifrada fuera de CotesPC; nunca a GitHub.'
