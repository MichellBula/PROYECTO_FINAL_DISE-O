import { useState } from "react";
import "./CrearPersona.css";

export default function CrearPersona() {
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState(false);
  const [guardando, setGuardando] = useState(false);

  // Fecha actual en horario local
  const fechaActual = new Date();

  const hoy = [
    fechaActual.getFullYear(),
    String(fechaActual.getMonth() + 1).padStart(2, "0"),
    String(fechaActual.getDate()).padStart(2, "0"),
  ].join("-");

  // ==================================================
  // REGISTRAR PERSONA
  // ==================================================

  async function manejarRegistro(evento) {
    evento.preventDefault();

    const formulario = evento.currentTarget;
    const formData = new FormData(formulario);

    const obtener = (campo) =>
      String(formData.get(campo) ?? "").trim();

    // Obtener los datos del formulario
    const tipoDocumento = obtener("tipo_documento");
    const documento = obtener("numero_documento");
    const primerNombre = obtener("primer_nombre");
    const segundoNombre = obtener("segundo_nombre");
    const apellidos = obtener("apellidos");
    const fecha = obtener("fecha_nacimiento");
    const genero = obtener("genero");
    const correo = obtener("correo");
    const celular = obtener("celular");

    setMensaje("");
    setError(false);

    // ==================================================
    // VALIDACIONES
    // ==================================================

    if (!/^[0-9]{1,10}$/.test(documento)) {
      setError(true);
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      return;
    }

    if (
      !primerNombre ||
      primerNombre.length > 30 ||
      /[0-9]/.test(primerNombre)
    ) {
      setError(true);
      setMensaje(
        "El primer nombre debe tener máximo 30 caracteres y no contener números."
      );
      return;
    }

    if (
      segundoNombre &&
      (segundoNombre.length > 30 || /[0-9]/.test(segundoNombre))
    ) {
      setError(true);
      setMensaje("El segundo nombre no es válido.");
      return;
    }

    if (
      !apellidos ||
      apellidos.length > 60 ||
      /[0-9]/.test(apellidos)
    ) {
      setError(true);
      setMensaje(
        "Los apellidos deben tener máximo 60 caracteres y no contener números."
      );
      return;
    }

    if (!/^[0-9]{10}$/.test(celular)) {
      setError(true);
      setMensaje("El celular debe tener exactamente 10 dígitos.");
      return;
    }

    if (!fecha || fecha > hoy) {
      setError(true);
      setMensaje("Introduce una fecha de nacimiento válida.");
      return;
    }

    // ==================================================
    // PREPARAR DATOS PARA FASTAPI
    // ==================================================

    const datosPersona = {
      tipo_documento: tipoDocumento,
      numero_documento: documento,
      primer_nombre: primerNombre,
      segundo_nombre: segundoNombre || null,
      apellidos: apellidos,
      fecha_nacimiento: fecha,
      genero: genero,
      correo: correo,
      celular: celular,
    };

    // ==================================================
    // ENVIAR DATOS AL MICROSERVICIO
    // ==================================================

    setGuardando(true);

    try {
      const respuesta = await fetch(
        "/api/crear-persona/personas",
        {
          method: "POST",

          // Enviar la sesión del usuario autenticado
          credentials: "include",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(datosPersona),
        }
      );

      const resultado = await respuesta.json().catch(() => null);

      // ==================================================
      // MANEJAR ERRORES DEL BACKEND
      // ==================================================

      if (!respuesta.ok) {
        if (respuesta.status === 401 || respuesta.status === 403) {
          throw new Error(
            "Tu sesión no es válida o ha expirado. Inicia sesión nuevamente."
          );
        }

        if (respuesta.status === 409) {
          throw new Error(
            "Ya existe una persona con ese tipo y número de documento."
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

        if (respuesta.status === 503) {
          throw new Error(
            "El microservicio no pudo completar el registro. Revisa su conexión con PostgreSQL y la auditoría."
          );
        }

        throw new Error(
          typeof resultado?.detail === "string"
            ? resultado.detail
            : `Error al registrar la persona (${respuesta.status}).`
        );
      }

      // ==================================================
      // REGISTRO EXITOSO
      // ==================================================

      setError(false);

      setMensaje(
        "✅ Persona registrada correctamente en PostgreSQL."
      );

      console.log("Persona creada:", resultado);

      // Limpiar el formulario después de guardar
      formulario.reset();

    } catch (error) {
      console.error("Error al crear persona:", error);

      setError(true);

      setMensaje(
        error instanceof Error
          ? error.message
          : "No se pudo conectar con el microservicio."
      );

    } finally {
      setGuardando(false);
    }
  }

  // ==================================================
  // INTERFAZ
  // ==================================================

  return (
    <div className="crear-persona">
      <h3>Registrar nueva persona</h3>

      <p>
        Completa los datos de la persona que deseas registrar.
      </p>

      <form onSubmit={manejarRegistro}>
        <div className="crear-grid">

          <label>
            Tipo de documento *
            <select name="tipo_documento" required>
              <option value="">Selecciona una opción</option>
              <option value="Cédula">Cédula</option>
              <option value="Tarjeta de identidad">
                Tarjeta de identidad
              </option>
            </select>
          </label>

          <label>
            Número de documento *
            <input
              name="numero_documento"
              type="text"
              inputMode="numeric"
              pattern="[0-9]{1,10}"
              maxLength={10}
              required
              placeholder="Ej. 1234567890"
            />
          </label>

          <label>
            Primer nombre *
            <input
              name="primer_nombre"
              type="text"
              required
              maxLength={30}
              placeholder="Primer nombre"
            />
          </label>

          <label>
            Segundo nombre
            <input
              name="segundo_nombre"
              type="text"
              maxLength={30}
              placeholder="Opcional"
            />
          </label>

          <label>
            Apellidos *
            <input
              name="apellidos"
              type="text"
              required
              maxLength={60}
              placeholder="Apellidos"
            />
          </label>

          <label>
            Fecha de nacimiento *
            <input
              name="fecha_nacimiento"
              type="date"
              max={hoy}
              required
            />
          </label>

          <label>
            Género *
            <select name="genero" required>
              <option value="">Selecciona una opción</option>
              <option value="Femenino">Femenino</option>
              <option value="Masculino">Masculino</option>
              <option value="No binario">No binario</option>
              <option value="Prefiero no reportar">
                Prefiero no reportar
              </option>
            </select>
          </label>

          <label>
            Correo electrónico *
            <input
              name="correo"
              type="email"
              required
              maxLength={120}
              placeholder="ejemplo@correo.com"
            />
          </label>

          <label>
            Celular *
            <input
              name="celular"
              type="tel"
              inputMode="numeric"
              pattern="[0-9]{10}"
              maxLength={10}
              required
              placeholder="3001234567"
            />
          </label>

          <label>
            Fotografía (próximamente)
            <input
              name="fotografia"
              type="file"
              accept="image/png,image/jpeg"
              disabled
            />
            <small>
              La carga de fotografías todavía no está disponible.
            </small>
          </label>

        </div>

        <button
          type="submit"
          className="crear-boton"
          disabled={guardando}
        >
          {guardando ? "Guardando persona..." : "Crear persona"}
        </button>

        {mensaje && (
          <p
            className={error ? "crear-error" : "crear-exito"}
            role="status"
          >
            {mensaje}
          </p>
        )}
      </form>
    </div>
  );
}