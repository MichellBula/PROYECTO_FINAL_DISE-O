-- ============================================
-- MIGRACIÓN 04: REGISTRO Y ROLES DE USUARIOS
-- ============================================

BEGIN;


-- ============================================
-- 1. TABLA DE PERFILES DE USUARIO
-- ============================================

CREATE TABLE IF NOT EXISTS public.auth_perfiles (

    usuario_roble_id UUID PRIMARY KEY,

    correo VARCHAR(255) NOT NULL,

    nombre VARCHAR(100) NOT NULL,

    rol VARCHAR(20) NOT NULL DEFAULT 'CONSULTA',

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_auth_perfiles_rol
        CHECK (
            rol IN (
                'ADMINISTRADOR',
                'OPERADOR',
                'CONSULTA'
            )
        )
);


-- ============================================
-- 2. TABLA DE HISTORIAL DE CAMBIOS DE ROLES
-- ============================================

CREATE TABLE IF NOT EXISTS public.auth_cambios_rol (

    id BIGSERIAL PRIMARY KEY,

    administrador_roble_id UUID NOT NULL,

    usuario_roble_id UUID NOT NULL
        REFERENCES public.auth_perfiles(usuario_roble_id),

    rol_anterior VARCHAR(20) NOT NULL,

    rol_nuevo VARCHAR(20) NOT NULL,

    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()

);


-- ============================================
-- 3. REGISTRAR USUARIOS EXISTENTES
-- ============================================

-- Recupera los usuarios que ya iniciaron sesión
-- anteriormente mediante Roble.
--
-- Si un usuario tiene varias sesiones, utiliza
-- la información de su sesión más reciente.
--
-- Todos reciben inicialmente el rol CONSULTA.
-- Los roles superiores se asignarán posteriormente.

INSERT INTO public.auth_perfiles (
    usuario_roble_id,
    correo,
    nombre
)

SELECT DISTINCT ON (usuario_roble_id)

    usuario_roble_id,

    correo,

    nombre

FROM public.auth_sesiones

ORDER BY
    usuario_roble_id,
    creada_en DESC

ON CONFLICT (usuario_roble_id) DO NOTHING;


-- ============================================
-- 4. PERMISOS SOBRE LOS PERFILES
-- ============================================

GRANT SELECT, INSERT, UPDATE
ON public.auth_perfiles
TO gestion_api;


-- ============================================
-- 5. PERMISOS SOBRE EL HISTORIAL DE ROLES
-- ============================================

GRANT SELECT, INSERT
ON public.auth_cambios_rol
TO gestion_api;


-- ============================================
-- 6. PERMISOS SOBRE LA SECUENCIA
-- ============================================

GRANT USAGE, SELECT
ON SEQUENCE public.auth_cambios_rol_id_seq
TO gestion_api;


-- ============================================
-- 7. CONFIRMAR LA MIGRACIÓN
-- ============================================

COMMIT;