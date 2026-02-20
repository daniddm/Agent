import anthropic


def main():
    client = anthropic.Anthropic()
    messages = []

    print("Chatbot de IA (escribe 'salir' para terminar)")
    print("-" * 45)

    while True:
        user_input = input("\nTú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("¡Hasta luego!")
            break

        messages.append({"role": "user", "content": user_input})

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="Eres un asistente amable y útil. Responde en el mismo idioma que el usuario.",
            messages=messages,
        ) as stream:
            print("\nBot: ", end="", flush=True)
            response_text = ""
            for text in stream.text_stream:
                print(text, end="", flush=True)
                response_text += text
            print()

        messages.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    main()
