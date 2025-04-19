

import re
import requests
import json
import time
import os
import logging
import asyncio
from dotenv import load_dotenv
from google.genai.types import HttpOptions
from google import genai
from google.genai import types
from openai import OpenAI, AsyncOpenAI

DEBUG_MODE = True

# Carga las variables de entorno del archivo .env en el mismo directorio que el script
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
SOFIA_OPENAI_API_KEY = os.getenv('SOFIA_OPENAI_API_KEY')

INFORMA_API_USERNAME = os.getenv('INFORMA_API_USERNAME')
INFORMA_API_PASSWORD = os.getenv('INFORMA_API_PASSWORD')
INFORMA_API_URL = os.getenv('INFORMA_API_URL')

GEMINI_API_KEY_JESUS = os.getenv("GEMINI_API_KEY_JESUS")
GEMINI_API_KEY_MIGUEL = os.getenv("GEMINI_API_KEY_MIGUEL")

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

ZOHO_API_KEY = os.getenv("ZOHO_API_KEY")

# Telegram:
telegram_chat_id_jesus = "754280831"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

llm_timeout = 120

# Crear una instancia del cliente GEMINI
gemini_client_jesus = genai.Client(
    api_key=GEMINI_API_KEY_JESUS,
    http_options=HttpOptions(timeout=llm_timeout*1000)  #Timeout en ms
)
gemini_client_miguel = genai.Client(
    api_key=GEMINI_API_KEY_MIGUEL,
    http_options=HttpOptions(timeout=llm_timeout*1000)  #Timeout en ms
)

open_router_client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=OPENROUTER_API_KEY,
    timeout=llm_timeout,
)
open_router_client_async = AsyncOpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=OPENROUTER_API_KEY,
    timeout=llm_timeout,
)

open_router_url = "https://openrouter.ai/api/v1/chat/completions"
open_router_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
    timeout=llm_timeout
)
groq_client_async = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
    timeout=llm_timeout
)


# gets API Key from environment variable OPENAI_API_KEY
openai_client = OpenAI(
    api_key=OPENAI_API_KEY, 
    timeout=llm_timeout
)
openai_client_async = AsyncOpenAI(
    api_key=OPENAI_API_KEY, 
    timeout=llm_timeout
)



