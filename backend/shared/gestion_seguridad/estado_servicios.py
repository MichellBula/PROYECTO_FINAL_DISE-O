"""
Estado persistente de los microservicios administrables.

La base de datos es la fuente de verdad: consultar_persona lee el estado
antes de atender cada solicitud y el API Gateway permite modificarlo
únicamente a usuarios ADMINISTRADOR.
"""

import logging
from uuid import UUID

import psycopg
from fastapi import HTTPException

from .sesiones import conexion

logger = logging.getLogger(__name__)
SERVICIO_CONSULTA = "CONSULTA"


def obtener_estado_consulta() -> dict:
    """Lee el estado de consulta directamente de PostgreSQL."""
    with conexion() as conn:
        fila = conn.execute(
            """
            SELECT servicio, habilitado, actualizado_en, actualizado_por
            FROM public.control_servicios
            WHERE servicio = %s
            """,
            (SERVICIO_CONSULTA,),
        ).fetchone()

    if fila is None:
        raise RuntimeError("No existe la configuración del servicio CONSULTA")

    return dict(fila)


def cambiar_estado_consulta(habilitado: bool, administrador_id: str) -> dict:
    """
    Cambia el estado y registra el historial en una sola transacción.
    No crea eventos si el servicio ya tenía el estado solicitado.

    La validación del rol ADMINISTRADOR y del token CSRF corresponde
    al API Gateway antes de llamar a esta función.
    """
    admin_uuid = UUID(str(administrador_id))

    with conexion() as conn:
        anterior = conn.execute(
            """
            SELECT habilitado
            FROM public.control_servicios
            WHERE servicio = %s
            FOR UPDATE
            """,
            (SERVICIO_CONSULTA,),
        ).fetchone()

        if anterior is None:
            raise RuntimeError("No existe la configuración del servicio CONSULTA")

        if anterior["habilitado"] != habilitado:
            estado = conn.execute(
                """
                UPDATE public.control_servicios
                SET habilitado = %s,
                    actualizado_en = NOW(),
                    actualizado_por = %s
                WHERE servicio = %s
                RETURNING servicio, habilitado, actualizado_en, actualizado_por
                """,
                (habilitado, admin_uuid, SERVICIO_CONSULTA),
            ).fetchone()

            conn.execute(
                """
                INSERT INTO public.control_servicios_cambios (
                    servicio,
                    administrador_roble_id,
                    habilitado_anterior,
                    habilitado_nuevo
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    SERVICIO_CONSULTA,
                    admin_uuid,
                    anterior["habilitado"],
                    habilitado,
                ),
            )
        else:
            estado = conn.execute(
                """
                SELECT servicio, habilitado, actualizado_en, actualizado_por
                FROM public.control_servicios
                WHERE servicio = %s
                """,
                (SERVICIO_CONSULTA,),
            ).fetchone()

    return dict(estado)


def exigir_consulta_habilitada() -> None:
    """
    Dependencia FastAPI para los endpoints de consultar_persona.
    Rechaza las consultas si el administrador deshabilitó el servicio.
    Ante un error de configuración o base de datos, falla de forma segura.
    """
    try:
        estado = obtener_estado_consulta()
    except (psycopg.Error, RuntimeError) as exc:
        logger.exception("No se pudo comprobar el estado del servicio CONSULTA")
        raise HTTPException(
            status_code=503,
            detail="No se pudo comprobar la disponibilidad del servicio de consulta",
        ) from exc

    if not estado["habilitado"]:
        raise HTTPException(
            status_code=503,
            detail="El microservicio de consulta está deshabilitado por el administrador",
        )
