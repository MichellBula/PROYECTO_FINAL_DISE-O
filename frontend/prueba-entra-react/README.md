# Prueba de integración con Entra ID (NO es el frontend definitivo)

Requiere registrar app SPA en el tenant, con redirect URI EXACTO `http://localhost:5173` tipo SPA.
Requiere app API distinta con scope `personas.leer` y URI `api://<ID_APP_API>`.
Agregar en SPA: API Permissions -> My APIs -> `personas.leer` -> Grant consent si lo exige.

En PowerShell del PC principal:

```powershell
cd frontend/prueba-entra-react
Copy-Item .env.example .env
# Editar .env con tenant, client ID SPA y client ID API
npm install
npm run dev
```

Abrir `http://localhost:5173` (NO 127.0.0.1; coincide con redirect registrado).
El backend debe estar en `http://127.0.0.1:8000` y el túnel SSH de BD activo.

Las variables VITE son públicas por diseño. Solo incluyen IDs, nunca secretos de cliente.
Si Entra exige admin consent, un administrador del tenant deberá aprobar la configuración.
