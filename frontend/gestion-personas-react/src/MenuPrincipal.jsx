
import { useState } from "react";
import "./menu.css";

// Importar los componentes del sistema
import CrearPersona from "./CrearPersona.jsx";
import ModificarPersona from "./ModificarPersona.jsx";
import EliminarPersona from "./EliminarPersona.jsx";
import Auditoria from "./Auditoria.jsx";
import ChatbotIA from "./ChatbotIA.jsx";

// Opciones del menú principal
const modulos = [
  {
    id: "inicio",
    nombre: "Inicio",
    descripcion:
      "Bienvenida al sistema de Gestión de Datos Personales.",
  },
  {
    id: "crear",
    nombre: "Crear persona",
    descripcion:
      "Formulario para registrar nuevas personas.",
  },
  {
    id: "consultar",
    nombre: "Consultar persona",
    descripcion:
      "Búsqueda por tipo y número de documento.",
  },
  {
    id: "modificar",
    nombre: "Modificar persona",
    descripcion:
      "Actualización de información personal.",
  },
  {
    id: "eliminar",
    nombre: "Eliminar persona",
    descripcion:
      "Eliminación de registros con confirmación.",
  },
  {
    id: "auditoria",
    nombre: "Auditoría",
    descripcion:
      "Consulta del historial de operaciones realizadas.",
  },
  {
    id: "chatbot",
    nombre: "Chatbot IA",
    descripcion:
      "Consultas inteligentes en lenguaje natural.",
  },
];

export default function MenuPrincipal({ contenidoConsultar }) {
  const [moduloActivo, setModuloActivo] = useState("inicio");

  // Obtener información del módulo seleccionado
  const modulo =
    modulos.find((item) => item.id === moduloActivo) ||
    modulos[0];

  // Mostrar el componente correspondiente
  function mostrarContenido() {
    switch (moduloActivo) {
      case "inicio":
        return (
          <div className="menu-bienvenida">
            <h3>¡Bienvenido al sistema!</h3>

            <p>
              Selecciona una opción del menú lateral
              para acceder a los módulos de la aplicación.
            </p>

            <p>
              Desde aquí puedes crear, consultar,
              modificar y eliminar personas,
              revisar la auditoría y utilizar
              el asistente inteligente.
            </p>
          </div>
        );

      case "crear":
        return <CrearPersona />;

      case "consultar":
        return (
          contenidoConsultar || (
            <div className="menu-modulo">
              <h3>Consultar persona</h3>

              <p>
                El formulario de consulta todavía
                no está conectado al menú.
              </p>
            </div>
          )
        );

      case "modificar":
        return <ModificarPersona />;

      case "eliminar":
        return <EliminarPersona />;

      case "auditoria":
        return <Auditoria />;

      case "chatbot":
        return <ChatbotIA />;

      default:
        return (
          <div className="menu-modulo">
            <p>Selecciona una opción del menú.</p>
          </div>
        );
    }
  }

  return (
    <section className="menu-sistema">
      {/* MENÚ LATERAL */}
      <aside className="menu-lateral">
        <h2>Panel de control</h2>

        <p>Gestión de personas</p>

        <nav aria-label="Módulos del sistema">
          {modulos.map((item) => (
            <button
              key={item.id}
              type="button"
              className={
                moduloActivo === item.id
                  ? "menu-opcion activa"
                  : "menu-opcion"
              }
              aria-current={
                moduloActivo === item.id
                  ? "page"
                  : undefined
              }
              onClick={() => setModuloActivo(item.id)}
            >
              {item.nombre}
            </button>
          ))}
        </nav>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <div className="menu-contenido">
        <span className="menu-etiqueta">
          PANEL ADMINISTRATIVO
        </span>

        <h2>{modulo.nombre}</h2>

        <p>{modulo.descripcion}</p>

        {/* MOSTRAR EL MÓDULO SELECCIONADO */}
        {mostrarContenido()}
      </div>
    </section>
  );
}
