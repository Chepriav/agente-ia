import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """Eres un experto de clase mundial en panificación técnica y artesanal, especializado exclusivamente en pizza (Napoletana, Romana, New York Style, Detroit y Gluten-Free). Tu enfoque combina la tradición italiana con la ciencia de alimentos."""

historial = []

def chat(mensaje_usuario):
    historial.append({"role": "user", "content": mensaje_usuario})

    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=historial
    )

    mensaje_agente = respuesta.content[0].text
    historial.append({"role": "assistant", "content": mensaje_agente})

    return mensaje_agente

print("🤖 Agente listo. Escribe 'salir' para terminar.\n")

while True:
    entrada = input("Tú: ")
    if entrada.lower() == "salir":
        break
    respuesta = chat(entrada)
    print(f"\nAgente: {respuesta}\n")
