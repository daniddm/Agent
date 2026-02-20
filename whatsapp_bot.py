import os

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- Configuración del proveedor de IA ---
# Cambia AI_PROVIDER a "claude" si prefieres usar Claude (de pago).
# Por defecto usa Groq (gratis).
AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq")

# Almacena conversaciones por número de teléfono
conversations: dict[str, list[dict]] = {}

SYSTEM_PROMPT = "Eres un asistente amable y útil en WhatsApp. Sé conciso en tus respuestas. Responde en el mismo idioma que el usuario."
MAX_HISTORY = 20


def _build_history(user_number: str, user_message: str) -> list[dict]:
    if user_number not in conversations:
        conversations[user_number] = []

    history = conversations[user_number]
    history.append({"role": "user", "content": user_message})

    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    return history


def _save_reply(user_number: str, text: str) -> None:
    conversations[user_number].append({"role": "assistant", "content": text})


def get_groq_response(user_number: str, user_message: str) -> str:
    """Usa Groq API (GRATIS) con Llama 3.3 70B."""
    from groq import Groq

    client = Groq()  # usa GROQ_API_KEY del entorno
    history = _build_history(user_number, user_message)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history],
        max_tokens=500,
    )

    reply = response.choices[0].message.content
    _save_reply(user_number, reply)
    return reply


def get_claude_response(user_number: str, user_message: str) -> str:
    """Usa Claude API (de pago)."""
    import anthropic

    client = anthropic.Anthropic()
    history = _build_history(user_number, user_message)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    reply = response.content[0].text
    _save_reply(user_number, reply)
    return reply


def get_ai_response(user_number: str, user_message: str) -> str:
    if AI_PROVIDER == "claude":
        return get_claude_response(user_number, user_message)
    return get_groq_response(user_number, user_message)


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    user_number = request.form.get("From", "")

    if not incoming_msg:
        return "", 204

    if incoming_msg.lower() == "reset":
        conversations.pop(user_number, None)
        reply_text = "Conversación reiniciada."
    else:
        reply_text = get_ai_response(user_number, incoming_msg)

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp), 200, {"Content-Type": "text/xml"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
