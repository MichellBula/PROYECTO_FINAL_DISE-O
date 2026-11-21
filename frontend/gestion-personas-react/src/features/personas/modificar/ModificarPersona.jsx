import { useState } from "react";
import "./ModificarPersona.css";

export default function ModificarPersona() {
  const [tipoDocumento, setTipoDocumento] = useState("Cédula");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [persona, setPersona] = useState(null);
  
  // Guarda el tipo de documento original para armar la URL del PUT
  const [tipoDocOriginal, setTipoDocOriginal] = useState(""); 
  
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState(false);
  const [cargando, setCargando] = useState(false);

  // Fecha actual en horario local (igual que en CrearPersona)
  const fechaActual = new Date();
  const hoy = [
    fechaActual.getFullYear(),
    String(fechaActual.getMonth() + 1).padStart(2, "0"),
    String(fechaActual.getDate()).padStart(2, "0"),
  ].join("-");

  // ==================================================
  // 1. BUSCAR PERSONA
  // ==================================================
  async function buscarPersona(evento) {
    evento.preventDefault();
    setPersona(null);
    setMensaje("");
    setError(false);
    setCargando(true);

    if (!/^[0-9]{1,10}$/.test(numeroDocumento)) {
      setError(true);
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      setCargando(false);
      return;
    }

    try {
      const tipoParam = encodeURIComponent(tipoDocumento); 
      const respuesta = await fetch(`/api/personas/${tipoParam}/${numeroDocumento}`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const resultado = await respuesta.json().catch(() => null);

      if (!respuesta.ok) {
        if (respuesta.status === 404) {
          throw new Error("No se encontró ninguna persona con ese documento.");
        }
        throw new Error(
          typeof resultado?.detail === "string"
            ? resultado.detail
            : `Error al buscar la persona (${respuesta.status}).`
        );
      }

      // Si la respuesta es exitosa, llenamos el formulario
      const personaEncontrada = resultado?.persona ?? resultado;

      if (
        !personaEncontrada?.tipo_documento ||
        !personaEncontrada?.numero_documento
      ) {
        throw new Error(
          "El microservicio de consulta devolvió datos incompletos."
        );
      }

      setPersona(personaEncontrada);

      setTipoDocOriginal(personaEncontrada.tipo_documento);

      setNumeroDocumento(
        String(personaEncontrada.numero_documento)
      );
      
      setMensaje("Persona encontrada. Puedes editar sus datos.");

    } catch (error) {
      console.error("Error al buscar persona:", error);
      setError(true);
      setMensaje(
        error instanceof Error ? error.message : "No se pudo conectar con el microservicio de consulta."
      );
    } finally {
      setCargando(false);
    }
  }

  function actualizarCampo(evento) {
    const { name, value } = evento.target;
    setPersona((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  }

  // ==================================================
  // 2. GUARDAR CAMBIOS
  // ==================================================
  async function manejarModificacion(evento) {
    evento.preventDefault();
    if (!persona) return;

    const formulario = evento.currentTarget;
    const formData = new FormData(formulario);

    const obtener = (campo) => String(formData.get(campo) ?? "").trim();

    // Obtener datos del formulario
    const nuevoTipo = obtener("tipo_documento");
    const primerNombre = obtener("primer_nombre");
    const segundoNombre = obtener("segundo_nombre");
    const apellidos = obtener("apellidos");
    const fecha = obtener("fecha_nacimiento");
    const genero = obtener("genero");
    const correo = obtener("correo");
    const celular = obtener("celular");
    const foto = formData.get("fotografia");

    setMensaje("");
    setError(false);

    // Validaciones
    if (!primerNombre || primerNombre.length > 30 || /[0-9]/.test(primerNombre)) {
      setError(true);
      setMensaje("El primer nombre no es válido.");
      return;
    }

    if (apellidos.length > 60 || /[0-9]/.test(apellidos) || !apellidos) {
      setError(true);
      setMensaje("Los apellidos no son válidos.");
      return;
    }

    if (!/^[0-9]{10}$/.test(celular)) {
      setError(true);
      setMensaje("El celular debe tener exactamente 10 dígitos.");
      return;
    }

    if (foto && foto.size > 0) {
      if (!["image/jpeg", "image/png"].includes(foto.type)) {
        setError(true);
        setMensaje("La fotografía debe ser JPG o PNG.");
        return;
      }
      if (foto.size > 2 * 1024 * 1024) {
        setError(true);
        setMensaje("La fotografía no debe superar los 2 MB.");
        return;
      }
    }

    // Preparamos el FormData para enviar (FastAPI requiere FormData por la foto)
    const datosEnvio = new FormData();
    datosEnvio.append("tipo_documento", nuevoTipo);
    datosEnvio.append("primer_nombre", primerNombre);
    datosEnvio.append("segundo_nombre", segundoNombre || "");
    datosEnvio.append("apellidos", apellidos);
    datosEnvio.append("fecha_nacimiento", fecha);
    datosEnvio.append("genero", genero);
    datosEnvio.append("correo", correo);
    datosEnvio.append("celular", celular);

    // Adjuntar la foto solo si el usuario seleccionó una nueva
    if (foto && foto.size > 0) {
      datosEnvio.append("foto", foto);
    }

    setCargando(true);

    try {
      // 👇 AGREGA ESTOS CONSOLE.LOG AQUÍ 👇
      console.log("=== DATOS PARA GUARDAR ===");
      console.log("Tipo Original:", tipoDocOriginal);
      console.log("Número Documento:", numeroDocumento);
      console.log("Nuevo Tipo:", nuevoTipo);


      // Codificamos el tipo original para que los espacios y tildes viajen seguros en la URL
      const tipoOriginalParam = encodeURIComponent(tipoDocOriginal);
      const url = `/api/modificar-persona/personas/${tipoOriginalParam}/${numeroDocumento}`;

      console.log("URL final a enviar:", url);

      const respuesta = await fetch(url, {
        method: "PUT",
        credentials: "include",
        // NO agregamos headers de Content-Type, el navegador lo hace solo al usar FormData
        body: datosEnvio,
      });

      const resultado = await respuesta.json().catch(() => null);

      // Manejar errores de FastAPI
      if (!respuesta.ok) {
        if (respuesta.status === 401 || respuesta.status === 403) {
          throw new Error("Tu sesión no es válida o ha expirado. Inicia sesión nuevamente.");
        }
        if (respuesta.status === 404) {
          throw new Error(
              `Error HTTP 404: ${
                typeof resultado?.detail === "string"
                  ? resultado.detail
                  : "No se encontró la ruta o el registro solicitado."
              }`
            );        
          }
        if (respuesta.status === 422) {
          const detalle = resultado?.detail;
          const descripcion = Array.isArray(detalle)
            ? detalle.map((item) => item.msg).join(". ")
            : typeof detalle === "string"
              ? detalle
              : "Los datos no cumplen las validaciones del servidor.";
          throw new Error(descripcion);
        }
        throw new Error(
          typeof resultado?.detail === "string"
            ? resultado.detail
            : `Error al modificar la persona (${respuesta.status}).`
        );
      }

      // MODIFICACIÓN EXITOSA
      setError(false);
      setMensaje("Persona modificada correctamente en PostgreSQL.");
      
      // Actualizamos el tipo original por si vuelve a guardar en la misma sesión
      setTipoDocOriginal(nuevoTipo);

    } catch (error) {
      console.error("Error al modificar persona:", error);
      setError(true);
      setMensaje(
        error instanceof Error ? error.message : "No se pudo conectar con el microservicio."
      );
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="modificar-persona">
      <h3>Modificar persona</h3>
      <p>
        Primero busca una persona por su documento. Después podrás editar su información.
      </p>

      {/* BUSCADOR */}
      <form className="modificar-buscador" onSubmit={buscarPersona}>
        <div className="modificar-grid">
          <label>
            Tipo de documento (Búsqueda)
            <select
              value={tipoDocumento}
              onChange={(evento) => {
                setTipoDocumento(evento.target.value);
                setPersona(null);
                setMensaje("");
              }}
            >
              <option value="Cédula">Cédula</option>
              <option value="Tarjeta de identidad">Tarjeta de identidad</option>
            </select>
          </label>

          <label>
            Número de documento
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]{1,10}"
              maxLength={10}
              value={numeroDocumento}
              onChange={(evento) => {
                setNumeroDocumento(evento.target.value.replace(/\D/g, ""));
                setPersona(null);
                setMensaje("");
              }}
              placeholder="Ej. 1234567890"
              required
            />
          </label>
        </div>

        <button type="submit" className="modificar-boton" disabled={cargando}>
          {cargando && !persona ? "Buscando..." : "Buscar persona"}
        </button>
      </form>

      {/* FORMULARIO DE EDICIÓN */}
      {persona && (
        <form onSubmit={manejarModificacion}>
          <h3>Información de la persona</h3>

          <div className="modificar-grid">
            <label>
              Número de documento
              <input value={persona.numero_documento} disabled />
            </label>

            {/* Selector para cambiar de T.I a Cédula */}
            <label>
              Tipo de documento *
              <select
                name="tipo_documento"
                value={persona.tipo_documento || "Cédula"}
                onChange={actualizarCampo}
                required
              >
                <option value="Cédula">Cédula</option>
                <option value="Tarjeta de identidad">Tarjeta de identidad</option>
              </select>
            </label>

            <label>
              Primer nombre *
              <input name="primer_nombre" value={persona.primer_nombre || ""} onChange={actualizarCampo} required maxLength={30} />
            </label>

            <label>
              Segundo nombre
              <input name="segundo_nombre" value={persona.segundo_nombre || ""} onChange={actualizarCampo} maxLength={30} />
            </label>

            <label>
              Apellidos *
              <input name="apellidos" value={persona.apellidos || ""} onChange={actualizarCampo} required maxLength={60} />
            </label>

            <label>
              Fecha de nacimiento *
              <input type="date" name="fecha_nacimiento" value={persona.fecha_nacimiento || ""} onChange={actualizarCampo} max={hoy} required />
            </label>

            <label>
              Género *
              <select name="genero" value={persona.genero || ""} onChange={actualizarCampo} required>
                <option value="Femenino">Femenino</option>
                <option value="Masculino">Masculino</option>
                <option value="No binario">No binario</option>
                <option value="Prefiero no reportar">Prefiero no reportar</option>
              </select>
            </label>

            <label>
              Correo electrónico *
              <input type="email" name="correo" value={persona.correo || ""} onChange={actualizarCampo} maxLength={120} required />
            </label>

            <label>
              Celular *
              <input type="tel" name="celular" value={persona.celular || ""} onChange={actualizarCampo} inputMode="numeric" pattern="[0-9]{10}" maxLength={10} required />
            </label>

            <label>
              Nueva fotografía (opcional)
              <input type="file" name="fotografia" accept="image/jpeg,image/png" />
            </label>
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