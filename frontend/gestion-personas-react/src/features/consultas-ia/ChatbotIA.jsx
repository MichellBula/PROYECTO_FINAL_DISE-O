
import { useState } from "react";
import "./ChatbotIA.css";

const mensajeInicial = {
  id: 1,
  tipo: "asistente",
  texto:
    "¡Hola! Soy el asistente del Sistema de Gestión de Datos Personales. Actualmente estoy en modo demostración.",
};

export default function ChatbotIA() {
  const [pregunta, setPregunta] = useState("");
  const [mensajes, setMensajes] = useState([mensajeInicial]);

  function enviarMensaje(evento) {
    evento.preventDefault();

    const texto = pregunta.trim();

    if (!texto) return;

    const mensajeUsuario = {
      id: crypto.randomUUID(),
      tipo: "usuario",
      texto: texto,
    };

    const respuestaDemo = {
      id: crypto.randomUUID(),
      tipo: "asistente",
      texto:
        " Esta es una respuesta de demostración. " +
        "El chatbot todavía no está conectado a n8n ni a RAG. " +
        "No se ha consultado ninguna base de datos.",
    };

    setMensajes((anteriores) => [
      ...anteriores,
      mensajeUsuario,
      respuestaDemo,
    ]);

    setPregunta("");
  }

  function limpiarChat() {
    setMensajes([{ ...mensajeInicial }]);
    setPregunta("");
  }

  return (
    <section className="chatbot-contenedor">
      <div className="chatbot-cabecera">
        <div>
          <h3> Chatbot IA</h3>
          <p>
            Asistente del Sistema de Gestión de Datos Personales
          </p>
        </div>

        <span className="chatbot-etiqueta">
          Modo demostración
        </span>
      </div>

      <div className="chatbot-aviso">
         El chatbot todavía no está conectado al backend.
        No introduzcas datos personales reales durante las pruebas.
      </div>

      <div
        className="chatbot-conversacion"
        aria-live="polite"
      >
        {mensajes.map((mensaje) => (
          <div
            key={mensaje.id}
            className={`chatbot-mensaje ${mensaje.tipo}`}
          >
            <span className="chatbot-autor">
              {mensaje.tipo === "usuario"
                ? "Tú"
                : " Asistente"}
            </span>

            <p>{mensaje.texto}</p>
          </div>
        ))}
      </div>

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
        />

        <button
          type="submit"
          disabled={!pregunta.trim()}
        >
          Enviar
        </button>
      </form>

      <button
        type="button"
        className="chatbot-limpiar"
        onClick={limpiarChat}
      >
         Limpiar conversación
      </button>
    </section>
  );
}
