
import { useEffect, useState } from "react";
import "./FotoPersona.css";

/** Foto actual de una persona, leida por Gateway con la sesion de Roble. */
export default function FotoPersona({ persona, version = 0, tipoDocumento = null }) {
  // En edición se consulta con el tipo persistido, no el valor aún sin guardar.
  const tipo = tipoDocumento ?? persona?.tipo_documento;
  const numero = persona?.numero_documento;
  const [imagen, setImagen] = useState({ estado: "cargando", url: "" });

  useEffect(() => {
    if (!tipo || !numero) {
      setImagen({ estado: "sin-foto", url: "" });
      return;
    }

    const controlador = new AbortController();
    let urlTemporal = null;
    setImagen({ estado: "cargando", url: "" });

    async function cargarFotografia() {
      try {
        const ruta = `/api/personas/${encodeURIComponent(numero)}/fotografia` +
          `?tipo_documento=${encodeURIComponent(tipo)}`;
        const respuesta = await fetch(ruta, {
          method: "GET",
          credentials: "include",
          cache: "no-store",
          signal: controlador.signal,
        });

        if (respuesta.status === 404) {
          if (!controlador.signal.aborted) {
            setImagen({ estado: "sin-foto", url: "" });
          }
          return;
        }
        if (!respuesta.ok) {
          throw new Error(`HTTP ${respuesta.status}`);
        }
        const tipoContenido = respuesta.headers.get("Content-Type") || "";
        if (!tipoContenido.startsWith("image/")) {
          throw new Error("El servidor no devolvió una imagen");
        }

        const archivo = await respuesta.blob();
        if (controlador.signal.aborted) return;
        urlTemporal = URL.createObjectURL(archivo);
        setImagen({ estado: "ok", url: urlTemporal });
      } catch (error) {
        if (!controlador.signal.aborted) {
          console.error("No se pudo consultar la fotografía:", error);
          setImagen({ estado: "error", url: "" });
        }
      }
    }

    cargarFotografia();
    return () => {
      controlador.abort();
      if (urlTemporal) URL.revokeObjectURL(urlTemporal);
    };
  }, [tipo, numero, version]);

  return (
    <section className="foto-persona" aria-label="Fotografía asignada">
      <h4>Fotografía asignada</h4>
      {imagen.estado === "ok" ? (
        <img
          className="foto-persona-imagen"
          src={imagen.url}
          alt="Fotografía asignada a la persona consultada"
          onError={() => setImagen({ estado: "error", url: "" })}
        />
      ) : (
        <div className="foto-persona-vacia" role="status">
          <svg width="54" height="54" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="1.4"
            strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="3" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="m4 17 5-5 4 4 3-3 4 4" />
            <path d="m3 21 18-18" />
          </svg>
          <span>
            {imagen.estado === "cargando"
              ? "Cargando fotografía..."
              : imagen.estado === "error"
                ? "No se pudo cargar la fotografía"
                : "Sin fotografía"}
          </span>
        </div>
      )}
    </section>
  );
}