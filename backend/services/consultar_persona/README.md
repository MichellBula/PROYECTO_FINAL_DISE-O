# Consultar persona: FastAPI + PostgreSQL + Microsoft Entra ID

Este es SOLO el microservicio de consulta. No incluye aun los otros cinco servicios del proyecto.

## Ejecutar en PowerShell del PC principal

1. Mantener tunel SSH abierto en otra terminal:

   `ssh -i "$HOME\.ssh\cotespc_ed25519" -N -L 127.0.0.1:15432:127.0.0.1:5432 cotes@192.168.40.73`

2. Abrir terminal aqui: `cd backend/services/consultar_persona`
3. `py -m venv .venv`
4. `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
5. `Copy-Item .env.example .env` y editar los valores reales (sin subirlos)
6. `.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`

Verificacion inicial: abrir `http://127.0.0.1:8000/salud`. Esperado `{"estado":"ok","postgres":"conectado"}`.
La ruta protegida `GET /personas/C%C3%A9dula/1234567890` debe devolver 401 SIN bearer token y escribir DENEGADO en auditoria.

La API valida firma RS256, emisor v2 del tenant, audiencia (ID app API), expiración, tenant y scope `personas.leer`.
No admite ID tokens ni tokens para Microsoft Graph. En Entra ID configurar accessTokenAcceptedVersion=2 para la app API.

Al obtener token válido desde el ejemplo React la API devolverá 200 si la persona existe o 404 si no existe. Ambos se auditan.

**Seguridad:** usar HTTPS al desplegar, credenciales solo en entorno backend, restringir CORS a los orígenes autorizados y proteger el acceso a la tabla `auditoria`. El servicio no implementa aún un flujo completo de auditoría de los otros microservicios.
