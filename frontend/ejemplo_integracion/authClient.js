// En navegador usar SOLO rutas relativas, pasando por proxy Vite.
// No guardar contrasenas ni token de sesion en localStorage.
const ROOT = '/api/auth';

async function solicitud(ruta, opciones = {}) {
  const res = await fetch(`${ROOT}${ruta}`, {
    credentials: 'include',
    ...opciones,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return data;
}

export async function login(email, password) {
  return solicitud('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
}

export async function miSesion() {
  return solicitud('/yo');
}

export async function logout() {
  const sesion = await miSesion();
  return solicitud('/logout', {
    method: 'POST',
    headers: { 'X-CSRF-Token': sesion.csrf_token },
  });
}
