import React, { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";

const apiId = import.meta.env.VITE_ENTRA_API_CLIENT_ID;
const apiUrl = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const scopes = [`api://${apiId}/personas.leer`];

export default function App() {
  const { instance, accounts } = useMsal();
  const [documento, setDocumento] = useState("9900000099");
  const [tipo, setTipo] = useState("Cédula");
  const [resultado, setResultado] = useState("");
  const cuenta = accounts[0];

  async function iniciar() {
    try {
      await instance.loginPopup({ scopes });
      setResultado("Autenticado. Ya puedes consultar.");
    } catch (err) { setResultado(`No se pudo iniciar sesión: ${err.message}`); }
  }

  async function consultar() {
    if (!cuenta) return setResultado("Primero inicia sesión.");
    try {
      let token;
      try {
        token = (await instance.acquireTokenSilent({ account: cuenta, scopes })).accessToken;
      } catch (err) {
        if (!(err instanceof InteractionRequiredAuthError)) throw err;
        token = (await instance.acquireTokenPopup({ account: cuenta, scopes })).accessToken;
      }
      const url = `${apiUrl}/personas/${encodeURIComponent(tipo)}/${encodeURIComponent(documento)}`;
      const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      const datos = await resp.json();
      setResultado(`HTTP ${resp.status}\n${JSON.stringify(datos, null, 2)}`);
    } catch (err) { setResultado(`Error: ${err.message}`); }
  }

  return <main style={{maxWidth:740,margin:"48px auto",fontFamily:"sans-serif",lineHeight:1.6}}>
    <h1>Prueba Entra ID + FastAPI + PostgreSQL</h1>
    <p>Cuenta: {cuenta?.username ?? "No autenticado"}</p>
    {!cuenta ? <button onClick={iniciar}>Iniciar sesión con Microsoft</button>
      : <button onClick={() => instance.logoutPopup({ account: cuenta })}>Cerrar sesión</button>}
    <p><label>Tipo de documento: <select value={tipo} onChange={e=>setTipo(e.target.value)}>
      <option>Cédula</option><option>Tarjeta de identidad</option>
    </select></label></p>
    <p><label>Número de documento: <input value={documento} onChange={e=>setDocumento(e.target.value)} /></label></p>
    <button onClick={consultar} disabled={!cuenta}>Consultar en FastAPI</button>
    <pre style={{whiteSpace:"pre-wrap",background:"#f4f4f4",padding:16}}>{resultado}</pre>
    <small>Demo local. Nunca muestra ni imprime el token de acceso.</small>
  </main>;
}
