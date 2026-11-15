# Operacion inicial del servidor PostgreSQL

El servidor PostgreSQL 17 esta en `CotesPC` -> Windows -> Ubuntu WSL2 -> Docker. En el servidor, el proyecto actual utiliza `~/gestion-datos-personales/infra/postgres`.

## Comandos (en Ubuntu WSL2, desde la carpeta de Compose)

```bash
cd ~/gestion-datos-personales/infra/postgres
sudo docker compose ps
sudo docker compose stop db
sudo docker compose start db
sudo docker compose logs --tail=50 db
```

El contenedor publica `127.0.0.1:5432` solamente. Para conectarse desde otro PC se usa un tunel SSH a Windows del servidor. La IP de Windows podria cambiar.

## Backup manual (en Ubuntu WSL2)

```bash
cd ~/gestion-datos-personales/infra/postgres
mkdir -p ~/respaldos-postgres
sudo docker compose exec -T db pg_dump -U gestion_admin -d gestion_personas -Fc > ~/respaldos-postgres/gestion_personas_$(date +%Y%m%d_%H%M%S).dump
ls -lh ~/respaldos-postgres/
```

Este archivo **puede contener datos personales**. No se sube a GitHub y debe copiarse a un almacenamiento seguro fuera del portatil servidor. Una copia de seguridad solo se considera confiable cuando se prueba su restauracion en una **base separada de pruebas** (nunca directamente en produccion).

## Precauciones

- Nunca ejecutar `sudo docker compose down -v` salvo que se desee borrar los volumenes de datos.
- No reemplazar a ciegas el `compose.yaml` existente en el servidor: cambios en los nombres del proyecto Compose o del volumen pueden hacer que PostgreSQL arranque con un volumen **nuevo y vacio**. Comparar primero con el archivo versionado.
- `.env` real permanece solo en el servidor. No enviarlo por chat ni subirlo al repositorio.
- El volumen persistente protege de eliminar el contenedor, no de averias del disco, robo o borrado accidental.
