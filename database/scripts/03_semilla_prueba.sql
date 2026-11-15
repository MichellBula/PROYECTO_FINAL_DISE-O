-- Ejecutar UNA sola vez, en DBeaver conectado a gestion_personas.
-- Una persona ficticia de prueba, registrada con auditoria en la misma transaccion.
BEGIN;
WITH creada AS (
    INSERT INTO public.persona (
        tipo_documento, numero_documento, primer_nombre, apellidos,
        fecha_nacimiento, genero, correo, celular
    ) VALUES (
        'Cédula', '9900000099', 'Persona', 'De Prueba',
        DATE '2001-02-03', 'Prefiero no reportar', 'persona.ficticia@example.com', '3000000099'
    )
    ON CONFLICT (tipo_documento, numero_documento) DO NOTHING
    RETURNING tipo_documento, numero_documento
)
INSERT INTO public.auditoria (usuario, tipo_operacion, tipo_documento, numero_documento, resultado, detalle)
SELECT 'PRUEBA_MANUAL_DBEAVER', 'CREAR', tipo_documento, numero_documento, 'EXITO',
       'Registro de persona ficticia para probar acceso autenticado desde React'
FROM creada;
COMMIT;
SELECT tipo_documento, numero_documento, primer_nombre FROM public.persona WHERE numero_documento='9900000099';
