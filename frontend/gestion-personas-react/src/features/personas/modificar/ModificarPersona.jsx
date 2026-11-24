
import { useEffect, useRef, useState } from "react";
import "./ModificarPersona.css";
import FotoPersona from "../../../components/FotoPersona.jsx";

const LIMITE_FOTO = 2 * 1024 * 1024;

export default function ModificarPersona() {
  const [tipoDocumento, setTipoDocumento] = useState("Cédula");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [persona, setPersona] = useState(null);
  const [versionFoto, setVersionFoto] = useState(0);
  const [tipoDocOriginal, setTipoDocOriginal] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [accionFoto, setAccionFoto] = useState("conservar");
  const [fotoNueva, setFotoNueva] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState("");
  const inputFoto = useRef(null);

  const fechaActual = new Date();
  const hoy = [
    fechaActual.getFullYear(),
    String(fechaActual.getMonth() + 1).padStart(2, "0"),
    String(fechaActual.getDate()).padStart(2, "0"),
  ].join("-");

  useEffect(() => {
    if (!fotoNueva) {
      setVistaPrevia("");
      return;
    }
    const url = URL.createObjectURL(fotoNueva);
    setVistaPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [fotoNueva]);

  function reiniciarFoto() {
    setAccionFoto("conservar");
    setFotoNueva(null);
    if (inputFoto.current) inputFoto.current.value = "";
  }

  function cambiarFoto(evento) {
    const archivo = evento.target.files?.[0] ?? null;
    if (!archivo) return;
    setMensaje("");
    setError(false);

    if (!["image/jpeg", "image/png"].includes(archivo.type)) {
      setError(true);
      setMensaje("Selecciona una fotografía JPG o PNG.");
      reiniciarFoto();
      return;
    }
    if (archivo.size === 0 || archivo.size > LIMITE_FOTO) {
      setError(true);
      setMensaje("La fotografía no puede estar vacía ni superar 2 MB.");
      reiniciarFoto();
      return;
    }

    setFotoNueva(archivo);
    setAccionFoto("reemplazar");
  }

  async function buscarPersona(evento) {
    evento.preventDefault();
    setPersona(null);
    setMensaje("");
    setError(false);
    reiniciarFoto();

    if (!/^[0-9]{1,10}$/.test(numeroDocumento)) {
      setError(true);
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      return;
    }

    setCargando(true);
    try {
      // Se conserva el contrato actual de la API Gateway:
      // GET /api/personas/{numero}?tipo_documento={tipo}
      const numero = encodeURIComponent(numeroDocumento);
      const tipo = encodeURIComponent(tipoDocumento);
      const respuesta = await fetch(
        `/api/personas/${numero}?tipo_documento=${tipo}`,
        { credentials: "include" }
      );
      const resultado = await respuesta.json().catch(() => null);
      if (!respuesta.ok) {
        throw new Error(
          respuesta.status === 404
            ? "No se encontró una persona con ese documento."
            : typeof resultado?.detail === "string"
              ? resultado.detail
              : `Error en la búsqueda (${respuesta.status}).`
        );
      }

      const encontrada = resultado?.persona ?? resultado;
      if (!encontrada?.tipo_documento || !encontrada?.numero_documento) {
        throw new Error("El servicio devolvió datos incompletos de la persona.");
      }
      setPersona(encontrada);
      setTipoDocOriginal(encontrada.tipo_documento);
      setNumeroDocumento(String(encontrada.numero_documento));
      setMensaje("Persona encontrada. Puedes editar sus datos y su fotografía.");
    } catch (err) {
      setError(true);
      setMensaje(err instanceof Error ? err.message : "No se pudo consultar la persona.");
    } finally {
      setCargando(false);
    }
  }

  function actualizarCampo(evento) {
    const { name, value } = evento.target;
    setPersona((anterior) => ({ ...anterior, [name]: value }));
  }

  async function manejarModificacion(evento) {
    evento.preventDefault();
    if (!persona || cargando) return;

    const formulario = evento.currentTarget;
    const campos = new FormData(formulario);
    const obtener = (nombre) => String(campos.get(nombre) ?? "").trim();
    const nuevoTipo = obtener("tipo_documento");
    const primerNombre = obtener("primer_nombre");
    const apellidos = obtener("apellidos");
    const celular = obtener("celular");

    setMensaje("");
    setError(false);

    if (!primerNombre || primerNombre.length > 30 || /\d/.test(primerNombre)) {
      setError(true);
      setMensaje("El primer nombre no es válido.");
      return;
    }
    if (!apellidos || apellidos.length > 60 || /\d/.test(apellidos)) {
      setError(true);
      setMensaje("Los apellidos no son válidos.");
      return;
    }
    if (!/^[0-9]{10}$/.test(celular)) {
      setError(true);
      setMensaje("El celular debe tener exactamente 10 dígitos.");
      return;
    }
    if (accionFoto === "reemplazar" && !fotoNueva) {
      setError(true);
      setMensaje("Selecciona una fotografía nueva.");
      return;
    }

    const datosEnvio = new FormData();
    for (const nombre of [
      "tipo_documento", "primer_nombre", "segundo_nombre", "apellidos",
      "fecha_nacimiento", "genero", "correo", "celular",
    ]) {
      datosEnvio.append(nombre, obtener(nombre));
    }
    datosEnvio.append("accion_foto", accionFoto);
    if (accionFoto === "reemplazar") {
      datosEnvio.append("foto", fotoNueva);
    }

    setCargando(true);
    try {
      // El proyecto ya usa sesión Roble + CSRF para operaciones de escritura.
      const respuestaSesion = await fetch("/api/auth/yo", {
        credentials: "include",
      });
      if (!respuestaSesion.ok) {
        throw new Error("Tu sesión ha expirado. Inicia sesión nuevamente.");
      }
      const sesion = await respuestaSesion.json();
      if (!sesion.csrf_token) {
        throw new Error("No se pudo obtener el token CSRF de la sesión.");
      }

      // La Gateway recibe tipo original como parámetro de consulta.
      const numero = encodeURIComponent(numeroDocumento);
      const tipoOriginal = encodeURIComponent(tipoDocOriginal);
      const url = `/api/personas/${numero}?tipo_documento=${tipoOriginal}`;
      const respuesta = await fetch(url, {
        method: "PUT",
        credentials: "include",
        headers: { "X-CSRF-Token": sesion.csrf_token },
        // No incluir Content-Type: el navegador añade boundary de multipart.
        body: datosEnvio,
      });
      const resultado = await respuesta.json().catch(() => null);
      if (!respuesta.ok) {
        if (respuesta.status === 401) throw new Error("Tu sesión ha expirado.");
        if (respuesta.status === 403) throw new Error("No tienes permisos para modificar personas.");
        if (respuesta.status === 409) throw new Error("Ya existe otra persona con ese documento.");
        if (respuesta.status === 404) {
          throw new Error(`HTTP 404: ${resultado?.detail ?? "Ruta o persona no encontrada"}`);
        }
        const detalle = resultado?.detail;
        throw new Error(
          Array.isArray(detalle)
            ? detalle.map((item) => item.msg).join(". ")
            : typeof detalle === "string"
              ? detalle
              : `Error al guardar (HTTP ${respuesta.status}).`
        );
      }

      const actualizada = resultado?.persona;
      if (actualizada) setPersona(actualizada);
      else if (accionFoto === "quitar") {
        setPersona((anterior) => ({ ...anterior, foto_ruta: null }));
      }
      setTipoDocOriginal(actualizada?.tipo_documento ?? nuevoTipo);
      setTipoDocumento(actualizada?.tipo_documento ?? nuevoTipo);
      reiniciarFoto();
      setVersionFoto((version) => version + 1);
      setError(false);
      setMensaje("Persona modificada correctamente en PostgreSQL.");
    } catch (err) {
      setError(true);
      setMensaje(err instanceof Error ? err.message : "No se pudo guardar la modificación.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="modificar-persona">
      <h3>Modificar persona</h3>
      <p>Busca una persona, edita su información y decide qué hacer con su fotografía.</p>

      <form className="modificar-buscador" onSubmit={buscarPersona}>
        <div className="modificar-grid">
          <label>
            Tipo de documento (búsqueda)
            <select value={tipoDocumento} onChange={(e) => {
              setTipoDocumento(e.target.value);
              setPersona(null);
              reiniciarFoto();
            }}>
              <option value="Cédula">Cédula</option>
              <option value="Tarjeta de identidad">Tarjeta de identidad</option>
            </select>
          </label>
          <label>
            Número de documento
            <input type="text" inputMode="numeric" pattern="[0-9]{1,10}"
              maxLength={10} value={numeroDocumento} required
              onChange={(e) => {
                setNumeroDocumento(e.target.value.replace(/\D/g, ""));
                setPersona(null);
                reiniciarFoto();
              }}
              placeholder="Ej. 1234567890" />
          </label>
        </div>
        <button type="submit" className="modificar-boton" disabled={cargando}>
          {cargando && !persona ? "Buscando..." : "Buscar persona"}
        </button>
      </form>

      {persona && (
        <form onSubmit={manejarModificacion}>
          <h3>Información de la persona</h3>
          <div className="modificar-grid">
            <label>Número de documento
              <input value={persona.numero_documento || ""} readOnly />
            </label>
            <label>Tipo de documento *
              <select name="tipo_documento" value={persona.tipo_documento || "Cédula"}
                onChange={actualizarCampo} required>
                <option value="Cédula">Cédula</option>
                <option value="Tarjeta de identidad">Tarjeta de identidad</option>
              </select>
            </label>
            <label>Primer nombre *
              <input name="primer_nombre" value={persona.primer_nombre || ""}
                onChange={actualizarCampo} required maxLength={30} />
            </label>
            <label>Segundo nombre
              <input name="segundo_nombre" value={persona.segundo_nombre || ""}
                onChange={actualizarCampo} maxLength={30} />
            </label>
            <label>Apellidos *
              <input name="apellidos" value={persona.apellidos || ""}
                onChange={actualizarCampo} required maxLength={60} />
            </label>
            <label>Fecha de nacimiento *
              <input type="date" name="fecha_nacimiento"
                value={String(persona.fecha_nacimiento || "").slice(0, 10)}
                onChange={actualizarCampo} max={hoy} required />
            </label>
            <label>Género *
              <select name="genero" value={persona.genero || ""}
                onChange={actualizarCampo} required>
                <option value="Femenino">Femenino</option>
                <option value="Masculino">Masculino</option>
                <option value="No binario">No binario</option>
                <option value="Prefiero no reportar">Prefiero no reportar</option>
              </select>
            </label>
            <label>Correo electrónico *
              <input type="email" name="correo" value={persona.correo || ""}
                onChange={actualizarCampo} required maxLength={120} />
            </label>
            <label>Celular *
              <input type="tel" name="celular" value={persona.celular || ""}
                onChange={actualizarCampo} inputMode="numeric" pattern="[0-9]{10}"
                maxLength={10} required />
            </label>
          </div>

          <div className="modificar-foto-panel">
            <h4>Fotografía de la persona</h4>
            <FotoPersona
              persona={persona}
              tipoDocumento={tipoDocOriginal}
              version={versionFoto}
            />

            <label>Nueva fotografía (opcional)
              <input ref={inputFoto} type="file" name="fotografia"
                accept="image/jpeg,image/png" onChange={cambiarFoto} disabled={cargando} />
              <small>JPG o PNG, máximo 2 MB.</small>
            </label>
            {vistaPrevia && accionFoto === "reemplazar" && (
              <div className="modificar-foto-vista">
                <img src={vistaPrevia} alt="Vista previa de la nueva fotografía" />
                <span>Se reemplazará la fotografía al guardar los cambios.</span>
              </div>
            )}
            {accionFoto === "quitar" && (
              <p className="modificar-foto-alerta">
                Al guardar se quitará la fotografía asociada a esta persona.
              </p>
            )}
            <div className="modificar-foto-acciones">
              <button type="button" onClick={reiniciarFoto} disabled={cargando}>
                Conservar fotografía
              </button>
              <button type="button" onClick={() => {
                setAccionFoto("quitar");
                setFotoNueva(null);
                if (inputFoto.current) inputFoto.current.value = "";
              }} disabled={cargando}>
                Quitar fotografía
              </button>
            </div>
            <p className="modificar-foto-accion">
              Acción seleccionada: <strong>{accionFoto}</strong>
            </p>
          </div>

          <button type="submit" className="modificar-boton" disabled={cargando}>
            {cargando ? "Guardando cambios..." : "Guardar cambios"}
          </button>
        </form>
      )}
      {mensaje && (
        <p className={error ? "modificar-error" : "modificar-exito"} role="status">
          {mensaje}
        </p>
      )}
    </div>
  );
}