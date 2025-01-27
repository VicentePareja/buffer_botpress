import time
import threading
from fastapi import FastAPI, Request
from botpress_talk import crear_usuario, create_conversation, create_message, list_messages

botpress_url = 'https://chat.botpress.cloud/'
hook_id = 'c89e067a-b093-4a96-88fd-e2d5ab7875be'  # ID del hook de Botpress
base_url = f'{botpress_url}{hook_id}'

# Variables globales para manejar el estado del mensaje y el temporizador
mensaje_acumulado = ""
timer = None
lock = threading.Lock()
app = FastAPI()


def send_message(base_url, mensaje):
    """Envía el mensaje acumulado a Botpress."""
    print(f"DEBUG: Enviando mensaje acumulado: {mensaje}")
    user_id, x_user_key = crear_usuario(base_url)
    conversation_id = create_conversation(base_url, user_id, x_user_key)
    create_message(base_url, user_id, conversation_id, x_user_key, mensaje)
    # Espera de 20 segundos antes de listar los mensajes
    time.sleep(20)
    all_messages = list_messages(base_url, conversation_id, x_user_key)
    for message in all_messages:
        print(f"Mensaje recibido de Botpress: {message.get('payload').get('text')}")


def enviar_mensaje_acumulado():
    """Envía el mensaje acumulado cuando el temporizador se activa."""
    global mensaje_acumulado, timer
    with lock:
        if mensaje_acumulado:
            send_message(base_url, mensaje_acumulado)
            print(f"DEBUG: Mensaje procesado y enviado: {mensaje_acumulado}")
            mensaje_acumulado = ""  # Resetear el mensaje acumulado
        timer = None


def recibir_mensaje(nuevo_mensaje):
    """Acumula mensajes y reinicia el temporizador."""
    global mensaje_acumulado, timer
    with lock:
        # Concatenar el nuevo mensaje con un salto de línea
        if mensaje_acumulado:
            mensaje_acumulado += f"\n{nuevo_mensaje}"
        else:
            mensaje_acumulado = nuevo_mensaje

        print(f"DEBUG: Mensaje acumulado actualizado: {mensaje_acumulado}")

        # Reiniciar el temporizador
        if timer is not None:
            print("DEBUG: Temporizador existente cancelado.")
            timer.cancel()

        print("DEBUG: Creando un nuevo temporizador de 15 segundos.")
        timer = threading.Timer(15.0, enviar_mensaje_acumulado)
        timer.start()


@app.post("/recibir_mensaje")
async def endpoint_recibir_mensaje(request: Request):
    """Endpoint para recibir mensajes desde Botpress."""
    try:
        data = await request.json()
        print(f"DEBUG: Datos recibidos: {data}")

        # Extraer el texto del mensaje
        nuevo_mensaje = data.get("payload", {}).get("text", "")
        preview = data.get("preview", None)

        # Debugging de los datos extraídos
        print(f"DEBUG: Nuevo mensaje extraído: {nuevo_mensaje}")
        if preview:
            print(f"DEBUG: Preview extraído: {preview}")

        if nuevo_mensaje:
            recibir_mensaje(nuevo_mensaje)
            return {"status": "Mensaje recibido y procesado"}
        else:
            print("DEBUG: El mensaje recibido está vacío o no tiene formato esperado.")
            return {"status": "Falta el mensaje en la solicitud"}
    except Exception as e:
        print(f"Error procesando el mensaje: {e}")
        return {"status": "Error procesando el mensaje", "detail": str(e)}


def main():
    print("API iniciada. Escuchando mensajes en el endpoint /recibir_mensaje...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    main()
