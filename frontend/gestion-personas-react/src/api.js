/**
 * El navegador se comunica solo con el proxy local de Vite (/api/*).
 * La cookie de sesión es HttpOnly: no se lee ni se guarda en JavaScript.
 */
async function solicitar(ruta, opciones = {}) {
  let respuesta;
  try {
    respuesta = await fetch(`/api${ruta}`, {
      credentials: 'include',
      ...opciones,
    });
  } catch {
    throw new Error('No se pudo conectar. Comprueba los puertos 8000, 8001 y 5173.');
  }

  const texto = await respuesta.text();
  let datos = {};
  try {
    datos = texto ? JSON.parse(texto) : {};
  } catch {
    // No mostrar HTML de proxy ni trazas de servidor al usuario.
  }

  if (!respuesta.ok) {
    const detalle = typeof datos.detail === 'string'
      ? datos.detail
      : `Solicitud rechazada (HTTP ${respuesta.status})`;
    const error = new Error(detalle);
    error.status = respuesta.status;
    throw error;
  }
  return datos;
}

export function iniciarSesion(email, password) {
  return solicitar('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
}

export function consultarSesion() {
  return solicitar('/auth/yo');
}

export async function cerrarSesion() {
  const sesion = await consultarSesion();
  return solicitar('/auth/logout', {
    method: 'POST',
    headers: { 'X-CSRF-Token': sesion.csrf_token },
  });
}

export function consultarPersona(tipoDocumento, numeroDocumento) {
  return solicitar(`/personas/${encodeURIComponent(tipoDocumento)}/${encodeURIComponent(numeroDocumento)}`);
}
