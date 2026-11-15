import { useEffect, useState } from 'react';
import {
  cerrarSesion,
  consultarPersona,
  consultarSesion,
  iniciarSesion,
} from './api.js';

function Mensaje({ tipo = 'info', children }) {
  if (!children) return null;
  return <p className={`mensaje mensaje--${tipo}`} role="status">{children}</p>;
}

export default function App() {
  const [sesion, setSesion] = useState(null);
  const [verificando, setVerificando] = useState(true);
  const [correo, setCorreo] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [tipo, setTipo] = useState('Cédula');
  const [numero, setNumero] = useState('');
  const [persona, setPersona] = useState(null);
  const [mensaje, setMensaje] = useState('');
  const [tipoMensaje, setTipoMensaje] = useState('info');
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    let vigente = true;
    consultarSesion()
      .then((datos) => { if (vigente) setSesion(datos.usuario); })
      .catch(() => { if (vigente) setSesion(null); })
      .finally(() => { if (vigente) setVerificando(false); });
    return () => { vigente = false; };
  }, []);

  async function entrar(evento) {
    evento.preventDefault();
    setOcupado(true);
    setMensaje('');
    setPersona(null);
    try {
      const datos = await iniciarSesion(correo.trim(), contrasena);
      setSesion(datos.usuario);
      setContrasena('');
      setTipoMensaje('success');
      setMensaje('Sesión iniciada correctamente con Roble.');
    } catch (error) {
      setTipoMensaje('error');
      setMensaje(error.message);
    } finally {
      setOcupado(false);
    }
  }

  async function buscar(evento) {
    evento.preventDefault();
    setOcupado(true);
    setPersona(null);
    setMensaje('');
    try {
      const datos = await consultarPersona(tipo, numero.trim());
      setPersona(datos);
      setTipoMensaje('success');
      setMensaje('Consulta realizada correctamente y registrada en auditoría.');
    } catch (error) {
      if (error.status === 401) {
        setSesion(null);
        setTipoMensaje('error');
        setMensaje('Tu sesión terminó. Vuelve a iniciar sesión.');
      } else if (error.status === 404) {
        setTipoMensaje('info');
        setMensaje('Persona no encontrada. La consulta también queda auditada.');
      } else {
        setTipoMensaje('error');
        setMensaje(error.message);
      }
    } finally {
      setOcupado(false);
    }
  }

  async function salir() {
    setOcupado(true);
    setMensaje('');
    try {
      await cerrarSesion();
      setSesion(null);
      setPersona(null);
      setNumero('');
      setCorreo('');
      setContrasena('');
      setTipoMensaje('info');
      setMensaje('Sesión cerrada correctamente.');
    } catch (error) {
      setTipoMensaje('error');
      setMensaje(error.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <main className="pagina">
      <header className="cabecera">
        <span className="marca"><span className="marca-icono">GD</span> Gestión de Datos Personales</span>
        <span className="etiqueta">Prototipo de integración · Roble + PostgreSQL</span>
      </header>

      <section className="presentacion">
        <div>
          <p className="sobrelinea">Diseño de Software II</p>
          <h1>Autenticación y consulta de personas</h1>
          <p className="subtitulo">Inicio de sesión con Roble, consultas protegidas con FastAPI y auditoría en PostgreSQL.</p>
        </div>
        <div className="indicador">{verificando ? 'Comprobando sesión…' : sesion ? '● Sesión activa' : '○ Sesión no iniciada'}</div>
      </section>

      <div className="contenido">
        <section className="panel">
          <div className="panel-encabezado">
            <h2>Acceso</h2>
            <p>Usa una cuenta creada y verificada en el contrato Roble del proyecto.</p>
          </div>

          {verificando ? (
            <p>Comprobando la sesión guardada…</p>
          ) : sesion ? (
            <div className="perfil">
              <span className="avatar">{sesion.name?.slice(0, 1)?.toUpperCase() || 'U'}</span>
              <strong>{sesion.name || 'Usuario'}</strong>
              <span className="muted">{sesion.email}</span>
              <p className="muted small">Identidad verificada por Roble. La cookie permanece protegida por el navegador.</p>
              <button className="boton boton-secundario" onClick={salir} disabled={ocupado}>Cerrar sesión</button>
            </div>
          ) : (
            <form onSubmit={entrar} className="formulario">
              <label htmlFor="correo">Correo</label>
              <input id="correo" type="email" autoComplete="username" value={correo} onChange={(e) => setCorreo(e.target.value)} required placeholder="usuario@correo.com" />
              <label htmlFor="contrasena">Contraseña</label>
              <input id="contrasena" type="password" autoComplete="current-password" value={contrasena} onChange={(e) => setContrasena(e.target.value)} required placeholder="Contraseña de Roble" />
              <button className="boton" disabled={ocupado}>{ocupado ? 'Verificando…' : 'Iniciar sesión'}</button>
            </form>
          )}
        </section>

        <section className="panel">
          <div className="panel-encabezado">
            <h2>Consultar persona</h2>
            <p>Esta consulta requiere una sesión activa. Las solicitudes quedan auditadas.</p>
          </div>
          <form onSubmit={buscar} className="formulario">
            <label htmlFor="tipo">Tipo de documento</label>
            <select id="tipo" value={tipo} onChange={(e) => setTipo(e.target.value)} disabled={!sesion || ocupado}>
              <option value="Cédula">Cédula</option>
              <option value="Tarjeta de identidad">Tarjeta de identidad</option>
            </select>
            <label htmlFor="numero">Número de documento</label>
            <input id="numero" type="text" inputMode="numeric" pattern="[0-9]{1,10}" maxLength={10} value={numero} onChange={(e) => setNumero(e.target.value.replace(/\D/g, ''))} disabled={!sesion || ocupado} required placeholder="Entre 1 y 10 dígitos" />
            <button className="boton" disabled={!sesion || ocupado}>{ocupado ? 'Consultando…' : 'Consultar persona'}</button>
          </form>
          {!sesion && !verificando && <p className="aviso">Inicia sesión para habilitar la consulta.</p>}
        </section>
      </div>

      <Mensaje tipo={tipoMensaje}>{mensaje}</Mensaje>

      {persona !== null && (
        <section className="panel resultado">
          <div className="panel-encabezado"><h2>Resultado de la consulta</h2><p>Datos obtenidos de PostgreSQL mediante FastAPI.</p></div>
          <pre>{JSON.stringify(persona, null, 2)}</pre>
        </section>
      )}

      <footer className="pie">Entorno de desarrollo local. Usa únicamente datos de prueba, no información personal real.</footer>
    </main>
  );
}