# Envía un mensaje al canal de Telegram:
def enviar_mensaje_telegram(mensaje, chat_id=telegram_chat_id_jesus, referencia="", max_retries=2, retry_count=0, max_recursive_retries=3):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    telegram_headers = {'Content-Type': 'application/json'}  # Encabezado para indicar que se envía JSON

    mensaje_escapado = escapar_caracteres(mensaje)  # Escapa caracteres seleccionados como: " ' &

    # Telegram admite un máximo de 4096 caracteres por mensaje.
    longitud_max_mensaje = 3500  # Longitud máxima del mensaje para dejar margen a URLs y otros imprevistos.

    # Dividir el mensaje si es más largo que la longitud máxima definida para evitar el error del API
    mensajes = [mensaje_escapado[i:i+longitud_max_mensaje] for i in range(0, len(mensaje_escapado), longitud_max_mensaje)]

    # Añadir "Continue..." al final de cada parte excepto la última
    for i in range(len(mensajes) - 1):
        mensajes[i] += "\n\n<b>Continues...</b>"

    for mensaje_parte in mensajes:
        data = json.dumps({  # Codifica los datos como JSON
            'chat_id': chat_id,
            'text': mensaje_parte,
            'parse_mode': 'HTML',  # Markdown
            'disable_web_page_preview': True  # True si no quieres una vista previa del enlace
        })

        response_telegram = None  # Inicializar response_telegram antes del try

        for attempt in range(max_retries):
            try:
                response_telegram = requests.post(url, headers=telegram_headers, data=data, timeout=10)
                response_telegram.raise_for_status()
                if response_telegram.status_code == 200:
                    # Mensaje enviado con éxito
                    break
            except requests.exceptions.HTTPError as e:
                if response_telegram is not None and response_telegram.status_code == 429:
                    # Captura el error 429 y reintenta después de 10 segundos
                    if retry_count < max_recursive_retries:
                        print(f"{referencia} - 🚨 Error 429: Too Many Requests. Esperando 10 segundos antes de reintentar.")
                        time.sleep(10)
                        # Llama a la función nuevamente de forma recursiva
                        enviar_mensaje_telegram(mensaje, chat_id, referencia, max_retries, retry_count + 1, max_recursive_retries)
                        return  # Sal del bucle actual para evitar enviar mensajes duplicados
                    else:
                        print(f"{referencia} - 🚨 Máximo número de reintentos alcanzado después de {retry_count} intentos debido al error 429.")
                        break
                else:
                    print(f"{referencia} - 🚨 Error HTTP: {e}. Intento {attempt + 1} de {max_retries}.")
                    time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f"{referencia} - 🚨 Error al enviar mensaje a Telegram: {e}. Intento {attempt + 1} de {max_retries}.")
                time.sleep(5)
        else:
            # Si todos los intentos fallan, maneja el error
            if response_telegram is not None:
                try:
                    # Intenta imprimir el mensaje de error de la respuesta de la API
                    error_message = response_telegram.json().get('description', 'No hay descripción del error.')
                    mensaje_error = f"{referencia} - 🚨 Error al enviar mensaje a Telegram: {error_message}"
                    print(mensaje_error + "\n⚠️ Mensaje que ha dado el problema:\n" + mensaje_parte + "\nFin del mensaje con error.")
                
                except ValueError:
                    # Si la respuesta no contiene JSON válido, imprime el texto de la respuesta
                    mensaje_error = f"{referencia} - 🚨 Error al enviar mensaje a Telegram después de {max_retries} intentos: {response_telegram.text}\n"
                    
                    print(mensaje_error + "\n⚠️ Mensaje que ha dado el problema:\n" + mensaje_parte + "\nFin del mensaje con error.")
                    enviar_mensaje_telegram(f"🚨 Error al mandar el siguiente mensaje en Telegram: {mensaje[:150]}")

            else:
                # Si la respuesta es nula debido a fallos de conexión en todos los intentos
                mensaje_error = f"{referencia} - 🚨 Error al enviar mensaje a Telegram: Todos los intentos fallaron. No se pudo establecer conexión."
                print(mensaje_error + "\n⚠️ Mensaje que ha dado el problema:\n" + mensaje_parte + "\nFin del mensaje con error.")
                enviar_mensaje_telegram(f"🚨 Error al mandar el siguiente mensaje en Telegram: {mensaje[:150]}")
        
        # Delay para evitar exceder el límite de tasa de Telegram
        time.sleep(1)

    return None



# Necesario para que no se rompa el mensaje en telegram cuando hay algún simbolo no escapado: 
def escapar_caracteres(texto):
    # Primero, escapa los caracteres especiales que podrían causar problemas
    texto = texto.replace('&', '&amp;')
    texto = texto.replace('"', '&quot;')
    #texto = texto.replace("'", '&apos;')
    # Luego, restablece las etiquetas HTML comunes para que se interpreten correctamente
    texto = re.sub(r'&lt;(\/?b)&gt;', r'<\1>', texto)
    texto = re.sub(r'&lt;(\/?i)&gt;', r'<\1>', texto)
    texto = re.sub(r'&lt;(\/?u)&gt;', r'<\1>', texto)
    texto = re.sub(r'&lt;(\/?a\s+href=.*?)&gt;', r'<\1>', texto)
    return texto




def setup_logger(name: str, log_file: str) -> logging.Logger:
    """Configura el logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = logging.DEBUG if DEBUG_MODE else logging.INFO
        logger.setLevel(level)

        # Configurar el manejador de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

        # Configurar el manejador de archivo
        if not os.path.exists(log_file):
            open(log_file, 'a', encoding='utf-8').close()
        os.chmod(log_file, 0o666)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Añadir manejadores al logger
        logger.addHandler(file_handler)

        # Suprimir mensajes DEBUG de módulos externos
        for module in ["httpx", "httpcore", "urllib3", "asyncio", "watchfiles", "uvicorn", "uvicorn.error", "uvicorn.access", "openai"]:
            logging.getLogger(module).setLevel(logging.WARNING)

    return logger