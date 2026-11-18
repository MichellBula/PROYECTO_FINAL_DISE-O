
import { useState } from "react";
import "./ModificarPersona.css";

// Datos ficticios para desarrollar la interfaz.
// NO provienen de PostgreSQL.
const personaEjemplo = {
  tipo_documento: "Cédula",
  numero_documento: "1234567890",
  primer_nombre: "Lucía",
  segundo_nombre: "María",
  apellidos: "Ejemplo Prueba",
  fecha_nacimiento: "2000-04-10",
  genero: "Femenino",
  correo: "lucia@example.com",
  celular: "3001234567",
};

export default function ModificarPersona() {
  const [tipoDocumento, setTipoDocumento] = useState("Cédula");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [persona, setPersona] = useState(null);
  const [mensaje, setMensaje] = useState("");
  const [tipoMensaje, setTipoMensaje] = useState("info");

  const hoy = new Date().toISOString().slice(0, 10);

  function buscarPersona(evento) {
    evento.preventDefault();
    setPersona(null);
    setMensaje("");

    if (!/^[0-9]{1,10}$/.test(numeroDocumento)) {
      setTipoMensaje("error");
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      return;
    }

    // Búsqueda simulada mientras no exista la API de modificación.
    if (
      tipoDocumento === personaEjemplo.tipo_documento &&
      numeroDocumento === personaEjemplo.numero_documento
    ) {
      setPersona({ ...personaEjemplo });
      setTipoMensaje("info");
      setMensaje(
        "Persona ficticia encontrada. Puedes editar sus datos."
      );
    } else {
      setTipoMensaje("error");
      setMensaje(
        "No se encontró ese documento en los datos de prueba."
      );
    }
  }

  function actualizarCampo(evento) {
    const { name, value } = evento.target;

    setPersona((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  }

  function validarCambios(evento) {
    evento.preventDefault();

    if (!persona) return;

    if (
      !persona.primer_nombre.trim() ||
      !persona.apellidos.trim()
    ) {
      setTipoMensaje("error");
      setMensaje("El nombre y los apellidos son obligatorios.");
      return;
    }

    if (
      !persona.fecha_nacimiento ||
      persona.fecha_nacimiento > hoy
    ) {
      setTipoMensaje("error");
      setMensaje("La fecha de nacimiento no es válida.");
      return;
    }

    if (!/^[0-9]{10}$/.test(persona.celular)) {
      setTipoMensaje("error");
      setMensaje("El celular debe tener exactamente 10 dígitos.");
      return;
    }

    const archivo = new FormData(
      evento.currentTarget
    ).get("fotografia");

    if (archivo && archivo.size > 0) {
      if (!["image/jpeg", "image/png"].includes(archivo.type)) {
        setTipoMensaje("error");
        setMensaje("La fotografía debe ser JPG o PNG.");
        return;
      }

      if (archivo.size > 2 * 1024 * 1024) {
        setTipoMensaje("error");
        setMensaje("La fotografía no debe superar los 2 MB.");
        return;
      }
    }

    setTipoMensaje("exito");
    setMensaje(
      "✅ Cambios validados correctamente. " +
      "Esta es una simulación: todavía no se guardan en PostgreSQL."
    );
  }

  return (
    <section className="modificar-persona">
      <h3> Modificar persona</h3>
      <p>
        Primero busca una persona por su documento.
        Después podrás editar su información.
      </p>

      <div className="modificar-aviso">
        Modo de prueba: utiliza la cédula 1234567890.
        No se consultan ni modifican datos reales.
      </div>

      {/* BUSCADOR */}
      <form
        className="modificar-buscador"
        onSubmit={buscarPersona}
      >
        <label>
          Tipo de documento
          <select
            value={tipoDocumento}
            onChange={(evento) => {
              setTipoDocumento(evento.target.value);
              setPersona(null);
              setMensaje("");
            }}
          >
            <option value="Cédula">Cédula</option>
            <option value="Tarjeta de identidad">
              Tarjeta de identidad
            </option>
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
              setNumeroDocumento(
                evento.target.value.replace(/\D/g, "")
              );
              setPersona(null);
              setMensaje("");
            }}
            placeholder="Ej. 1234567890"
            required
          />
        </label>

        <button type="submit" className="modificar-boton">
           Buscar persona
        </button>
      </form>

      {/* FORMULARIO DE EDICIÓN */}
      {persona && (
        <form
          className="modificar-formulario"
          onSubmit={validarCambios}
        >
          <h3>Información de la persona</h3>

          <div className="modificar-grid">
            <label>
              Número de documento
              <input
                value={persona.numero_documento}
                disabled
              />
            </label>

            <label>
              Primer nombre *
              <input
                name="primer_nombre"
                value={persona.primer_nombre}
                onChange={actualizarCampo}
                required
                maxLength={60}
              />
            </label>

            <label>
              Segundo nombre
              <input
                name="segundo_nombre"
                value={persona.segundo_nombre}
                onChange={actualizarCampo}
                maxLength={60}
              />
            </label>

            <label>
              Apellidos *
              <input
                name="apellidos"
                value={persona.apellidos}
                onChange={actualizarCampo}
                required
                maxLength={120}
              />
            </label>

            <label>
              Fecha de nacimiento *
              <input
                type="date"
                name="fecha_nacimiento"
                value={persona.fecha_nacimiento}
                onChange={actualizarCampo}
                max={hoy}
                required
              />
            </label>

            <label>
              Género *
              <select
                name="genero"
                value={persona.genero}
                onChange={actualizarCampo}
                required
              >
                <option value="Femenino">Femenino</option>
                <option value="Masculino">Masculino</option>
                <option value="Otro">Otro</option>
              </select>
            </label>

            <label>
              Correo electrónico *
              <input
                type="email"
                name="correo"
                value={persona.correo}
                onChange={actualizarCampo}
                maxLength={120}
                required
              />
            </label>

            <label>
              Celular *
              <input
                type="tel"
                name="celular"
                value={persona.celular}
                onChange={actualizarCampo}
                inputMode="numeric"
                pattern="[0-9]{10}"
                maxLength={10}
                required
              />
            </label>

            <label>
              Nueva fotografía (opcional)
              <input
                type="file"
                name="fotografia"
                accept="image/jpeg,image/png"
              />
            </label>
          </div>

          <button type="submit" className="modificar-boton">
            Validar cambios
          </button>
        </form>
      )}

      {mensaje && (
        <p
          role="status"
          className={`modificar-mensaje ${tipoMensaje}`}
        >
          {mensaje}
        </p>
      )}
    </section>
  );
}
