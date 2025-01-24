import time
from botpress_talk import crear_usuario, create_conversation, create_message, list_messages, call_hello_endpoint

botpress_url = 'https://chat.botpress.cloud/'
hook_id = 'c89e067a-b093-4a96-88fd-e2d5ab7875be'  # ID del hook de Botpress
base_url = f'{botpress_url}{hook_id}'


def main():

    # 1. esperar por mensaje
    # 2. recibirmensaje y crear timer de 15 segundos
    # 3. recibir mensaje, concatenar y repetir dos.

    mensaje: str = "Holaaa heroku"
    user_id, x_user_key = crear_usuario(base_url)
    conversation_id = create_conversation(base_url, user_id, x_user_key)
    create_message(base_url, user_id, conversation_id, x_user_key, mensaje)
    # Espera de 15 segundos antes de listar los mensajes
    time.sleep(15)  # Pausa de 15 segundos
    all_messages = list_messages(base_url, conversation_id, x_user_key)
    for message in all_messages:
        print(f"Mensaje: {message.get('payload').get('text')}\n")

main()