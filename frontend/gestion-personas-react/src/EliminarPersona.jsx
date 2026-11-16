
import { useState } from "react";
import "./EliminarPersona.css";

// Persona ficticia para las pruebas de la interfaz.
const personaEjemplo = {
  tipo_documento: "Cédula",
  numero_documento: "1234567890",
  primer_nombre: "Lucía",
  segundo_nombre: "María",
  apellidos: "Ejemplo Prueba",
  correo: "lucia@example.com",
  celular: "3001234567",
};

export default function EliminarPersona() {
  const [tipoDocumento, setTipoDocumento] = useState("Cédula");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [persona, setPersona] = useState(null);
  const [eliminada, setEliminada] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [tipoMensaje, setTipoMensaje] = useState("info");

  function buscarPersona(evento) {
    evento.preventDefault();

    setPersona(null);
    setMensaje("");

    if (!/^[0-9]{1,10}$/.test(numeroDocumento)) {
      setTipoMensaje("error");
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      return;
    }

    if (
      !eliminada &&
      tipoDocumento === personaEjemplo.tipo_documento &&
      numeroDocumento === personaEjemplo.numero_documento
    ) {
      setPersona({ ...personaEjemplo });
      setTipoMensaje("info");
      setMensaje("Persona ficticia encontrada.");
    } else {
      setTipoMensaje("error");
      setMensaje("No se encontró la persona en los datos de prueba.");
    }
  }

  function eliminarPersona() {
    if (!persona) return;

    const confirmar = window.confirm(
      `¿Estás segura de eliminar a ${persona.primer_nombre} ` +
      `${persona.apellidos}?\n\n` +
      "Esto es solo una simulación. No se modificará PostgreSQL."
    );

    if (!confirmar) return;

    // Únicamente cambia el estado local de React.
    setPersona(null);
    setEliminada(true);
    setTipoMensaje("exito");
    setMensaje(
      "Simulación completada. La persona fue retirada " +
      "de esta vista, pero NO se eliminó de PostgreSQL."
    );
  }

  return (
    <section className="eliminar-persona">
      <h3>Eliminar persona</h3>

      <p>
        Busca una persona mediante su documento y revisa
        sus datos antes de confirmar la eliminación.
      </p>

      <div className="eliminar-aviso">
         Modo de prueba: utiliza la cédula
        <strong> 1234567890</strong>.
        No se eliminarán datos reales.
      </div>

      <form
        onSubmit={buscarPersona}
        className="eliminar-buscador"
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

        <button type="submit" className="eliminar-buscar">
          Buscar persona
        </button>
      </form>

      {persona && (
        <div className="eliminar-resultado">
          <h4>Información encontrada</h4>

          <div className="eliminar-datos">
            <p>
              <strong>Tipo de documento:</strong>{" "}
              {persona.tipo_documento}
            </p>

            <p>
              <strong>Número:</strong>{" "}
              {persona.numero_documento}
            </p>

            <p>
              <strong>Nombres:</strong>{" "}
              {persona.primer_nombre}{" "}
              {persona.segundo_nombre}
            </p>

            <p>
              <strong>Apellidos:</strong>{" "}
              {persona.apellidos}
            </p>

            <p>
              <strong>Correo:</strong>{" "}
              {persona.correo}
            </p>

            <p>
              <strong>Celular:</strong>{" "}
              {persona.celular}
            </p>
          </div>

          <div className="eliminar-advertencia">
            ⚠️ Revisa cuidadosamente la información
            antes de continuar.
          </div>

          <button
            type="button"
            className="eliminar-confirmar"
            onClick={eliminarPersona}
          >
            Solicitar eliminación
          </button>
        </div>
      )}

      {mensaje && (
        <p
          role="status"
          className={`eliminar-mensaje ${tipoMensaje}`}
        >
          {mensaje}
        </p>
      )}
    </section>
  );
}
