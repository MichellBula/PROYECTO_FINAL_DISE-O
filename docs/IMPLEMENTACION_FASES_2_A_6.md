# Implementación guiada — fases 2 a 6

## Estado de partida
- BD `gestion_personas` en PostgreSQL 17 Docker en Ubuntu WSL2 de `CotesPC`.
- `public.persona` y `public.auditoria` YA existen. **No volver a ejecutar `schema.sql`**.
- DBeaver desde el PC principal mediante túnel `127.0.0.1:15432`.
- Los scripts de este paquete son **archivos adicionales**, no reemplazan `compose.yaml`.

## Fase 2: Backup en CotesPC (Ubuntu WSL2)

Abrir Ubuntu en CotesPC. Los scripts están en la copia del repositorio que haya en Ubuntu (clonarla o copiarlos si todavía no existe allí):

```bash
bash database/scripts/01_backup.sh
```

Si NO has puesto los scripts en Ubuntu, puedes ejecutar manualmente desde la carpeta Compose:

```bash
cd ~/gestion-datos-personales/infra/postgres
mkdir -p ~/respaldos-postgres
umask 077
sudo docker compose exec -T db pg_dump -U gestion_admin -d gestion_personas -Fc > ~/respaldos-postgres/gestion_personas_manual.dump
sudo docker compose exec -T db pg_restore -l < ~/respaldos-postgres/gestion_personas_manual.dump > /dev/null
ls -lh ~/respaldos-postgres/gestion_personas_manual.dump
```

**Guardar respaldo cifrado fuera de CotesPC**; no subir a GitHub. El dump incluye datos sensibles.

## Fase 3: Prueba de restauración en BD diferente

```bash
bash database/scripts/02_verificar_restauracion.sh ~/respaldos-postgres/NOMBRE_REAL_DEL_ARCHIVO.dump
```

Si usaste el backup manual, reemplaza `NOMBRE_REAL_DEL_ARCHIVO.dump` por `gestion_personas_manual.dump`.
La base temporal se llama `gestion_personas_restauracion`, **no** `gestion_personas`.
Cuando termines de comprobar resultados y quieras borrar **solo** la base de prueba:

```bash
cd ~/gestion-datos-personales/infra/postgres
sudo docker compose exec -T db dropdb -U gestion_admin gestion_personas_restauracion
```

No hagas esto contra `gestion_personas` ni uses `docker compose down -v`.

## Fase 4: Rol limitado para backend

En DBeaver con usuario administrador `gestion_admin`, abre SQL y ejecuta todo `database/permissions/02_rol_gestion_api.sql`.
Después EN Ubuntu WSL2 de CotesPC:

```bash
cd ~/gestion-datos-personales/infra/postgres
sudo docker compose exec db psql -U gestion_admin -d gestion_personas
```

Dentro de `psql` escribe `\password gestion_api`, ingresa dos veces una contraseña NUEVA y segura; para salir `\q`.
No mostrar ni enviar esa contraseña. Debe guardarse solo en `.env` del backend del PC principal.

Permisos: `persona` SELECT/INSERT/UPDATE/DELETE; `auditoria` únicamente INSERT, sin SELECT/UPDATE/DELETE ni ALTER/CREATE. Para un proyecto final, revisar la separación por microservicios y usar cuentas aún más limitadas (este rol es el primer paso).

## Fase 5: Auditoría de errores y denegaciones

El microservicio `consultar_persona` registra automáticamente cada GET a `/personas/...`:

- HTTP 200 -> `EXITO`
- HTTP 401 o 403 -> `DENEGADO`
- HTTP 404, 422, 500 o 503 -> `ERROR`

Se escribe un evento en `public.auditoria` con la operación `CONSULTAR`, actor `tenant:oid` cuando tiene token validado, o `NO_AUTENTICADO` en otro caso. Los tokens y contraseñas nunca se registran. Este es el comportamiento del **primer microservicio**, no de los seis servicios todavía.

