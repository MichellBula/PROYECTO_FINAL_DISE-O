
import { useState } from "react";
import "./Auditoria.css";

// Registros de ejemplo.
// NO provienen de PostgreSQL.
const registrosEjemplo = [
  {
    id: 1,
    fecha_transaccion: "2026-11-15T09:20:00",
    usuario: "roble:usuario-demo-01",
    tipo_operacion: "CONSULTAR",
    tipo_documento: "Cédula",
    numero_documento: "1234567890",
    resultado: "EXITO",
  },
  {
    id: 2,
    fecha_transaccion: "2026-11-15T10:15:00",
    usuario: "NO_AUTENTICADO",
    tipo_operacion: "CONSULTAR",
    tipo_documento: "Cédula",
    numero_documento: "9999999999",
    resultado: "DENEGADO",
  },
  {
    id: 3,
    fecha_transaccion: "2026-11-15T11:30:00",
    usuario: "roble:usuario-demo-02",
    tipo_operacion: "CREAR",
    tipo_documento: "Tarjeta de identidad",
    numero_documento: "12345678",
    resultado: "EXITO",
  },
  {
    id: 4,
    fecha_transaccion: "2026-11-15T13:45:00",
    usuario: "roble:usuario-demo-01",
    tipo_operacion: "MODIFICAR",
    tipo_documento: "Cédula",
    numero_documento: "1234567890",
    resultado: "EXITO",
  },
  {
    id: 5,
    fecha_transaccion: "2026-11-15T14:10:00",
    usuario: "roble:usuario-demo-01",
    tipo_operacion: "CONSULTAR",
    tipo_documento: "Cédula",
    numero_documento: "9999999999",
    resultado: "ERROR",
  },
];

export default function Auditoria() {
  const [documento, setDocumento] = useState("");
  const [operacion, setOperacion] = useState("");
  const [resultado, setResultado] = useState("");
  const [fecha, setFecha] = useState("");

  const registrosFiltrados = registrosEjemplo.filter((registro) => {
    const coincideDocumento =
      !documento ||
      registro.numero_documento.includes(documento);

    const coincideOperacion =
      !operacion || registro.tipo_operacion === operacion;

    const coincideResultado =
      !resultado || registro.resultado === resultado;

    const coincideFecha =
      !fecha ||
      registro.fecha_transaccion.slice(0, 10) === fecha;

    return (
      coincideDocumento &&
      coincideOperacion &&
      coincideResultado &&
      coincideFecha
    );
  });

  function limpiarFiltros() {
    setDocumento("");
    setOperacion("");
    setResultado("");
    setFecha("");
  }

  return (
    <section className="auditoria">
      <div className="auditoria-encabezado">
        <h3>Historial de auditoría</h3>
        <p>
          Consulta las operaciones registradas en el sistema.
        </p>
      </div>

      <div className="auditoria-aviso">
         Modo demostración: los registros mostrados son
        ficticios y no provienen de PostgreSQL.
      </div>

      {/* FILTROS */}
      <div className="auditoria-filtros">
        <label>
          Número de documento
          <input
            type="text"
            inputMode="numeric"
            placeholder="Buscar documento"
            value={documento}
            onChange={(e) =>
              setDocumento(e.target.value.replace(/\D/g, ""))
            }
            maxLength={10}
          />
        </label>

        <label>
          Operación
          <select
            value={operacion}
            onChange={(e) => setOperacion(e.target.value)}
          >
            <option value="">Todas</option>
            <option value="CREAR">Crear</option>
            <option value="CONSULTAR">Consultar</option>
            <option value="MODIFICAR">Modificar</option>
            <option value="ELIMINAR">Eliminar</option>
          </select>
        </label>

        <label>
          Resultado
          <select
            value={resultado}
            onChange={(e) => setResultado(e.target.value)}
          >
            <option value="">Todos</option>
            <option value="EXITO">Éxito</option>
            <option value="ERROR">Error</option>
            <option value="DENEGADO">Denegado</option>
          </select>
        </label>

        <label>
          Fecha
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
          />
        </label>
      </div>

      <button
        type="button"
        className="auditoria-limpiar"
        onClick={limpiarFiltros}
      >
        Limpiar filtros
      </button>

      {/* TABLA DE AUDITORÍA */}
      <div className="auditoria-tabla-contenedor">
        <table className="auditoria-tabla">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Usuario</th>
              <th>Operación</th>
              <th>Documento</th>
              <th>Resultado</th>
            </tr>
          </thead>

          <tbody>
            {registrosFiltrados.length > 0 ? (
              registrosFiltrados.map((registro) => (
                <tr key={registro.id}>
                  <td>
                    {new Date(
                      registro.fecha_transaccion
                    ).toLocaleString("es-CO")}
                  </td>

                  <td>{registro.usuario}</td>

                  <td>{registro.tipo_operacion}</td>

                  <td>
                    {registro.tipo_documento}
                    <br />
                    {registro.numero_documento}
                  </td>

                  <td>
                    <span
                      className={
                        "auditoria-estado " +
                        registro.resultado.toLowerCase()
                      }
                    >
                      {registro.resultado}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="auditoria-vacio">
                  No se encontraron registros con esos filtros.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="auditoria-total">
        Registros encontrados: {registrosFiltrados.length}
      </p>
    </section>
  );
}
