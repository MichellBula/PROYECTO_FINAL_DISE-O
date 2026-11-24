import { useEffect, useState } from "react";
import {
  cambiarEstadoConsulta,
  obtenerEstadoConsulta,
} from "./serviciosApi.js";
import "./ControlServicios.css";

function mostrarFecha(valor) {
  if (!valor) return "Sin cambios registrados";
  const fecha = new Date(valor);
  return Number.isNaN(fecha.getTime())
    ? "Fecha no disponible"
    : fecha.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}

export default function ControlServicios() {
  const [estado, setEstado] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  async function cargarEstado() {
    setCargando(true);
    setError("");
    setMensaje("");
    try {
      const datos = await obtenerEstadoConsulta();
      setEstado(datos);
    } catch (err) {
      setError(err.message || "No se pudo obtener el estado del servicio.");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    let vigente = true;
    obtenerEstadoConsulta()
      .then((datos) => {
        if (vigente) setEstado(datos);
      })
      .catch((err) => {
        if (vigente) setError(err.message || "No se pudo consultar el estado.");
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });
    return () => {
      vigente = false;
    };
  }, []);

  async function alternarConsulta() {
    if (!estado || guardando) return;

    const nuevoEstado = !estado.habilitado;
    if (
      !nuevoEstado &&
      !window.confirm(
        "¿Deshabilitar el microservicio de consulta? Las búsquedas y fotos de consulta devolverán un error temporal hasta que vuelvas a habilitarlo."
      )
    ) {
      return;
    }

    setGuardando(true);
    setError("");
    setMensaje("");
    try {
      const datos = await cambiarEstadoConsulta(nuevoEstado);
      setEstado(datos);
      setMensaje(
        datos.habilitado
          ? "El microservicio de consulta quedó habilitado."
          : "El microservicio de consulta quedó deshabilitado."
      );
    } catch (err) {
      setError(err.message || "No se pudo guardar el cambio.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section className="control-servicios" aria-labelledby="control-consulta-titulo">
      <div className="control-servicios-cabecera">
        <div>
          <span className="control-servicios-indicador">ADMINISTRACIÓN DE SERVICIOS</span>
          <h3 id="control-consulta-titulo">Microservicio de consulta</h3>
          <p>Controla temporalmente las búsquedas de personas desde el sistema.</p>
        </div>
        <span
          className={`control-servicios-estado ${estado?.habilitado ? "activo" : "inactivo"}`}
          aria-live="polite"
        >
          {cargando ? "Consultando…" : !estado ? "Sin información" : estado.habilitado ? "● Habilitado" : "● Deshabilitado"}
        </span>
      </div>

      <div className="control-servicios-detalle">
        <p>
          {cargando
            ? "Obteniendo el estado actual…"
            : estado?.habilitado
              ? "Las consultas de personas y sus fotografías están disponibles."
              : estado
                ? "Las consultas y fotografías están temporalmente bloqueadas (HTTP 503)."
                : "No es posible determinar si el servicio está disponible."}
        </p>
        {estado && (
          <p className="control-servicios-fecha">
            Último cambio: {mostrarFecha(estado.actualizado_en)}
          </p>
        )}
      </div>

      {error && <p className="control-servicios-error" role="alert">{error}</p>}
      {mensaje && <p className="control-servicios-exito" role="status">{mensaje}</p>}

      <div className="control-servicios-acciones">
        <button
          type="button"
          className={`control-servicios-boton ${estado?.habilitado ? "deshabilitar" : "habilitar"}`}
          onClick={alternarConsulta}
          disabled={cargando || guardando || !estado}
        >
          {guardando
            ? "Guardando cambio…"
            : estado?.habilitado
              ? "Deshabilitar consulta"
              : "Habilitar consulta"}
        </button>
        <button
          type="button"
          className="control-servicios-recargar"
          onClick={cargarEstado}
          disabled={cargando || guardando}
        >
          Actualizar estado
        </button>
      </div>

      <p className="control-servicios-nota">
        Esta opción no detiene el contenedor Docker. Solo bloquea las operaciones de
        consulta; modificar y eliminar personas siguen funcionando por separado.
      </p>
    </section>
  );
}