Prueba sin token desde PowerShell PC principal:

```powershell
curl.exe -i "http://127.0.0.1:8000/personas/C%C3%A9dula/1234567890"
```

Debe responder HTTP 401; verificar DENEGADO desde DBeaver:

```sql
SELECT usuario, tipo_operacion, resultado, detalle, fecha_transaccion
FROM public.auditoria
ORDER BY fecha_transaccion DESC
LIMIT 10;
```

La API usa estrategia *fail-closed* si no puede registrar auditoría. Un fallo general de PostgreSQL puede impedir también el registro de errores; para producción se necesitaría una cola o sistema externo fiable.

## Fase 6: FastAPI + Entra ID

### 6.1 Configurar dos registros de aplicación en Microsoft Entra

Acceder a https://entra.microsoft.com, Identidad > Aplicaciones > Registros de aplicaciones.
Requiere acceso autorizado a un tenant y posiblemente consentimiento del administrador.

A. Registrar app **API** (single tenant). Copiar **Directory (tenant) ID** y **Application (client) ID** de la API. En **Expose an API** establecer URI predeterminada `api://<CLIENT_ID_API>` y crear scope delegado **`personas.leer`** habilitado. En Manifest, establecer `requestedAccessTokenVersion: 2` (o `accessTokenAcceptedVersion` según pantalla/manifest), para emitir access tokens v2 a esta API.

B. Registrar app **SPA** (single tenant), plataforma **Single-page application**, redirect URI `http://localhost:5173`. Guardar su Application (client) ID. En API permissions añadir **My APIs > API creada > personas.leer**. Solicitar consentimiento si hace falta.

No se necesitan client secrets en React ni en FastAPI para validar tokens con claves públicas.

### 6.2 Iniciar túnel desde PC principal (PowerShell)

```powershell
ssh -i "$HOME\.ssh\cotespc_ed25519" -N -o ExitOnForwardFailure=yes -L 127.0.0.1:15432:127.0.0.1:5432 cotes@192.168.40.73
```

### 6.3 Iniciar FastAPI (PC principal, otra terminal PowerShell)

```powershell
cd backend/services/consultar_persona
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Editar .env: password gestion_api, tenant GUID, client ID API GUID
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Probar `http://127.0.0.1:8000/salud` y GET sin token HTTP 401. No usar `/docs` como prueba de login; es solo interfaz para consultar la API.

### 6.4 Iniciar frontend React de prueba

En otra terminal:

```powershell
cd frontend/prueba-entra-react
Copy-Item .env.example .env
# Editar .env: tenant GUID, client ID SPA GUID y client ID API GUID
npm install
npm run dev
```

Abrir `http://localhost:5173`, iniciar sesión y consultar la API. `404` si documento no existe, `200` si existe, `401` sin token y `403` si falta permiso. Revisar los eventos en `auditoria`.

### 6.5 Prueba de lectura exitosa (opcional, con persona ficticia)

Se eliminó a Carlos en las pruebas anteriores. Para obtener HTTP 200, primero insertar otra persona ficticia en una transacción con su auditoría. Se incluye `database/scripts/03_semilla_prueba.sql`. Ejecutar UNA sola vez desde DBeaver como administrador; luego consultar el documento `9900000099` desde React.

## Criterios de aceptación
- Backup personalizado creado y archivo verificable.
- Restauración efectuada en la BD de prueba, no en la original.
- Rol gestion_api sin permisos de alterar tablas, borrar auditoría ni administrar PostgreSQL.
- API rechaza peticiones sin token y registra DENEGADO.
- SPA consigue **access token para la API** y GET devuelve 200/404; API verifica firma, emisor, audiencia, expiración y scope.

**Si los IDs de Entra ID aún no se han configurado, la fase 6 queda preparada, pero no validada: no anunciarla como terminada hasta probar un token real.**
