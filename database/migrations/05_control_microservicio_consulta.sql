-- ==========================================================
-- MIGRACION 05: CONTROL DEL MICROSERVICIO DE CONSULTA
-- Ejecutar una sola vez en gestion_personas como gestion_admin.
-- No detiene contenedores ni modifica registros de personas.
-- ==========================================================

BEGIN;

-- 1. Estado persistente de los servicios administrables.
CREATE TABLE IF NOT EXISTS public.control_servicios (
    servicio VARCHAR(32) PRIMARY KEY,
    habilitado BOOLEAN NOT NULL DEFAULT TRUE,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_por UUID NULL
        REFERENCES public.auth_perfiles(usuario_roble_id),
    CONSTRAINT ck_control_servicios_nombre
        CHECK (servicio IN ('CONSULTA'))
);

-- Se registra inicialmente como habilitado.
-- ON CONFLICT evita reactivar un servicio que ya fue deshabilitado.
INSERT INTO public.control_servicios (servicio, habilitado)
VALUES ('CONSULTA', TRUE)
ON CONFLICT (servicio) DO NOTHING;

-- 2. Historial de cambios: permite saber quien lo activo o desactivo.
CREATE TABLE IF NOT EXISTS public.control_servicios_cambios (
    id BIGSERIAL PRIMARY KEY,
    servicio VARCHAR(32) NOT NULL
        REFERENCES public.control_servicios(servicio),
    administrador_roble_id UUID NOT NULL
        REFERENCES public.auth_perfiles(usuario_roble_id),
    habilitado_anterior BOOLEAN NOT NULL,
    habilitado_nuevo BOOLEAN NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_control_servicios_cambio_real
        CHECK (habilitado_anterior <> habilitado_nuevo)
);

-- 3. El backend puede consultar y actualizar el estado.
-- No se le concede permiso DELETE ni INSERT sobre el estado.
GRANT SELECT, UPDATE
ON TABLE public.control_servicios
TO gestion_api;

-- 4. El backend registra las acciones en el historial.
GRANT SELECT, INSERT
ON TABLE public.control_servicios_cambios
TO gestion_api;

GRANT USAGE, SELECT
ON SEQUENCE public.control_servicios_cambios_id_seq
TO gestion_api;

COMMIT;
