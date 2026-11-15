# Sistema de Gestion de Datos Personales

Proyecto final de Diseno de Software II. Arquitectura objetivo basada en **React**, **microservicios FastAPI**, **PostgreSQL 17 en Docker**, **Microsoft Entra ID**, **n8n** y **RAG**.

## Estado actual

- PostgreSQL funciona en un contenedor Docker, en Ubuntu WSL2 dentro del portatil servidor `CotesPC`.
- La base `gestion_personas` contiene las tablas `public.persona` y `public.auditoria`.
- Se han realizado pruebas manuales de CRUD, validaciones, unicidad, transacciones y auditoria.
- Entra ID, microservicios, n8n y RAG todavia no estan integrados.

## Estructura

```text
database/schema.sql            Modelo SQL inicial probado
infra/postgres/compose.yaml    Definicion reproducible del contenedor
infra/postgres/.env.example    Variables de entorno sin secretos
docs/modelo-datos.md           Decisiones del modelo y validaciones
docs/operacion-servidor.md     Administracion y respaldo inicial
frontend/README.md            Espacio reservado para React
backend/README.md             Espacio reservado para FastAPI
n8n/README.md                 Espacio reservado para flujos n8n/RAG
```

## Base de datos

La base se llama `gestion_personas`. El archivo `database/schema.sql` define las tablas e indices iniciales. Para crear una **nueva** base vacia, conectar DBeaver o `psql` a esa base y ejecutar el script completo.

**No ejecutar `schema.sql` como migracion de una base que ya tiene otra estructura**: `CREATE TABLE IF NOT EXISTS` no modifica columnas ni restricciones de tablas existentes. Los cambios futuros van en migraciones versionadas.

## Seguridad

- No subir archivos `.env`, claves privadas, respaldos ni datos personales.
- PostgreSQL publica el puerto unicamente en `127.0.0.1` del servidor; desde un equipo externo se utiliza un tunel SSH.
- El frontend React nunca recibira las credenciales de PostgreSQL.
- Los tokens de Microsoft Entra ID deben validarse en el backend, y los permisos de cada operacion deben comprobarse en los microservicios.
- El usuario administrador `gestion_admin` solo debe utilizarse para administracion. Se creara otro usuario de permisos limitados para FastAPI.

## Documentacion

Leer `docs/modelo-datos.md` y `docs/operacion-servidor.md` antes de crear nuevas tablas o reiniciar el contenedor.
