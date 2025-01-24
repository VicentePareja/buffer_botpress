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
    user_id, x_user_key = crear_usuario(base_url)
    conversation_id = create_conversation(base_url, user_id, x_user_key)
    create_message(base_url, user_id, conversation_id, x_user_key, mensaje)
    # Espera de 15 segundos antes de listar los mensajes
    time.sleep(15)  # Pausa de 15 segundos
    all_messages = list_messages(base_url, conversation_id, x_user_key)
    for message in all_messages:
        print(f"Mensaje: {message.get('payload').get('text')}\n")

def enviar_mensaje_acumulado():
    global mensaje_acumulado, timer
    with lock:
        if mensaje_acumulado:
            send_message(base_url, mensaje_acumulado)
            print(f"Mensaje enviado: \n{mensaje_acumulado}")
            mensaje_acumulado = ""  # Resetear el mensaje acumulado
        timer = None

def recibir_mensaje(nuevo_mensaje):
    global mensaje_acumulado, timer
    with lock:
        # Concatenar el nuevo mensaje con un salto de línea
        if mensaje_acumulado:
            mensaje_acumulado += f"\n{nuevo_mensaje}"
        else:
            mensaje_acumulado = nuevo_mensaje

        # Reiniciar el temporizador
        if timer is not None:
            timer.cancel()

        # Crear un nuevo temporizador
        timer = threading.Timer(30.0, enviar_mensaje_acumulado)
        timer.start()

@app.post("/recibir_mensaje")
async def endpoint_recibir_mensaje(request: Request):
    data = await request.json()
    nuevo_mensaje = data.get("mensaje", "")
    if nuevo_mensaje:
        recibir_mensaje(nuevo_mensaje)
        return {"status": "Mensaje recibido y procesado"}
    else:
        return {"status": "Falta el mensaje en la solicitud"}

def main():
    print("API iniciada. Escuchando mensajes en el endpoint /recibir_mensaje...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)