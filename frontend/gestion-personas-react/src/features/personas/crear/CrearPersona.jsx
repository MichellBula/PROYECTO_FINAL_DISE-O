
import { useState } from "react";
import "./CrearPersona.css";

export default function CrearPersona() {
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState(false);

  const hoy = new Date().toISOString().slice(0, 10);

  function manejarRegistro(evento) {
    evento.preventDefault();

    const formulario = evento.currentTarget;
    const datos = new FormData(formulario);

    const documento = String(datos.get("numero_documento")).trim();
    const celular = String(datos.get("celular")).trim();
    const fecha = String(datos.get("fecha_nacimiento"));
    const fotografia = datos.get("fotografia");

    setMensaje("");
    setError(false);

    if (!/^[0-9]{1,10}$/.test(documento)) {
      setError(true);
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
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

    if (fotografia?.size > 2 * 1024 * 1024) {
      setError(true);
      setMensaje("La fotografía no debe superar los 2 MB.");
      return;
    }

    setMensaje(
      "✅ Formulario validado correctamente. " +
      "Todavía no se han guardado datos en PostgreSQL."
    );
  }

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
              maxLength={60}
              placeholder="Primer nombre"
            />
          </label>

          <label>
            Segundo nombre
            <input
              name="segundo_nombre"
              type="text"
              maxLength={60}
              placeholder="Opcional"
            />
          </label>

          <label>
            Apellidos *
            <input
              name="apellidos"
              type="text"
              required
              maxLength={120}
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
              <option value="Otro">Otro</option>
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
            Fotografía
            <input
              name="fotografia"
              type="file"
              accept="image/png,image/jpeg"
            />
          </label>
        </div>

        <button type="submit" className="crear-boton">
          Validar registro
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
