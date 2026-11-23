import { useEffect, useState } from "react";

import MenuPrincipal from "./components/MenuPrincipal.jsx";

// Nuevo componente de registro
import Registro from "./features/autenticacion/Registro.jsx";

import {
  cerrarSesion,
  consultarPersona,
  consultarSesion,
  iniciarSesion,
} from "./services/api.js";


// =====================================================
// COMPONENTE DE MENSAJES
// =====================================================

function Mensaje({ tipo = "info", children }) {
  if (!children) return null;

  return (
    <p
      className={`mensaje mensaje--${tipo}`}
      role="status"
    >
      {children}
    </p>
  );
}


// =====================================================
// APLICACIÓN PRINCIPAL
// =====================================================

export default function App() {

  // ===================================================
  // 1. AUTENTICACIÓN
  // ===================================================

  const [sesion, setSesion] = useState(null);

  const [verificando, setVerificando] = useState(true);

  const [correo, setCorreo] = useState("");

  const [contrasena, setContrasena] = useState("");

  // Alternar entre login y registro
  const [vistaAcceso, setVistaAcceso] = useState("login");


  // ===================================================
  // 2. CONSULTA DE PERSONAS
  // ===================================================

  const [tipo, setTipo] = useState("Cédula");

  const [numero, setNumero] = useState("");

  const [persona, setPersona] = useState(null);

  const [mensajeConsulta, setMensajeConsulta] = useState("");

  const [tipoMensajeConsulta, setTipoMensajeConsulta] =
    useState("info");


  // ===================================================
  // 3. ESTADOS GENERALES
  // ===================================================

  const [mensaje, setMensaje] = useState("");

  const [tipoMensaje, setTipoMensaje] = useState("info");

  const [ocupado, setOcupado] = useState(false);


  // ===================================================
  // 4. COMPROBAR SESIÓN EXISTENTE
  // ===================================================

  useEffect(() => {

    let vigente = true;

    consultarSesion()
      .then((datos) => {

        if (vigente) {
          setSesion(datos.usuario);
        }

      })
      .catch(() => {

        if (vigente) {
          setSesion(null);
        }

      })
      .finally(() => {

        if (vigente) {
          setVerificando(false);
        }

      });

    return () => {
      vigente = false;
    };

  }, []);


  // ===================================================
  // 5. CAMBIAR ENTRE LOGIN Y REGISTRO
  // ===================================================

  function mostrarRegistro() {

    setVistaAcceso("registro");

    setMensaje("");
    setContrasena("");
  }


  function mostrarLogin() {

    setVistaAcceso("login");

    setMensaje("");
    setTipoMensaje("info");
  }


  // ===================================================
  // 6. INICIAR SESIÓN
  // ===================================================

  async function entrar(evento) {
    evento.preventDefault();

    setOcupado(true);
    setMensaje("");
    setPersona(null);
    setMensajeConsulta("");

    try {

      const datos = await iniciarSesion(
        correo.trim(),
        contrasena
      );

      setSesion(datos.usuario);

      setContrasena("");

      setVistaAcceso("login");

      setTipoMensaje("success");

      setMensaje(
        "Sesión iniciada correctamente con Roble."
      );

    } catch (error) {

      setTipoMensaje("error");

      setMensaje(error.message);

    } finally {

      setOcupado(false);

    }
  }


  // ===================================================
  // 7. CONSULTAR PERSONA
  // ===================================================

  async function buscar(evento) {
    evento.preventDefault();

    if (!sesion) {

      setTipoMensajeConsulta("error");

      setMensajeConsulta(
        "Debes iniciar sesión para consultar personas."
      );

      return;
    }

    setOcupado(true);

    setPersona(null);
    setMensajeConsulta("");

    try {

      const datos = await consultarPersona(
        tipo,
        numero.trim()
      );

      setPersona(datos);

      setTipoMensajeConsulta("success");

      setMensajeConsulta(
        "Persona encontrada correctamente."
      );

    } catch (error) {

      if (error.status === 401) {

        setSesion(null);
        setPersona(null);

        setTipoMensaje("error");

        setMensaje(
          "Tu sesión terminó. Vuelve a iniciar sesión."
        );

        setTipoMensajeConsulta("error");

        setMensajeConsulta(
          "No tienes una sesión activa."
        );

      } else if (error.status === 404) {

        setTipoMensajeConsulta("info");

        setMensajeConsulta(
          "No se encontró una persona con ese documento."
        );

      } else {

        setTipoMensajeConsulta("error");

        setMensajeConsulta(
          error.message ||
          "No se pudo realizar la consulta."
        );
      }

    } finally {

      setOcupado(false);

    }
  }


  // ===================================================
  // 8. CERRAR SESIÓN
  // ===================================================

  async function salir() {

    setOcupado(true);

    setMensaje("");

    try {

      await cerrarSesion();

      setSesion(null);

      setPersona(null);

      setNumero("");

      setTipo("Cédula");

      setCorreo("");

      setContrasena("");

      setVistaAcceso("login");

      setMensajeConsulta("");

      setTipoMensajeConsulta("info");

      setTipoMensaje("info");

      setMensaje(
        "Sesión cerrada correctamente."
      );

    } catch (error) {

      setTipoMensaje("error");

      setMensaje(error.message);

    } finally {

      setOcupado(false);

    }
  }


  // ===================================================
  // 9. CONTENIDO DEL MÓDULO CONSULTAR
  // ===================================================

  const contenidoConsultar = (

    <section className="panel panel-consulta">

      <div className="panel-encabezado">

        <h2>Consultar persona</h2>

        <p>
          Busca una persona por tipo y número de documento.
          Esta operación requiere una sesión activa.
        </p>

      </div>


      <form
        onSubmit={buscar}
        className="formulario"
      >

        <label htmlFor="tipo">
          Tipo de documento
        </label>

        <select
          id="tipo"
          value={tipo}
          onChange={(e) => {

            setTipo(e.target.value);

            setPersona(null);

            setMensajeConsulta("");

          }}
          disabled={!sesion || ocupado}
        >

          <option value="Cédula">
            Cédula
          </option>

          <option value="Tarjeta de identidad">
            Tarjeta de identidad
          </option>

        </select>


        <label htmlFor="numero">
          Número de documento
        </label>

        <input
          id="numero"
          type="text"
          inputMode="numeric"
          pattern="[0-9]{1,10}"
          maxLength={10}
          value={numero}
          onChange={(e) => {

            setNumero(
              e.target.value.replace(/\D/g, "")
            );

            setPersona(null);

            setMensajeConsulta("");

          }}
          disabled={!sesion || ocupado}
          required
          placeholder="Entre 1 y 10 dígitos"
        />


        <button
          type="submit"
          className="boton"
          disabled={!sesion || ocupado}
        >
          {ocupado
            ? "Consultando…"
            : "Consultar persona"}
        </button>

      </form>


      <div className="mensajes-contenedor">

        <Mensaje tipo={tipoMensajeConsulta}>
          {mensajeConsulta}
        </Mensaje>

      </div>


      {persona !== null && (

        <div className="panel resultado">

          <div className="panel-encabezado">

            <h3>Resultado de la consulta</h3>

            <p>
              Datos obtenidos mediante FastAPI.
            </p>

          </div>

          <pre>
            {JSON.stringify(persona, null, 2)}
          </pre>

        </div>

      )}

    </section>
  );


  // ===================================================
  // 10. INTERFAZ PRINCIPAL
  // ===================================================

  return (

    <main className="pagina">

      {/* =====================================
          ENCABEZADO
      ===================================== */}

      <header className="cabecera">

        <span className="marca">

          <span className="marca-icono">
            GD
          </span>

          {" "}Gestión de Datos Personales

        </span>


        <span className="etiqueta">
          Roble + FastAPI + PostgreSQL
        </span>

      </header>


      {/* =====================================
          PRESENTACIÓN
      ===================================== */}

      <section className="presentacion presentacion-centrada">

        <div className="presentacion-texto">

          <p className="sobrelinea">
            DISEÑO DE SOFTWARE II
          </p>

          <h1>
            Sistema de Gestión de Datos Personales
          </h1>

          <p className="subtitulo">
            Plataforma de administración de información
            personal, autenticación con Roble y consultas
            protegidas mediante FastAPI.
          </p>

        </div>


        <div className="indicador">

          {verificando
            ? "Comprobando sesión…"
            : sesion
            ? "● Sesión activa"
            : "○ Sesión no iniciada"}

        </div>

      </section>


      {/* =====================================
          PANEL DE ACCESO
      ===================================== */}

      <div className="contenido contenido-centrado">

        {/* MOSTRAR REGISTRO */}

        {!verificando &&
        !sesion &&
        vistaAcceso === "registro" ? (

          <Registro
            onVolver={mostrarLogin}
          />

        ) : (

          <section className="panel panel-acceso">

            <div className="panel-encabezado acceso-encabezado">

              <div className="acceso-icono">

                <span aria-hidden="true">
                  🔐
                </span>

              </div>

              <h2>Acceso al sistema</h2>

              <p>
                Ingresa con tu cuenta de Roble
                para acceder a las funciones
                del sistema.
              </p>

            </div>


            {/* COMPROBANDO SESIÓN */}

            {verificando ? (

              <p className="acceso-cargando">
                Comprobando la sesión guardada…
              </p>

            ) : sesion ? (

              /* USUARIO AUTENTICADO */

              <div className="perfil perfil-centrado">

                <span className="avatar">

                  {sesion.name
                    ?.slice(0, 1)
                    ?.toUpperCase() || "U"}

                </span>


                <strong>
                  {sesion.name || "Usuario"}
                </strong>


                <span className="muted">
                  {sesion.email}
                </span>


                <p className="muted small">
                  Sesión iniciada con Roble.
                </p>


                <button
                  type="button"
                  className="boton boton-secundario"
                  onClick={salir}
                  disabled={ocupado}
                >
                  Cerrar sesión
                </button>

              </div>

            ) : (

              /* FORMULARIO DE LOGIN */

              <form
                onSubmit={entrar}
                className="formulario formulario-acceso"
              >

                <div className="campo-acceso">

                  <label htmlFor="correo">
                    Correo electrónico
                  </label>

                  <input
                    id="correo"
                    type="email"
                    autoComplete="username"
                    value={correo}
                    onChange={(e) =>
                      setCorreo(e.target.value)
                    }
                    required
                    placeholder="usuario@correo.com"
                  />

                </div>


                <div className="campo-acceso">

                  <label htmlFor="contrasena">
                    Contraseña
                  </label>

                  <input
                    id="contrasena"
                    type="password"
                    autoComplete="current-password"
                    value={contrasena}
                    onChange={(e) =>
                      setContrasena(e.target.value)
                    }
                    required
                    placeholder="Contraseña de Roble"
                  />

                </div>


                <button
                  type="submit"
                  className="boton boton-ingresar"
                  disabled={ocupado}
                >

                  {ocupado
                    ? "Verificando…"
                    : "Iniciar sesión"}

                </button>


                {/* NUEVO BOTÓN DE REGISTRO */}

                <button
                  type="button"
                  className="boton boton-secundario"
                  onClick={mostrarRegistro}
                  disabled={ocupado}
                >
                  Crear una cuenta
                </button>

              </form>

            )}

          </section>

        )}

      </div>


      {/* =====================================
          MENSAJES GENERALES
      ===================================== */}

      <div className="mensajes-contenedor">

        <Mensaje tipo={tipoMensaje}>
          {mensaje}
        </Mensaje>

      </div>


      {/* =====================================
          MENÚ PRINCIPAL
      ===================================== */}

      {!verificando && sesion && (

        <MenuPrincipal
          contenidoConsultar={contenidoConsultar}
        />

      )}


      {/* =====================================
          PIE DE PÁGINA
      ===================================== */}

      <footer className="pie">

        Sistema de Gestión de Datos Personales

        <span>
          {" "}· Entorno de desarrollo · Utiliza datos de prueba
        </span>

      </footer>

    </main>
  );
}