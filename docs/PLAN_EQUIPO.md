# Integracion de Roble + PostgreSQL: guia para el equipo

**Alcance:** esta entrega prepara la autenticacion persistente y una dependencia compartida de verificacion. No sustituye automaticamente las dependencias de Entra en `consultar_persona`, ni los microservicios CRUD que falten. Es necesario probarlos antes de decir que estan protegidos.

## Archivos

- `database/migrations/03_sesiones_roble.sql`: agrega `auth_sesiones` y `auth_eventos`. No altera `persona` ni `auditoria`.
- `backend/shared/`: biblioteca instalable para que los servicios FastAPI validen la misma cookie consultando PostgreSQL.
- `backend/services/autenticacion/main.py`: reemplazo de la version de sesiones en memoria. `GET /salud`, `GET /preparado`, `POST /auth/login`, `GET /auth/yo`, `GET /auth/privado`, `POST /auth/logout`.
- `frontend/ejemplo_integracion/`: ejemplo Vite y funciones fetch; debe adaptarse al frontend existente.

## 0. Antes de empezar

1. Hacer copia de seguridad de PostgreSQL (sin borrar volumen ni crear la DB de nuevo).
2. Confirmar en el PC principal que el tunel SSH a PostgreSQL funciona. DBeaver debe conectar con `gestion_admin` en `127.0.0.1:15432`.
3. No ejecutar `docker compose down -v`.
4. Crear un commit o rama de respaldo del `main.py` actual, que ya funciona.
5. Cambiar cualquier contrasena que haya sido expuesta por error en mensajes o capturas. NO subir `.env`.

## 1. Migracion SQL

En DBeaver conectado a `gestion_personas` como `gestion_admin`, abrir `database/migrations/03_sesiones_roble.sql` y ejecutar TODO el script.
Comprobar:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN ('auth_sesiones', 'auth_eventos');
```

Deben aparecer DOS tablas. El script usa `CREATE TABLE IF NOT EXISTS`, pero si ya habia tablas con columnas diferentes hay que detenerse y revisar la definicion.

## 2. Instalar la biblioteca compartida

En PowerShell desde `C:\Github\PROYECTO_FINAL_DISE-O`:

```powershell
.\backend\services\autenticacion\.venv\Scripts\python.exe -m pip install -r .\backend\services\autenticacion\requirements.txt
.\backend\services\autenticacion\.venv\Scripts\python.exe -m pip install -e .\backend\shared
```

Para cualquier otro microservicio, instalar `backend/shared` en SU propio entorno virtual. En Docker la imagen debera copiar esta biblioteca durante la construccion.

## 3. Configuracion

Copiar `backend/services/autenticacion/.env.example` a `backend/services/autenticacion/.env`, **conservando el archivo `.env` existente si contiene el contrato correcto** y agregando variables de PostgreSQL.

Las credenciales `PGUSER=gestion_api` y `PGPASSWORD` son las mismas que utiliza `consultar_persona`, siempre que la migracion haya dado GRANT al rol. NO compartir contrasenas por chat o GitHub.

El servicio carga automaticamente su `.env`; el paquete compartido lee esas variables despues de la carga.

## 4. Arranque y pruebas

Abrir terminal independiente del tunel SSH:

```powershell
cd "C:\Github\PROYECTO_FINAL_DISE-O\backend\services\autenticacion"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Probar `http://127.0.0.1:8001/salud` y `http://127.0.0.1:8001/preparado`.

`/preparado` debe devolver `{"estado":"ok","postgres":"conectado","tablas_auth":"listas"}`; de lo contrario corregir la conexion o permisos.

Repetir login/yo/privado/logout con PowerShell sin imprimir contrasenas, siguiendo la prueba ya utilizada en el proyecto.

**Prueba clave de persistencia:** iniciar sesion, comprobar `/auth/yo`, reiniciar SOLO Uvicorn manteniendo PostgreSQL y tunel, y repetir `/auth/yo` desde el MISMO PowerShell con `-WebSession $sesionRoble`. Debe seguir dando `autenticado: True` porque ahora la sesion esta en PostgreSQL. Luego logout y 401.

**Control de acceso:** sin cookie, `/auth/privado` debe responder 401; con cookie autenticada debe responder 200.

En DBeaver:

