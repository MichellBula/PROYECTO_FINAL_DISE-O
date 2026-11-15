# Modelo inicial de datos (v1)

Fuente de verdad: `database/schema.sql`. Base de datos: `gestion_personas`; esquema: `public`.

## `persona`

- `id_persona`: UUID, clave primaria, generado con `gen_random_uuid()`.
- `tipo_documento`: cedula o tarjeta de identidad.
- `numero_documento`: texto de 1 a 10 digitos (no entero, para preservar ceros iniciales).
- La pareja (`tipo_documento`, `numero_documento`) es unica.
- `primer_nombre`, `segundo_nombre`, `apellidos`: hasta 30, 30 y 60 caracteres. No admiten numeros. `segundo_nombre` es opcional.
- `fecha_nacimiento`: `DATE`. La comprobacion de fecha futura queda pendiente en FastAPI.
- `genero`: valores permitidos en la restriccion `ck_persona_genero`.
- `correo`: `VARCHAR(255)`, opcional, con verificacion basica de formato.
- `celular`: `VARCHAR(10)`, opcional, exactamente 10 digitos cuando se informa.
- `foto_ruta`: referencia externa al archivo; el maximo de 2 MB se valida antes de subirlo.
- `fecha_registro`: fecha y hora de creacion (`TIMESTAMPTZ`).

## `auditoria`

- `id_auditoria`: UUID, clave primaria.
- `usuario`: identificador de la identidad autenticada (mas adelante, Entra ID; no contrasenas ni tokens).
- `tipo_operacion`: `CREAR`, `MODIFICAR`, `CONSULTAR`, `ELIMINAR`, `CONSULTA_IA`, `CONSULTAR_AUDITORIA`.
- `tipo_documento`, `numero_documento`: campos opcionales relacionados logicamente con el documento consultado.
- `fecha_transaccion`: `TIMESTAMPTZ`.
- `resultado`: `EXITO`, `ERROR`, `DENEGADO`.
- `detalle`, `pregunta`, `respuesta`: contexto y resultados, evitando almacenar mas datos personales de los necesarios.

No existe FK de `auditoria` a `persona`: el historial debe sobrevivir a la eliminacion de una persona.

## Restricciones, auditoria y operaciones

- Ya se probaron insercion, unicidad del documento, seis validaciones, modificacion, eliminacion y registro de eventos.
- Las pruebas SQL de DBeaver escriben eventos de auditoria **explicitamente**. La base no crea logs por si sola para cada operacion.
- FastAPI registrara los eventos de las operaciones; escrituras y logs exitosos deben compartir una transaccion.
- Las consultas normales, fallos y accesos denegados necesitan tambien un diseno explicito de auditoria.
- Para calculos exactos de RAG, utilizar consultas estructuradas autorizadas a PostgreSQL.

## Cambios posteriores

No modificar `schema.sql` suponiendo que cambiara tablas ya existentes. Crear archivos SQL nuevos en `database/migrations/` y probar en una base de desarrollo antes de aplicarlos al servidor.
