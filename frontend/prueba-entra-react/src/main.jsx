import React from "react";
import { createRoot } from "react-dom/client";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import App from "./App.jsx";

const tenant = import.meta.env.VITE_ENTRA_TENANT_ID;
const spaClient = import.meta.env.VITE_ENTRA_SPA_CLIENT_ID;
if (!tenant || !spaClient) throw new Error("Completa el archivo .env de React");
const msal = new PublicClientApplication({
  auth: {
    clientId: spaClient,
    authority: `https://login.microsoftonline.com/${tenant}`,
    redirectUri: "http://localhost:5173",
  },
  cache: { cacheLocation: "sessionStorage" },
});
await msal.initialize();
createRoot(document.getElementById("root")).render(
  <React.StrictMode><MsalProvider instance={msal}><App /></MsalProvider></React.StrictMode>
);
