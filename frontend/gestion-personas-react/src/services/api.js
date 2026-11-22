
/**
 * Servicio de comunicación con la API Gateway.
 *
 * Todas las solicitudes se envían mediante /api.
 * La autenticación utiliza Roble y sesiones con cookies HttpOnly.
 * Las operaciones de escritura utilizan protección CSRF.
 */

async function solicitar(ruta, opciones = {}) {
  let respuesta;

  try {
    respuesta = await fetch(`/api${ruta}`, {
      credentials: "include",
      ...opciones,
    });
  } catch {
    throw new Error(
      "No se pudo conectar con la API Gateway. Comprueba la conexión con el servidor."
    );
  }

  const texto = await respuesta.text();

  let datos = {};

  try {
    datos = texto ? JSON.parse(texto) : {};
  } catch {
    // No mostrar HTML ni trazas internas al usuario.
  }

  if (!respuesta.ok) {
    const detalle =
      typeof datos.detail === "string"
        ? datos.detail
        : `Solicitud rechazada (HTTP ${respuesta.status})`;

    const error = new Error(detalle);
    error.status = respuesta.status;

    throw error;
  }

  return datos;
}


// ============================================
// AUTENTICACIÓN CON ROBLE
// ============================================

export function iniciarSesion(email, password) {
  return solicitar("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });
}


export function consultarSesion() {
  return solicitar("/auth/yo");
}


export async function cerrarSesion() {
  const sesion = await consultarSesion();

  return solicitar("/auth/logout", {
    method: "POST",
    headers: {
      "X-CSRF-Token": sesion.csrf_token,
    },
  });
}


// ============================================
// CONSULTAR PERSONA
// GET /api/personas/{documento}
// ============================================

export function consultarPersona(tipoDocumento, numeroDocumento) {
  const numero = encodeURIComponent(numeroDocumento);
  const tipo = encodeURIComponent(tipoDocumento);

  return solicitar(
    `/personas/${numero}?tipo_documento=${tipo}`
  );
}


// ============================================
// ELIMINAR PERSONA
// DELETE /api/personas/{documento}
// ============================================

export async function eliminarPersona(tipoDocumento, numeroDocumento) {
  const numero = encodeURIComponent(numeroDocumento);
  const tipo = encodeURIComponent(tipoDocumento);

  // Obtener el token CSRF de la sesión actual.
  const sesion = await consultarSesion();

  return solicitar(
    `/personas/${numero}?tipo_documento=${tipo}`,
    {
      method: "DELETE",
      headers: {
        "X-CSRF-Token": sesion.csrf_token,
      },
    }
  );
}
