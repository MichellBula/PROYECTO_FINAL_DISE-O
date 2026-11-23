/**
 * Comunicación entre React y el API Gateway.
 *
 * Funcionalidades:
 * - Autenticación con Roble.
 * - Registro de usuarios.
 * - Verificación de correo.
 * - Administración de roles.
 * - Consulta y eliminación de personas.
 * - Consultas inteligentes.
 */

// =====================================================
// 1. FUNCIÓN GENERAL PARA SOLICITUDES
// =====================================================

async function solicitar(ruta, opciones = {}) {
  let respuesta;

  try {
    respuesta = await fetch(`/api${ruta}`, {
      credentials: "include",
      ...opciones,
    });
  } catch {
    throw new Error(
      "No se pudo conectar con la API Gateway. " +
      "Comprueba la conexión con el servidor."
    );
  }

  const texto = await respuesta.text();

  let datos = {};

  try {
    datos = texto ? JSON.parse(texto) : {};
  } catch {
    // No mostrar respuestas HTML ni errores internos.
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


// =====================================================
// 2. INICIAR SESIÓN
// =====================================================

export function iniciarSesion(email, password) {
  return solicitar("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });
}


// =====================================================
// 3. REGISTRAR USUARIO
// =====================================================

export function registrarUsuario(name, email, password) {
  return solicitar("/auth/registro", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
      email,
      password,
    }),
  });
}


// =====================================================
// 4. VERIFICAR CORREO
// =====================================================

export function verificarCorreo(email, code) {
  return solicitar("/auth/verificar-correo", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      code,
    }),
  });
}


// =====================================================
// 5. CONSULTAR SESIÓN
// =====================================================

export function consultarSesion() {
  return solicitar("/auth/yo");
}


// =====================================================
// 6. CERRAR SESIÓN
// =====================================================

export async function cerrarSesion() {
  const sesion = await consultarSesion();

  return solicitar("/auth/logout", {
    method: "POST",
    headers: {
      "X-CSRF-Token": sesion.csrf_token,
    },
  });
}


// =====================================================
// 7. CONSULTAR USUARIOS
// =====================================================

export function consultarUsuarios(pagina = 1, limite = 20) {
  const parametros = new URLSearchParams({
    pagina: String(pagina),
    limite: String(limite),
  });

  return solicitar(
    `/auth/usuarios?${parametros.toString()}`
  );
}


// =====================================================
// 8. CAMBIAR ROL DE UN USUARIO
// =====================================================

export async function cambiarRolUsuario(usuarioId, rol) {
  const sesion = await consultarSesion();

  if (!sesion.csrf_token) {
    throw new Error(
      "No se pudo obtener el token de seguridad."
    );
  }

  const id = encodeURIComponent(usuarioId);

  return solicitar(`/auth/usuarios/${id}/rol`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": sesion.csrf_token,
    },
    body: JSON.stringify({
      rol,
    }),
  });
}


// =====================================================
// 9. CONSULTAR PERSONA
// =====================================================

export function consultarPersona(tipoDocumento, numeroDocumento) {
  const numero = encodeURIComponent(numeroDocumento);
  const tipo = encodeURIComponent(tipoDocumento);

  return solicitar(
    `/personas/${numero}?tipo_documento=${tipo}`
  );
}


// =====================================================
// 10. ELIMINAR PERSONA
// =====================================================

export async function eliminarPersona(
  tipoDocumento,
  numeroDocumento
) {
  const numero = encodeURIComponent(numeroDocumento);
  const tipo = encodeURIComponent(tipoDocumento);

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


// =====================================================
// 11. CONSULTAS INTELIGENTES
// =====================================================

export async function consultarIA(pregunta) {
  const texto = pregunta.trim();

  if (!texto || texto.length > 500) {
    throw new Error(
      "La pregunta debe contener entre 1 y 500 caracteres."
    );
  }

  const sesion = await consultarSesion();

  if (!sesion.csrf_token) {
    throw new Error(
      "No se pudo obtener el token de seguridad de la sesión."
    );
  }

  return solicitar("/consultas-ia", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": sesion.csrf_token,
    },
    body: JSON.stringify({
      pregunta: texto,
    }),
  });
}