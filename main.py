import time
import threading
from fastapi import FastAPI, Request
from botpress_talk import crear_usuario, create_conversation, create_message, list_messages

# ---------------------------------------------------------------------------------
# Configuraciones globales
# ---------------------------------------------------------------------------------
BOTPRESS_URL = 'https://chat.botpress.cloud/'
HOOK_ID = 'c89e067a-b093-4a96-88fd-e2d5ab7875be'  # Reemplaza con tu Hook ID
BASE_URL = f'{BOTPRESS_URL}{HOOK_ID}'

BUFFER_TIME = 20  # Tiempo (en segundos) que esperamos antes de enviar los mensajes acumulados
app = FastAPI()

# Diccionario global para acumular mensajes: { conversation_id: [lista_de_previews] }
messages_buffer = {}

# Diccionario para manejar los temporizadores: { conversation_id: timer_object }
timers = {}

# Lock para proteger el acceso concurrente a los diccionarios
lock = threading.Lock()


# ---------------------------------------------------------------------------------
# Función para enviar mensajes al Botpress "lógico"
# ---------------------------------------------------------------------------------
def send_buffered_messages_to_logic(conversation_id, messages_list):
    """
    Envía la lista de mensajes concatenados a Botpress.
    Aquí puedes adaptar la lógica de envío, por ejemplo:
      - crear_usuario()
      - create_conversation()
      - create_message()
      - list_messages()  (opcional, si quieres ver la respuesta del bot)
    """
    # Unimos los mensajes en un único string con saltos de línea
    texto_concatenado = "\n".join(messages_list)
    print(f"[DEBUG] Enviando al bot lógico:\nConversationID: {conversation_id}\nMensajes:\n{texto_concatenado}\n")

    # 1. Crear usuario
    user_id, x_user_key = crear_usuario(BASE_URL)
    if not user_id or not x_user_key:
        print(f"[ERROR] No se pudo crear usuario para la conversación {conversation_id}. Abortando envío.")
        return

    # 2. Crear conversación
    logic_conversation_id = create_conversation(BASE_URL, user_id, x_user_key)
    if not logic_conversation_id:
        print(f"[ERROR] No se pudo crear conversación lógica para {conversation_id}. Abortando envío.")
        return

    # 3. Enviar mensajes concatenados a la nueva conversación en el bot lógico
    response = create_message(BASE_URL, user_id, logic_conversation_id, x_user_key, texto_concatenado)
    if response:
        print(f"[DEBUG] Mensaje enviado al bot lógico: {response}")
    else:
        print(f"[ERROR] Ocurrió un problema al enviar los mensajes al bot lógico.")

    # (Opcional) Esperar para listar los mensajes y ver qué responde el bot
    time.sleep(2)  # Ajusta si necesitas más o menos tiempo
    all_messages = list_messages(BASE_URL, logic_conversation_id, x_user_key)
    for idx, msg in enumerate(all_messages, start=1):
        payload = msg.get('payload', {})
        print(f" - Respuesta {idx} del bot lógico: {payload.get('text', '')}")


# ---------------------------------------------------------------------------------
# Función que se llama cuando expira el temporizador de una conversación
# ---------------------------------------------------------------------------------
def on_timer_expired(conversation_id):
    """
    Envía el mensaje acumulado de 'conversation_id' al bot lógico y limpia el buffer.
    Esta función la ejecuta el hilo del temporizador al vencer.
    """
    global messages_buffer, timers

    with lock:
        # Recuperamos y borramos del diccionario los mensajes de esta conversación
        messages_list = messages_buffer.get(conversation_id, [])
        messages_buffer.pop(conversation_id, None)

        # Quitamos el timer de esa conversación, porque ya expiró.
        timers.pop(conversation_id, None)

    # Enviamos los mensajes al bot lógico (fuera del lock, para no bloquear)
    if messages_list:
        send_buffered_messages_to_logic(conversation_id, messages_list)


# ---------------------------------------------------------------------------------
# Función para acumular el nuevo mensaje y (re)iniciar el temporizador
# ---------------------------------------------------------------------------------
def buffer_incoming_message(conversation_id: str, preview_text: str):
    """
    Añade el preview del evento al buffer de esa conversación y reinicia el temporizador.
    """
    global messages_buffer, timers

    with lock:
        # Si no existe, creamos la lista de mensajes para la conversación
        if conversation_id not in messages_buffer:
            messages_buffer[conversation_id] = []

        # Agregamos el nuevo mensaje al buffer
        messages_buffer[conversation_id].append(preview_text)

        # Si ya había un timer corriendo para esta conversación, lo cancelamos
        if conversation_id in timers:
            timers[conversation_id].cancel()

        # Creamos un nuevo timer para esta conversación
        timer = threading.Timer(BUFFER_TIME, on_timer_expired, args=[conversation_id])
        timers[conversation_id] = timer
        timer.start()


# ---------------------------------------------------------------------------------
# Endpoint principal para recibir los eventos/mensajes
# ---------------------------------------------------------------------------------
@app.post("/recibir_mensaje")
async def endpoint_recibir_mensaje(request: Request):
    """
    Endpoint que recibe los 'events' provenientes de Botpress u otra fuente.
    Se asume que llega un JSON con la estructura mostrada en tu ejemplo.
    Extraemos 'conversationId' y 'preview' y luego los acumulamos.
    """
    try:
        data = await request.json()
        message = data.get("message", {})
        # Importante: aquí ajusta cómo extraes el conversationId y el preview,
        # dependiendo de la estructura JSON real que recibas.
        conversation_id = message.get("conversationId")
        preview = message.get("preview")

        print(f"[DEBUG] {conversation_id}: {preview}")

        # Validar si obtuvimos la información necesaria
        if not conversation_id:
            return {"status": "error", "detail": "No se encontró el conversationId en los datos."}

        if not preview:
            return {"status": "error", "detail": "No se encontró el preview (texto) en los datos."}

        # Acumular el mensaje en el buffer y reiniciar/crear el timer
        buffer_incoming_message(conversation_id, preview)

        return {"status": "ok", "detail": f"Mensaje bufferizado para conversación {conversation_id}."}

    except Exception as e:
        print(f"[ERROR] Ocurrió un problema procesando el mensaje: {e}")
        return {"status": "error", "detail": str(e)}


# ---------------------------------------------------------------------------------
# Función main (por si corres este archivo directamente)
# ---------------------------------------------------------------------------------
def main():
    print("API iniciada. Escuchando mensajes en el endpoint /recibir_mensaje...")
    print(f"Tiempo de buffer configurado en {BUFFER_TIME} segundos.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    main()
