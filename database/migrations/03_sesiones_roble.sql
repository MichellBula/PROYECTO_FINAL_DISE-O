-- Ejecutar SOLO UNA VEZ desde DBeaver conectado a gestion_personas como gestion_admin.
-- Esta migracion agrega tablas nuevas; NO modifica persona ni auditoria.
BEGIN;

CREATE TABLE IF NOT EXISTS public.auth_sesiones (
    token_hash CHAR(64) PRIMARY KEY,
    usuario_roble_id UUID NOT NULL,
    correo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    csrf_token TEXT NOT NULL,
    creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expira_en TIMESTAMPTZ NOT NULL,
    revocada_en TIMESTAMPTZ,
    CONSTRAINT auth_token_formato CHECK (token_hash ~ '^[a-f0-9]{64}$'),
    CONSTRAINT auth_fecha_valida CHECK (expira_en > creada_en)
);

CREATE INDEX IF NOT EXISTS auth_sesiones_vigencia_idx
    ON public.auth_sesiones (expira_en)
    WHERE revocada_en IS NULL;

CREATE TABLE IF NOT EXISTS public.auth_eventos (
    id BIGSERIAL PRIMARY KEY,
    usuario_roble_id UUID,
    evento TEXT NOT NULL CHECK (
        evento IN ('LOGIN_OK', 'LOGIN_RECHAZADO', 'LOGOUT')
    ),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Esta primera fase reutiliza el rol ya creado en el proyecto.
-- Mas adelante separar los roles por microservicio (minimo privilegio).
GRANT USAGE ON SCHEMA public TO gestion_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.auth_sesiones TO gestion_api;
GRANT SELECT, INSERT ON TABLE public.auth_eventos TO gestion_api;
GRANT USAGE, SELECT ON SEQUENCE public.auth_eventos_id_seq TO gestion_api;

COMMIT;
