import os

import anthropic
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
client = anthropic.Anthropic()

# Almacena conversaciones por número de teléfono
conversations: dict[str, list[dict]] = {}

SYSTEM_PROMPT = "Eres un asistente amable y útil en WhatsApp. Sé conciso en tus respuestas. Responde en el mismo idioma que el usuario."
MAX_HISTORY = 20  # Máximo de mensajes en el historial por usuario


def get_claude_response(user_number: str, user_message: str) -> str:
    if user_number not in conversations:
        conversations[user_number] = []

    history = conversations[user_number]
    history.append({"role": "user", "content": user_message})

    # Limitar historial para no exceder el contexto
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    assistant_text = response.content[0].text
    history.append({"role": "assistant", "content": assistant_text})

    return assistant_text


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    user_number = request.form.get("From", "")

    if not incoming_msg:
        return "", 204

    # Comando para borrar historial
    if incoming_msg.lower() == "reset":
        conversations.pop(user_number, None)
        reply_text = "Conversación reiniciada."
    else:
        reply_text = get_claude_response(user_number, incoming_msg)

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp), 200, {"Content-Type": "text/xml"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
