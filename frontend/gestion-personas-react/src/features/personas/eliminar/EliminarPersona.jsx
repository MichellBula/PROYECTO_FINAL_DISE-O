
import { useState } from "react";
import {
  consultarPersona,
  eliminarPersona as eliminarPersonaAPI,
} from "../../../services/api";

import "./EliminarPersona.css";

export default function EliminarPersona() {
  const [tipoDocumento, setTipoDocumento] = useState("Cédula");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [persona, setPersona] = useState(null);
  const [mensaje, setMensaje] = useState("");
  const [tipoMensaje, setTipoMensaje] = useState("info");
  const [cargando, setCargando] = useState(false);

  // 1. BUSCAR PERSONA EN POSTGRESQL
  async function buscarPersona(evento) {
    evento.preventDefault();

    setPersona(null);
    setMensaje("");

    if (!/^[0-9]{1,10}$/.test(numeroDocumento)) {
      setTipoMensaje("error");
      setMensaje("El documento debe tener entre 1 y 10 dígitos.");
      return;
    }

    setCargando(true);

    try {
      const datos = await consultarPersona(
        tipoDocumento,
        numeroDocumento
      );

      const personaEncontrada = datos.persona || datos;

      if (
        personaEncontrada.tipo_documento !== tipoDocumento ||
        String(personaEncontrada.numero_documento) !== numeroDocumento
      ) {
        throw new Error(
          "Los datos encontrados no coinciden con la búsqueda."
        );
      }

      setPersona(personaEncontrada);
      setTipoMensaje("info");
      setMensaje("Persona encontrada correctamente.");

    } catch (error) {
      setTipoMensaje("error");
      setMensaje(error.message || "No se pudo buscar la persona.");
    } finally {
      setCargando(false);
    }
  }

  // 2. ELIMINAR PERSONA DE POSTGRESQL
  async function eliminarPersona() {
    if (!persona || cargando) return;

    const confirmar = window.confirm(
      `¿Estás segura de eliminar a ${persona.primer_nombre} ` +
      `${persona.apellidos}?\n\n` +
      "Esta acción eliminará permanentemente el registro de PostgreSQL."
    );

    if (!confirmar) return;

    setCargando(true);
    setMensaje("");

    try {
      await eliminarPersonaAPI(
        persona.tipo_documento,
        persona.numero_documento
      );

      setPersona(null);
      setNumeroDocumento("");
      setTipoMensaje("exito");
      setMensaje("Persona eliminada correctamente de PostgreSQL.");

    } catch (error) {
      setTipoMensaje("error");
      setMensaje(error.message || "No se pudo eliminar la persona.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="eliminar-persona">
      <h3>Eliminar persona</h3>

      <p>
        Busca una persona mediante su documento y revisa
        sus datos antes de confirmar la eliminación.
      </p>

      <div className="eliminar-aviso">
        La eliminación es permanente. Verifica cuidadosamente
        la información antes de continuar.
      </div>

      <form
        onSubmit={buscarPersona}
        className="eliminar-buscador"
      >
        <label>
          Tipo de documento
          <select
            value={tipoDocumento}
            disabled={cargando}
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
            disabled={cargando}
            onChange={(evento) => {
              setNumeroDocumento(
                evento.target.value.replace(/\D/g, "")
              );
              setPersona(null);
              setMensaje("");
            }}
            placeholder="Ingrese el documento"
            required
          />
        </label>

        <button
          type="submit"
          className="eliminar-buscar"
          disabled={cargando}
        >
          {cargando ? "Procesando..." : "Buscar persona"}
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
              {persona.correo || "No registrado"}
            </p>

            <p>
              <strong>Celular:</strong>{" "}
              {persona.celular || "No registrado"}
            </p>
          </div>

          <div className="eliminar-advertencia">
            Esta acción eliminará permanentemente la persona
            de la base de datos.
          </div>

          <button
            type="button"
            className="eliminar-confirmar"
            onClick={eliminarPersona}
            disabled={cargando}
          >
            {cargando ? "Eliminando..." : "Eliminar persona"}
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
