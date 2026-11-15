-- Sistema de Gestion de Datos Personales
-- PostgreSQL 17 | Esquema inicial v1
-- Ejecutar dentro de la base de datos gestion_personas.
-- Identidad de operadores: Microsoft Entra ID (fuera de estas tablas).

BEGIN;

-- Tabla principal: registros de personas
CREATE TABLE IF NOT EXISTS public.persona (
    id_persona UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_documento VARCHAR(20) NOT NULL,
    numero_documento VARCHAR(10) NOT NULL,
    primer_nombre VARCHAR(30) NOT NULL,
    segundo_nombre VARCHAR(30),
    apellidos VARCHAR(60) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero VARCHAR(25) NOT NULL,
    correo VARCHAR(255),
    celular VARCHAR(10),
    foto_ruta TEXT,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_persona_documento
        UNIQUE (tipo_documento, numero_documento),
    CONSTRAINT ck_persona_tipo_documento
        CHECK (tipo_documento IN ('Tarjeta de identidad', 'Cédula')),
    CONSTRAINT ck_persona_numero_documento
        CHECK (numero_documento ~ '^[0-9]{1,10}$'),
    CONSTRAINT ck_persona_primer_nombre
        CHECK (btrim(primer_nombre) <> '' AND primer_nombre !~ '[0-9]'),
    CONSTRAINT ck_persona_segundo_nombre
        CHECK (segundo_nombre IS NULL OR (btrim(segundo_nombre) <> '' AND segundo_nombre !~ '[0-9]')),
    CONSTRAINT ck_persona_apellidos
        CHECK (btrim(apellidos) <> '' AND apellidos !~ '[0-9]'),
    CONSTRAINT ck_persona_genero
        CHECK (genero IN ('Masculino', 'Femenino', 'No binario', 'Prefiero no reportar')),
    CONSTRAINT ck_persona_correo
        CHECK (correo IS NULL OR correo ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'),
    CONSTRAINT ck_persona_celular
        CHECK (celular IS NULL OR celular ~ '^[0-9]{10}$')
);

-- Tabla de trazabilidad independiente de la existencia de persona.
-- No crear una FK a persona: el historial debe sobrevivir a su eliminación.
CREATE TABLE IF NOT EXISTS public.auditoria (
    id_auditoria UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario VARCHAR(255) NOT NULL,
    tipo_operacion VARCHAR(30) NOT NULL,
    tipo_documento VARCHAR(20),
    numero_documento VARCHAR(10),
    fecha_transaccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    resultado VARCHAR(30) NOT NULL,
    detalle TEXT,
    pregunta TEXT,
    respuesta TEXT,

    CONSTRAINT ck_auditoria_tipo_operacion
        CHECK (tipo_operacion IN (
            'CREAR', 'MODIFICAR', 'CONSULTAR', 'ELIMINAR',
            'CONSULTA_IA', 'CONSULTAR_AUDITORIA'
        )),
    CONSTRAINT ck_auditoria_resultado
        CHECK (resultado IN ('EXITO', 'ERROR', 'DENEGADO')),
    CONSTRAINT ck_auditoria_documento
        CHECK (
            (tipo_documento IS NULL AND numero_documento IS NULL)
            OR
            (
                tipo_documento IS NOT NULL
                AND numero_documento IS NOT NULL
                AND tipo_documento IN ('Tarjeta de identidad', 'Cédula')
                AND numero_documento ~ '^[0-9]{1,10}$'
            )
        )
);

-- Consultas por documento y registros más recientes.
CREATE INDEX IF NOT EXISTS idx_auditoria_documento_fecha
    ON public.auditoria (tipo_documento, numero_documento, fecha_transaccion DESC);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha
    ON public.auditoria (fecha_transaccion DESC);

-- Ayuda en consultas estructuradas como "persona más joven".
CREATE INDEX IF NOT EXISTS idx_persona_fecha_nacimiento
    ON public.persona (fecha_nacimiento);

COMMIT;

-- Verificación del resultado (ejecutar después):
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name IN ('persona', 'auditoria')
-- ORDER BY table_name;
