import requests
import uuid


def crear_usuario(base_url):
    url = f'{base_url}/users'
    user_id = str(uuid.uuid4())  # Genera un ID de usuario único
    payload = {
        'id': user_id,
        'name': user_id
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx
        data = response.json()  # Convierte la respuesta JSON en un diccionario
        x_user_key = data.get('key')  # Extrae el valor de 'key' del diccionario
        if x_user_key:
            print(f'Usuario creado con éxito. ID: {user_id} y obtenido x_user_key: XXXX')
            return user_id, x_user_key
        else:
            print('Error: La respuesta no contiene la clave "key".')
            return None, None
    except requests.exceptions.HTTPError as http_err:
        print(f'Error HTTP al crear usuario: {http_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Error en la solicitud al crear usuario: {req_err}')
    except ValueError:
        print('Error: La respuesta no es un JSON válido.')
    return None, None

def create_conversation(base_url, user_id, x_user_key):
    url = f'{base_url}/conversations'
    headers = {
        'x-user-key': x_user_key
    }
    payload = {
        'userId': user_id
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print(data)
        conversation_id = data.get('conversation', {}).get('id')
        if conversation_id:
            print(f'Conversación iniciada con éxito. ID: {conversation_id}')
            return conversation_id
        else:
            print('Error: La respuesta no contiene la clave "id" de la conversación.')
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f'Error HTTP al iniciar conversación: {http_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Error en la solicitud al iniciar conversación: {req_err}')
    except ValueError:
        print('Error: La respuesta no es un JSON válido.')
    return None

def create_message(base_url, user_id, conversation_id, x_user_key, mensaje):
    url = f'{base_url}/messages'
    headers = {
        'x-user-key': x_user_key
    }
    payload = {
        "payload": { "type": "text", "text": mensaje },
        'conversationId': conversation_id
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error al enviar mensaje: {response.status_code}, {response.text}')
        return None
    
def list_messages(base_url, conversation_id, x_user_key):
    url = f'{base_url}/conversations/{conversation_id}/messages'
    headers = {
        'x-user-key': x_user_key
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        messages = data.get('messages', [])
        if messages:
            print(f'Se recuperaron {len(messages)} mensajes de la conversación {conversation_id}.')
            return messages
        else:
            print(f'No se encontraron mensajes en la conversación {conversation_id}.')
            return []
    except requests.exceptions.HTTPError as http_err:
        print(f'Error HTTP al listar mensajes: {http_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Error en la solicitud al listar mensajes: {req_err}')
    except ValueError:
        print('Error: La respuesta no es un JSON válido.')
    return []

# Función para usar el endpoint base_url/hello
def call_hello_endpoint(chat_api_url_id):
    base_url = f'https://chat.botpress.cloud/{chat_api_url_id}/hello'

    try:
        response = requests.get(base_url)
        print(f"Respuesta completa del servidor: {response.text}")
        response.raise_for_status()
        print(f"Respuesta del servidor para {chat_api_url_id}: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP al llamar a {base_url} con {chat_api_url_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Error en la solicitud para {base_url} con {chat_api_url_id}: {req_err}")
    return None