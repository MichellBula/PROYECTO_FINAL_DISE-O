
import { useState } from "react";
import { consultarIA } from "../../services/api.js";
import "./ChatbotIA.css";


// ============================================
// MENSAJE INICIAL
// ============================================

const mensajeInicial = {
  id: "bienvenida",
  tipo: "asistente",
  texto:
    "¡Hola! Soy el asistente inteligente del Sistema de Gestión de Datos Personales. " +
    "Puedes hacer preguntas sobre la información disponible en el sistema.",
};


// ============================================
// COMPONENTE CHATBOT IA
// ============================================

export default function ChatbotIA() {
  const [pregunta, setPregunta] = useState("");
  const [mensajes, setMensajes] = useState([mensajeInicial]);
  const [cargando, setCargando] = useState(false);


  // ==========================================
  // ENVIAR PREGUNTA
  // ==========================================

  async function enviarMensaje(evento) {
    evento.preventDefault();

    const texto = pregunta.trim();

    if (!texto || cargando) {
      return;
    }

    const mensajeUsuario = {
      id: crypto.randomUUID(),
      tipo: "usuario",
      texto,
    };

    // Mostrar inmediatamente la pregunta.
    setMensajes((anteriores) => [
      ...anteriores,
      mensajeUsuario,
    ]);

    setPregunta("");
    setCargando(true);

    try {
      // Enviar la pregunta a FastAPI mediante la Gateway.
      const resultado = await consultarIA(texto);

      if (
        typeof resultado.respuesta !== "string" ||
        !resultado.respuesta.trim()
      ) {
        throw new Error(
          "El asistente no devolvió una respuesta válida."
        );
      }

      const mensajeAsistente = {
        id: crypto.randomUUID(),
        tipo: "asistente",
        texto: resultado.respuesta,
      };

      setMensajes((anteriores) => [
        ...anteriores,
        mensajeAsistente,
      ]);

    } catch (error) {
      let mensajeError =
        error.message || "No se pudo procesar la consulta.";

      if (error.status === 401) {
        mensajeError =
          "Tu sesión ha terminado. Inicia sesión nuevamente.";

      } else if (error.status === 403) {
        mensajeError =
          "No tienes autorización para realizar esta consulta.";

      } else if (error.status === 422) {
        mensajeError =
          "La pregunta no corresponde a una consulta disponible.";

      } else if (error.status === 503) {
        mensajeError =
          "El servicio de consultas inteligentes no está disponible en este momento.";
      }

      setMensajes((anteriores) => [
        ...anteriores,
        {
          id: crypto.randomUUID(),
          tipo: "error",
          texto: mensajeError,
        },
      ]);

    } finally {
      setCargando(false);
    }
  }


  // ==========================================
  // LIMPIAR CONVERSACIÓN
  // ==========================================

  function limpiarChat() {
    if (cargando) {
      return;
    }

    setMensajes([{ ...mensajeInicial }]);
    setPregunta("");
  }


  // ==========================================
  // INTERFAZ
  // ==========================================

  return (
    <section className="chatbot-contenedor">

      {/* ENCABEZADO */}
      <div className="chatbot-cabecera">
        <div>
          <h3>Chatbot IA</h3>

          <p>
            Asistente inteligente del Sistema
            de Gestión de Datos Personales
          </p>
        </div>

        <span className="chatbot-etiqueta">
          Conectado a FastAPI y n8n
        </span>
      </div>


      {/* AVISO */}
      <div className="chatbot-aviso">
        Las consultas requieren autenticación con Roble.
        Por ahora solo está habilitada la consulta del
        total de personas registradas.
        No introduzcas datos personales reales durante
        las pruebas.
      </div>


      {/* CONVERSACIÓN */}
      <div
        className="chatbot-conversacion"
        aria-live="polite"
        aria-label="Conversación con el asistente"
      >
        {mensajes.map((mensaje) => (
          <div
            key={mensaje.id}
            className={`chatbot-mensaje ${mensaje.tipo}`}
          >
            <span className="chatbot-autor">
              {mensaje.tipo === "usuario"
                ? "Tú"
                : mensaje.tipo === "error"
                ? "Sistema"
                : "Asistente"}
            </span>

            <p>{mensaje.texto}</p>
          </div>
        ))}

        {/* INDICADOR DE ESPERA */}
        {cargando && (
          <div className="chatbot-mensaje asistente">
            <span className="chatbot-autor">
              Asistente
            </span>

            <p>Procesando tu pregunta...</p>
          </div>
        )}
      </div>


      {/* FORMULARIO */}
      <form
        className="chatbot-formulario"
        onSubmit={enviarMensaje}
      >
        <input
          type="text"
          value={pregunta}
          onChange={(evento) =>
            setPregunta(evento.target.value)
          }
          placeholder="Escribe tu pregunta..."
          maxLength={500}
          aria-label="Escribe tu pregunta"
          disabled={cargando}
          required
        />

        <button
          type="submit"
          disabled={!pregunta.trim() || cargando}
        >
          {cargando ? "Enviando..." : "Enviar"}
        </button>
      </form>


      {/* LIMPIAR CHAT */}
      <button
        type="button"
        className="chatbot-limpiar"
        onClick={limpiarChat}
        disabled={cargando}
      >
        Limpiar conversación
      </button>

    </section>
  );
}
