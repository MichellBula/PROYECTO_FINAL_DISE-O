
import { useEffect, useRef, useState } from "react";
import "./CrearPersona.css";
import "./CrearPersonaFoto.css";

export default function CrearPersona() {
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [fotografia, setFotografia] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState("");
  const fotografiaInputRef = useRef(null);

  useEffect(() => {
    if (!fotografia) {
      setVistaPrevia("");
      return;
    }
    const url = URL.createObjectURL(fotografia);
    setVistaPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [fotografia]);

  function seleccionarFotografia(evento) {
    const archivo = evento.target.files?.[0] ?? null;
    setMensaje("");
    setError(false);

    if (!archivo) {
      setFotografia(null);
      return;
    }
    if (!["image/jpeg", "image/png"].includes(archivo.type)) {
      evento.target.value = "";
      setFotografia(null);
      setError(true);
      setMensaje("La fotografía debe ser JPG o PNG.");
      return;
    }
    if (archivo.size === 0 || archivo.size > 2 * 1024 * 1024) {
      evento.target.value = "";
      setFotografia(null);
      setError(true);
      setMensaje("La fotografía no debe estar vacía ni superar los 2 MB.");
      return;
    }
    setFotografia(archivo);
  }

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

    if (
      !["Cédula", "Tarjeta de identidad"].includes(tipoDocumento)
    ) {
      setError(true);
      setMensaje("Selecciona un tipo de documento válido.");
      return;
    }

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

    if (
      ![
        "Femenino",
        "Masculino",
        "No binario",
        "Prefiero no reportar",
      ].includes(genero)
    ) {
      setError(true);
      setMensaje("Selecciona un género válido.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
      setError(true);
      setMensaje("Introduce un correo electrónico válido.");
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
    // ENVIAR DATOS A LA API GATEWAY
    // ==================================================

    setGuardando(true);

    try {
      // 1. Obtener la sesión actual y su token CSRF.
      const respuestaSesion = await fetch("/api/auth/yo", {
        method: "GET",
        credentials: "include",
      });

      if (!respuestaSesion.ok) {
        throw new Error(
          "Tu sesión no es válida o ha expirado. Inicia sesión nuevamente."
        );
      }

      const datosSesion = await respuestaSesion.json();

      if (!datosSesion.csrf_token) {
        throw new Error(
          "No se pudo obtener el token de seguridad de la sesión."
        );
      }

      // 2. Con foto enviamos multipart; sin foto mantenemos JSON.
      // Nunca configurar Content-Type manualmente con FormData.
      let cuerpo;
      const encabezados = { "X-CSRF-Token": datosSesion.csrf_token };
      if (fotografia) {
        const datosConFoto = new FormData();
        Object.entries(datosPersona).forEach(([clave, valor]) => {
          datosConFoto.append(clave, valor ?? "");
        });
        datosConFoto.append("fotografia", fotografia);
        cuerpo = datosConFoto;
      } else {
        encabezados["Content-Type"] = "application/json";
        cuerpo = JSON.stringify(datosPersona);
      }

      const respuesta = await fetch("/api/personas", {
        method: "POST",
        credentials: "include",
        headers: encabezados,
        body: cuerpo,
      });

      const resultado = await respuesta
        .json()
        .catch(() => null);

      // ==================================================
      // MANEJAR ERRORES DEL BACKEND
      // ==================================================

      if (!respuesta.ok) {
        if (respuesta.status === 401) {
          throw new Error(
            "Tu sesión ha expirado. Inicia sesión nuevamente."
          );
        }

        if (respuesta.status === 403) {
          throw new Error(
            "La operación fue rechazada por seguridad. Verifica tu sesión y tus permisos."
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
            "El servicio no está disponible temporalmente. Comprueba la conexión con el servidor."
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

      formulario.reset();
      setFotografia(null);

    } catch (error) {
      console.error("Error al crear persona:", error);

      setError(true);

      setMensaje(
        error instanceof Error
          ? error.message
          : "No se pudo conectar con la API Gateway."
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

          <label className="crear-foto">
            Fotografía (opcional)
            <input
              name="fotografia"
              ref={fotografiaInputRef}
              type="file"
              accept="image/png,image/jpeg"
              onChange={seleccionarFotografia}
              disabled={guardando}
            />
            <small>JPG o PNG, máximo 2 MB.</small>
            {vistaPrevia && (
              <span className="crear-foto-vista">
                <img src={vistaPrevia} alt="Vista previa de fotografía seleccionada" />
                <button
                  type="button"
                  onClick={() => {
                    if (fotografiaInputRef.current) {
                      fotografiaInputRef.current.value = "";
                    }
                    setFotografia(null);
                  }}
                  disabled={guardando}
                >
                  Quitar selección
                </button>
              </span>
            )}
          </label>

        </div>

        <button
          type="submit"
          className="crear-boton"
          disabled={guardando}
        >
          {guardando
            ? "Guardando persona..."
            : "Crear persona"}
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