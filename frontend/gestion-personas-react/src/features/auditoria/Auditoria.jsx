import { useEffect, useState } from "react";
import "./Auditoria.css";

// ==============================================
// CONFIGURACIÓN
// ==============================================

const LIMITE_POR_PAGINA = 20;

const filtrosVacios = {
  documento: "",
  operacion: "",
  resultado: "",
  fecha: "",
  pagina: 1,
};

// ==============================================
// COMPONENTE PRINCIPAL
// ==============================================

export default function Auditoria() {

  // ============================================
  // ESTADOS DE LOS FILTROS
  // ============================================

  const [documento, setDocumento] = useState("");
  const [operacion, setOperacion] = useState("");
  const [resultado, setResultado] = useState("");
  const [fecha, setFecha] = useState("");

  // ============================================
  // ESTADOS DE LA CONSULTA
  // ============================================

  const [filtrosAplicados, setFiltrosAplicados] =
    useState({ ...filtrosVacios });

  const [registros, setRegistros] = useState([]);
  const [total, setTotal] = useState(0);

  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  // ============================================
  // CONSULTAR AUDITORÍA DESDE POSTGRESQL
  // ============================================

  useEffect(() => {

    const controlador = new AbortController();

    async function cargarAuditoria() {

      setCargando(true);
      setError("");

      try {

        // Construir los parámetros de la consulta
        const parametros = new URLSearchParams({
          pagina: String(filtrosAplicados.pagina),
          limite: String(LIMITE_POR_PAGINA),
        });

        // Filtro por documento
        if (filtrosAplicados.documento) {
          parametros.set(
            "numero_documento",
            filtrosAplicados.documento
          );
        }

        // Filtro por operación
        if (filtrosAplicados.operacion) {
          parametros.set(
            "tipo_operacion",
            filtrosAplicados.operacion
          );
        }

        // Filtro por resultado
        if (filtrosAplicados.resultado) {
          parametros.set(
            "resultado",
            filtrosAplicados.resultado
          );
        }

        // Filtro por fecha
        if (filtrosAplicados.fecha) {

          parametros.set(
            "fecha_desde",
            filtrosAplicados.fecha
          );

          parametros.set(
            "fecha_hasta",
            filtrosAplicados.fecha
          );
        }

        // Solicitud al microservicio de auditoría
        const respuesta = await fetch(
          `/api/auditoria?${parametros.toString()}`,
          {
            method: "GET",
            credentials: "include",
            signal: controlador.signal,
          }
        );

        const datos = await respuesta.json().catch(
          () => null
        );

        // ======================================
        // MANEJO DE ERRORES HTTP
        // ======================================

        if (!respuesta.ok) {

          if (respuesta.status === 401) {
            throw new Error(
              "Tu sesión ha expirado. Inicia sesión nuevamente."
            );
          }

          if (respuesta.status === 403) {
            throw new Error(
              "No tienes permisos para consultar la auditoría."
            );
          }

          if (respuesta.status === 422) {
            throw new Error(
              "Los filtros enviados no son válidos."
            );
          }

          throw new Error(
            datos?.detail ||
            `Error al consultar auditoría (HTTP ${respuesta.status}).`
          );
        }

        // ======================================
        // VALIDAR RESPUESTA
        // ======================================

        if (!Array.isArray(datos?.registros)) {
          throw new Error(
            "El servidor devolvió una respuesta inesperada."
          );
        }

        // ======================================
        // GUARDAR LOS REGISTROS REALES
        // ======================================

        if (!controlador.signal.aborted) {
          setRegistros(datos.registros);
          setTotal(Number(datos.total) || 0);
        }

      } catch (err) {

        if (err.name === "AbortError") {
          return;
        }

        if (!controlador.signal.aborted) {
          console.error(
            "Error consultando auditoría:",
            err
          );

          setError(err.message);
          setRegistros([]);
          setTotal(0);
        }

      } finally {

        if (!controlador.signal.aborted) {
          setCargando(false);
        }
      }
    }

    cargarAuditoria();

    return () => controlador.abort();

  }, [filtrosAplicados]);

  // ============================================
  // APLICAR FILTROS
  // ============================================

  function aplicarFiltros(evento) {

    evento.preventDefault();

    setFiltrosAplicados({
      documento,
      operacion,
      resultado,
      fecha,
      pagina: 1,
    });
  }

  // ============================================
  // LIMPIAR FILTROS
  // ============================================

  function limpiarFiltros() {

    setDocumento("");
    setOperacion("");
    setResultado("");
    setFecha("");

    setFiltrosAplicados({ ...filtrosVacios });
  }

  // ============================================
  // PAGINACIÓN
  // ============================================

  const totalPaginas = Math.max(
    1,
    Math.ceil(total / LIMITE_POR_PAGINA)
  );

  function paginaAnterior() {

    setFiltrosAplicados((actual) => ({
      ...actual,
      pagina: Math.max(1, actual.pagina - 1),
    }));
  }

  function paginaSiguiente() {

    setFiltrosAplicados((actual) => ({
      ...actual,
      pagina: Math.min(
        totalPaginas,
        actual.pagina + 1
      ),
    }));
  }

  // ============================================
  // FORMATEAR FECHA
  // ============================================

  function formatearFecha(valor) {

    if (!valor) {
      return "-";
    }

    const fechaRegistro = new Date(valor);

    if (Number.isNaN(fechaRegistro.getTime())) {
      return "-";
    }

    return fechaRegistro.toLocaleString("es-CO");
  }

  // ============================================
  // INTERFAZ
  // ============================================

  return (

    <section className="auditoria">

      {/* ENCABEZADO */}

      <div className="auditoria-encabezado">

        <h3>Historial de auditoría</h3>

        <p>
          Consulta las operaciones registradas
          en la base de datos PostgreSQL.
        </p>

      </div>

      {/* INFORMACIÓN */}

      <div className="auditoria-aviso">
        Los registros mostrados provienen del
        microservicio de auditoría.
      </div>

      {/* ======================================
          FILTROS
          ====================================== */}

      <form onSubmit={aplicarFiltros}>

        <div className="auditoria-filtros">

          {/* DOCUMENTO */}

          <label>

            Número de documento

            <input
              type="text"
              inputMode="numeric"
              placeholder="Buscar documento"
              value={documento}
              onChange={(e) =>
                setDocumento(
                  e.target.value.replace(/\D/g, "")
                )
              }
              maxLength={10}
            />

          </label>

          {/* OPERACIÓN */}

          <label>

            Operación

            <select
              value={operacion}
              onChange={(e) =>
                setOperacion(e.target.value)
              }
            >

              <option value="">
                Todas
              </option>

              <option value="CREAR">
                Crear
              </option>

              <option value="CONSULTAR">
                Consultar
              </option>

              <option value="MODIFICAR">
                Modificar
              </option>

              <option value="ELIMINAR">
                Eliminar
              </option>

              <option value="CONSULTA_IA">
                Consulta IA
              </option>

              <option value="CONSULTAR_AUDITORIA">
                Consultar auditoría
              </option>

            </select>

          </label>

          {/* RESULTADO */}

          <label>

            Resultado

            <select
              value={resultado}
              onChange={(e) =>
                setResultado(e.target.value)
              }
            >

              <option value="">
                Todos
              </option>

              <option value="EXITO">
                Éxito
              </option>

              <option value="ERROR">
                Error
              </option>

              <option value="DENEGADO">
                Denegado
              </option>

            </select>

          </label>

          {/* FECHA */}

          <label>

            Fecha

            <input
              type="date"
              value={fecha}
              onChange={(e) =>
                setFecha(e.target.value)
              }
            />

          </label>

        </div>

        {/* BOTONES */}

        <div className="auditoria-acciones">

          <button
            type="submit"
            className="auditoria-limpiar"
          >
            Buscar
          </button>

          <button
            type="button"
            className="auditoria-limpiar auditoria-secundario"
            onClick={limpiarFiltros}
          >
            Limpiar filtros
          </button>

        </div>

      </form>

      {/* ======================================
          MENSAJES DE ERROR
          ====================================== */}

      {error && (

        <div
          className="auditoria-error"
          role="alert"
        >
          {error}
        </div>

      )}

      {/* ======================================
          TABLA DE AUDITORÍA
          ====================================== */}

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

            {cargando ? (

              <tr>
                <td
                  colSpan="5"
                  className="auditoria-vacio"
                >
                  Cargando registros de auditoría...
                </td>
              </tr>

            ) : registros.length > 0 ? (

              registros.map((registro) => (

                <tr key={registro.id_auditoria}>

                  {/* FECHA */}

                  <td>
                    {formatearFecha(
                      registro.fecha_transaccion
                    )}
                  </td>

                  {/* USUARIO */}

                  <td>
                    {registro.usuario || "-"}
                  </td>

                  {/* OPERACIÓN */}

                  <td>
                    {registro.tipo_operacion || "-"}
                  </td>

                  {/* DOCUMENTO */}

                  <td>

                    {registro.tipo_documento || "-"}

                    <br />

                    {registro.numero_documento || "-"}

                  </td>

                  {/* RESULTADO */}

                  <td>

                    <span
                      className={
                        "auditoria-estado " +
                        (registro.resultado || "")
                          .toLowerCase()
                      }
                    >
                      {registro.resultado || "-"}
                    </span>

                  </td>

                </tr>

              ))

            ) : (

              <tr>

                <td
                  colSpan="5"
                  className="auditoria-vacio"
                >
                  {error
                    ? "No fue posible cargar los registros."
                    : "No se encontraron registros con esos filtros."}
                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>

      {/* ======================================
          TOTAL DE REGISTROS
          ====================================== */}

      {!cargando && !error && (

        <p className="auditoria-total">

          Registros encontrados: {total}

        </p>

      )}

      {/* ======================================
          PAGINACIÓN
          ====================================== */}

      {!cargando && !error && total > 0 && (

        <div className="auditoria-paginacion">

          <button
            type="button"
            onClick={paginaAnterior}
            disabled={filtrosAplicados.pagina === 1}
          >
            Anterior
          </button>

          <span>

            Página {filtrosAplicados.pagina}
            {" "}de{" "}
            {totalPaginas}

          </span>

          <button
            type="button"
            onClick={paginaSiguiente}
            disabled={
              filtrosAplicados.pagina >= totalPaginas
            }
          >
            Siguiente
          </button>

        </div>

      )}

    </section>
  );
}