```sql
SELECT evento, usuario_roble_id, fecha
FROM public.auth_eventos ORDER BY fecha DESC LIMIT 15;

SELECT usuario_roble_id, creada_en, expira_en, revocada_en
FROM public.auth_sesiones ORDER BY creada_en DESC LIMIT 15;
```

No mostrar ni copiar `token_hash`, `csrf_token`, contrasenas ni tokens.

## 5. Adaptar `consultar_persona` (NO hecho automaticamente)

Antes de tocarlo, revisar sus archivos `main.py` y `auth.py` actuales para identificar dependencias de Entra y rutas. El paquete por si solo NO anula la autorizacion previa.

Cuando este listo para usar Roble, instalar la biblioteca compartida en el `.venv` del servicio:

```powershell
.\backend\services\consultar_persona\.venv\Scripts\python.exe -m pip install -e .\backend\shared
```

En cada endpoint protegido de FastAPI se puede usar:

```python
from fastapi import Depends
from gestion_seguridad import exigir_usuario

# Ejemplo ilustrativo, adaptar al endpoint real:
# @app.get('/ruta-real-de-consulta')
# def consultar(..., usuario: dict = Depends(exigir_usuario)):
#     ...
```

**Alternativa:** `proteger_app(app)` aplica middleware a todas las rutas excepto salud/docs. No combinar a ciegas con dependencias antiguas de Entra ni con un sistema CORS no revisado. Probar acceso denegado, exitoso y auditoria por tipo/documento.

Una cookie solo funciona entre peticiones al mismo dominio de navegador; el puerto no forma parte del alcance de cookie. Recomendada una sola entrada `/api/*` via proxy del frontend. En el navegador entrar siempre por `http://127.0.0.1:5173`, NO mezclar `localhost` con `127.0.0.1`.

## 6. Incorporar a las companeras

**GitHub:** subir SOLO codigo, README, migraciones y `.env.example`. No subir bases de datos, tokens, claves SSH, dumps, capturas, `.env`, `.venv`.

**Roble:** las companeras pueden crear su cuenta en el mismo contrato mediante el flujo verificado por correo. Registrar contrasenas individuales; no compartir una sola cuenta.

**PostgreSQL:** sigue en el PC servidor, con contenedor independiente. Si cada companera ejecutara FastAPI en su computador, TI/propietario debe autorizarle una clave publica SSH individual al host servidor. Cada una puede abrir su propio tunel localhost `15432`; tienen que estar en la misma LAN o VPN autorizada. No abrir `5432` a Internet y no copiar la clave SSH privada del propietario.

```powershell
ssh -i "$HOME\.ssh\CLAVE_PERSONAL" -N -o ExitOnForwardFailure=yes -L 127.0.0.1:15432:127.0.0.1:5432 USUARIO_WINDOWS_SERVIDOR@IP_LAN_DEL_SERVIDOR
```

**Roles de base:** hoy se reutiliza `gestion_api` para esta prueba de equipo. Antes de produccion, crear roles separados por microservicio (lectura, alta, edicion, borrado, auditoria) y gestionar secretos por persona/servicio.

**Distribucion:** cada integrante debe instalar Python, crear su `.venv`, cargar SU `.env`, probar `/preparado` y ejecutar endpoints sin datos reales sensibles. Usar datos sinteticos durante desarrollo.

## 7. Pendientes antes de despliegue final

- Validar el servicio `consultar_persona` real con cookie Roble y quitar dependencias Entra que correspondan.
- Registrar consultas CRUD y accesos denegados en la tabla `auditoria` existente; `auth_eventos` solo cubre login/logout.
- Contenerizar por separado cada servicio, configurar gateway/reverse proxy HTTPS y permisos de DB minimos.
- Aplicar rate limiting en login, controles contra fuerza bruta, proteccion CSRF a todos los metodos de escritura, mecanismo de autorizacion por roles.
- Configurar politicas de retencion/borrado de sesiones y copias/restauraciones probadas.
- Confirmar el requisito de SSO del profesor: login con correo+contrasena de Roble NO es automaticamente SSO federado.

## Reglas de respaldo y Git

```gitignore
**/.env
**/.env.*
!**/.env.example
**/.venv/
**/__pycache__/
*.dump
```

Antes de confirmar: `git status --short` y `git check-ignore -v backend/services/autenticacion/.env backend/tests/.env`.
