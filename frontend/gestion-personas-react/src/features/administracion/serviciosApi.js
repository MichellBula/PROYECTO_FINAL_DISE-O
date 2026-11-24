import { consultarSesion } from "../../services/api.js";

// Estas operaciones usan el Gateway; React nunca accede a Docker ni a PostgreSQL.
const RUTA = "/api/admin/servicios/consulta";

async function solicitarEstado(opciones = {}) {
  let respuesta;

  try {
    respuesta = await fetch(RUTA, {
      credentials: "include",
      cache: "no-store",
      ...opciones,
    });
  } catch {
    throw new Error("No fue posible conectar con el API Gateway.");
  }

  const datos = await respuesta.json().catch(() => ({}));

  if (!respuesta.ok) {
    throw new Error(
      typeof datos.detail === "string"
        ? datos.detail
        : `No se pudo realizar la operación (HTTP ${respuesta.status}).`
    );
  }

  if (typeof datos.habilitado !== "boolean") {
    throw new Error("El servidor devolvió un estado de servicio inválido.");
  }

  return datos;
}

export function obtenerEstadoConsulta() {
  return solicitarEstado();
}

export async function cambiarEstadoConsulta(habilitado) {
  if (typeof habilitado !== "boolean") {
    throw new Error("El nuevo estado debe ser verdadero o falso.");
  }

  // El Gateway valida este token y comprueba el rol ADMINISTRADOR.
  const sesion = await consultarSesion();
  if (!sesion.csrf_token) {
    throw new Error("La sesión no tiene un token de seguridad válido.");
  }

  return solicitarEstado({
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": sesion.csrf_token,
    },
    body: JSON.stringify({ habilitado }),
  });
}
