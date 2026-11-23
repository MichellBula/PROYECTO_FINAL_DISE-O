import { useState } from "react";

import {
  registrarUsuario,
  verificarCorreo,
} from "../../services/api.js";


export default function Registro({ onVolver }) {

  // ==========================================
  // 1. DATOS DEL FORMULARIO
  // ==========================================

  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmarContrasena, setConfirmarContrasena] = useState("");

  // ==========================================
  // 2. VERIFICACIÓN DEL CORREO
  // ==========================================

  const [codigo, setCodigo] = useState("");

  // Etapas: registro, verificacion, completado
  const [paso, setPaso] = useState("registro");

  // ==========================================
  // 3. ESTADOS DE LA INTERFAZ
  // ==========================================

  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");


  // ==========================================
  // 4. REGISTRAR USUARIO CON ROBLE
  // ==========================================

  async function registrar(evento) {
    evento.preventDefault();

    setError("");
    setMensaje("");

    // Comprobar contraseñas
    if (contrasena !== confirmarContrasena) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    if (contrasena.length < 8) {
      setError(
        "La contraseña debe tener al menos 8 caracteres."
      );
      return;
    }

    setOcupado(true);

    try {
      await registrarUsuario(
        nombre.trim(),
        correo.trim().toLowerCase(),
        contrasena
      );

      // Eliminar la contraseña del estado
      setContrasena("");
      setConfirmarContrasena("");

      setMensaje(
        "Solicitud enviada correctamente. " +
        "Revisa tu correo para obtener el código de verificación."
      );

      // Mostrar formulario de verificación
      setPaso("verificacion");

    } catch (error) {
      setError(
        error.message || "No se pudo completar el registro."
      );

    } finally {
      setOcupado(false);
    }
  }


  // ==========================================
  // 5. VERIFICAR CORREO CON ROBLE
  // ==========================================

  async function verificar(evento) {
    evento.preventDefault();

    setError("");
    setMensaje("");
    setOcupado(true);

    try {
      await verificarCorreo(
        correo.trim().toLowerCase(),
        codigo.trim()
      );

      setCodigo("");
      setPaso("completado");

      setMensaje(
        "Tu correo fue verificado correctamente. " +
        "Ya puedes iniciar sesión."
      );

    } catch (error) {
      setError(
        error.message || "No se pudo verificar el correo."
      );

    } finally {
      setOcupado(false);
    }
  }


  // ==========================================
  // 6. INTERFAZ
  // ==========================================

  return (
    <section className="panel panel-acceso">

      <div className="panel-encabezado acceso-encabezado">

        <div className="acceso-icono">
          <span aria-hidden="true">👤</span>
        </div>

        <h2>Crear una cuenta</h2>

        <p>
          Regístrate utilizando Roble para acceder
          al sistema de Gestión de Datos Personales.
        </p>

      </div>


      {/* =====================================
          MENSAJES
      ===================================== */}

      {error && (
        <p
          className="mensaje mensaje--error"
          role="alert"
        >
          {error}
        </p>
      )}

      {mensaje && (
        <p
          className="mensaje mensaje--success"
          role="status"
        >
          {mensaje}
        </p>
      )}


      {/* =====================================
          ETAPA 1: REGISTRO
      ===================================== */}

      {paso === "registro" && (

        <form
          onSubmit={registrar}
          className="formulario formulario-acceso"
        >

          <div className="campo-acceso">

            <label htmlFor="registro-nombre">
              Nombre completo
            </label>

            <input
              id="registro-nombre"
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Tu nombre completo"
              autoComplete="name"
              minLength={2}
              maxLength={100}
              required
              disabled={ocupado}
            />

          </div>


          <div className="campo-acceso">

            <label htmlFor="registro-correo">
              Correo electrónico
            </label>

            <input
              id="registro-correo"
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="usuario@correo.com"
              autoComplete="email"
              maxLength={320}
              required
              disabled={ocupado}
            />

          </div>


          <div className="campo-acceso">

            <label htmlFor="registro-contrasena">
              Contraseña
            </label>

            <input
              id="registro-contrasena"
              type="password"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              placeholder="Crea una contraseña"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
              required
              disabled={ocupado}
            />

          </div>


          <div className="campo-acceso">

            <label htmlFor="registro-confirmar">
              Confirmar contraseña
            </label>

            <input
              id="registro-confirmar"
              type="password"
              value={confirmarContrasena}
              onChange={(e) =>
                setConfirmarContrasena(e.target.value)
              }
              placeholder="Repite tu contraseña"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
              required
              disabled={ocupado}
            />

          </div>


          <button
            type="submit"
            className="boton boton-ingresar"
            disabled={ocupado}
          >
            {ocupado
              ? "Registrando…"
              : "Crear cuenta"}
          </button>

        </form>
      )}


      {/* =====================================
          ETAPA 2: VERIFICAR CORREO
      ===================================== */}

      {paso === "verificacion" && (

        <form
          onSubmit={verificar}
          className="formulario formulario-acceso"
        >

          <p>
            Introduce el código de verificación
            enviado a tu correo electrónico.
          </p>

          <div className="campo-acceso">

            <label htmlFor="registro-codigo">
              Código de verificación
            </label>

            <input
              id="registro-codigo"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="Código recibido por correo"
              minLength={4}
              maxLength={32}
              required
              disabled={ocupado}
            />

          </div>

          <button
            type="submit"
            className="boton boton-ingresar"
            disabled={ocupado}
          >
            {ocupado
              ? "Verificando…"
              : "Verificar correo"}
          </button>

        </form>
      )}


      {/* =====================================
          ETAPA 3: REGISTRO COMPLETADO
      ===================================== */}

      {paso === "completado" && (

        <div className="perfil perfil-centrado">

          <span className="avatar">
            ✓
          </span>

          <h3>¡Registro completado!</h3>

          <p>
            Tu cuenta está lista para iniciar sesión.
          </p>

          <p className="muted small">
            Cuando ingreses por primera vez,
            se creará tu perfil con el rol CONSULTA.
          </p>

        </div>
      )}


      {/* =====================================
          VOLVER AL LOGIN
      ===================================== */}

      <button
        type="button"
        className="boton boton-secundario"
        onClick={onVolver}
        disabled={ocupado}
      >
        {paso === "completado"
          ? "Ir a iniciar sesión"
          : "Volver al inicio de sesión"}
      </button>

    </section>
  );
}