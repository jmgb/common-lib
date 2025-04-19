from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal, Dict, Union, Tuple
import time

import logging
import json
import sys
import aiohttp
from datetime import datetime, timedelta, date, timezone

from common_lib.shared_functions import *
from ai_models import *



# Analiza cualquier tipo de informe con el system prompt que se indique como argumento y los mensajes de usuario y asistentes.
async def gpt_request(ai_model, system_prompt, user_message, user_examples, assistant_examples, logger, response_format="json_object", temperature=0, openai_client=openai_client_async, gemini_client=gemini_client_miguel, groq_client=groq_client_async):
    """
    Realiza una solicitud a un modelo de IA y devuelve la respuesta.
    
    Args:
        ai_model (str): El modelo de IA a utilizar.
        system_prompt (str): El prompt del sistema que define el comportamiento del modelo.
        user_message (str): El mensaje del usuario que contiene la consulta.
        user_examples (list): Lista de ejemplos de mensajes de usuario para few-shot learning.
        assistant_examples (list): Lista de ejemplos de respuestas del asistente para few-shot learning.
        logger: El objeto logger para registrar información.
        response_format: Formato de respuesta esperado, puede ser "None" para un chat completion sin output estructurado, "json_object" o un modelo Pydantic.
        
    Returns:
        dict: La respuesta del modelo de IA procesada.
    """
    start_time = time.perf_counter()  # Marca el inicio del tiempo

    # Inicialización
    respuesta_dict = {} 
    diff_seconds = 10
    completion = None
 
    messages = [{"role": "system", "content": system_prompt}]
    # Añadir todos los ejemplos que haya.
    for user_msg, assistant_msg in zip(user_examples, assistant_examples):
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    
    # Añadir el mensaje de usuario con la info a analizar
    messages.append({"role": "user", "content": user_message})

    max_retries  = 3        # Intentos con distintos modelos que hacemos.
    for attempt in range(max_retries):
        try:
            # SI ES UN MODELO DE OPEN AI:
            if "gpt-4" in ai_model or "o3-mini" in ai_model:
                logger.debug(f"⏳ ESPERANDO RESPUESTA DE OPENAI: {ai_model}\n")        
                # Solo añadir response_format si es json_object
                completion_params = {
                    "model": ai_model,
                    "temperature": temperature,
                    "messages": messages,
                }
                if response_format and response_format == "json_object":
                    #logger.debug("response_format: json_object")
                    completion_params["response_format"] = {"type": "json_object"}
                    completion = await openai_client.beta.chat.completions.parse(**completion_params) 

                elif response_format: # Si es un modelo de Pydantic
                    #logger.debug(f"response_format: Pydantic model")
                    completion_params["response_format"] = response_format
                    completion = await openai_client.beta.chat.completions.parse(**completion_params) 

                else: #Respuesta de texto por defecto. No hace falta especificarlo
                    #logger.debug(f"response_format: texto")
                    completion_params["response_format"] = {"type": "text"}  
                    completion = await openai_client.chat.completions.create(**completion_params)
                    
                respuesta = completion.choices[0].message.content
                json_response_text = respuesta  # Obtener el texto de la respuesta


            # Si es un modelo de google, y no de OpenRouter lo usamos directamente. 
            elif "gemini" in ai_model and "google/gemini" not in ai_model: 
                logger.debug(f"⏳ ESPERANDO RESPUESTA DE GEMINI: {ai_model}\n")                
                contents = [
                    user_message
                ]
                
                if response_format == "json_object" or not response_format:
                    #logger.debug(f"response_format: {response_format}")
                    completion = await gemini_client.aio.models.generate_content(
                        model=ai_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            system_instruction=system_prompt
                            )  
                    )

                else:
                    #logger.debug(f"response_format: Pydantic model")
                    completion = await gemini_client.aio.models.generate_content(
                        model=ai_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            system_instruction=system_prompt,
                            response_mime_type='application/json',
                            response_schema=response_format
                            )  
                    )

                respuesta = completion
                json_response_text = respuesta.text
            

            # SI ES UN MODELO EJECUTADO POR GROQ:
            elif ai_model in groq_models: 
                logger.debug(f"⏳ ESPERANDO RESPUESTA DE GROQ: {ai_model}\n")

                # Solo añadir response_format si es json_object
                completion_params = {
                    "model": ai_model,
                    "temperature": temperature,
                    "messages": messages,
                }
                if response_format and response_format == "json_object":
                    #logger.debug("response_format: json_object")
                    completion_params["response_format"] = {"type": "json_object"}
                    completion = await groq_client.beta.chat.completions.parse(**completion_params) 

                elif response_format: # Si es un modelo de Pydantic
                    #logger.debug(f"response_format: Pydantic model")
                    completion_params["response_format"] = {
                        "type": "json_object",
                        "strict": True,            
                        "json_schema": convert_schema(response_format)
                    }
                    completion = await groq_client.beta.chat.completions.parse(**completion_params) 

                else: #Respuesta de texto por defecto. No hace falta especificarlo
                    completion_params["response_format"] = {"type": "text"}  
                    completion = await groq_client.chat.completions.create(**completion_params)
                    

                respuesta = completion.choices[0].message.content
                json_response_text = respuesta  # Obtener el texto de la respuesta

            # SI NO ES UN MODELO DE OPENAI ni de Google, ENTONCES USAMOS OPEN_ROUTER:
            else: 
                logger.debug(f"⏳ ESPERANDO RESPUESTA DE OPENROUTER {ai_model}\n")

                completion_params = {
                    "model": ai_model,
                    "temperature": temperature,
                    "messages": messages,
                    "provider": {
                        "order": ["Groq", "SambaNova", "Parasail"],
                        "sort": "throughput"
                    }
                }

                if response_format and response_format == "json_object":
                    #logger.debug("response_format: json_object")
                    pass
                
                elif response_format: # Si es un modelo de Pydantic
                    #logger.debug(f"response_format: Pydantic model")
                    completion_params["response_format"] = {
                        "type": "json_schema",
                        "strict": True,
                        "json_schema": convert_schema(response_format)
                        }
                else: 
                    completion_params["response_format"] = {"type": "text"}  
                    
                async with aiohttp.ClientSession() as session:
                    async with session.post(open_router_url, json=completion_params, headers=open_router_headers) as response:
                        completion = await response.json()

                #logger.debug(completion_params)
                #logger.debug("--")
                #logger.debug(completion)
                #logger.debug("--")
                json_response_text = completion["choices"][0]["message"]["content"] # Obtener el texto de la respuesta


            # PROCESAMOS LA RESPUESTA POR CUALQUIERA DE LOS CAMINOS ANTERIORES: 
            # Re-formateo por si la respuesta trajera caracteres extraños que rompan json.load

            # Extraer el JSON entre la primera '{' y la última '}'
            start_idx = json_response_text.find('{')
            end_idx = json_response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == -1:
                # Manejar el caso donde no se encuentre contenido JSON, por ejemplo:
                #logger.debug("La respuesta era solo de texto, no había un JSON con {}. Lo creamos ahora")
                respuesta_dict = {json_response_text}
                mensaje_aviso = f"⚠️ REVISAR: {respuesta_dict}\n"
                logger.warning(mensaje_aviso)
                enviar_mensaje_telegram(mensaje_aviso)

            else:
                json_str = json_response_text[start_idx:end_idx]
                respuesta_dict = json.loads(json_str)

            break  # Salir del ciclo de reintentos si la solicitud es exitosa

        except TimeoutError as te:
            logger.error(f"Timeout error: {te}")
            ai_model = cambiar_modelo_ia(ai_model, logger)
            mensaje_enviar = f"🚨 Timeout en gpt_request con {ai_model}: {te}\n\nReintentando... ({attempt + 1}/{max_retries})\n"
            logger.error(mensaje_enviar)
            continue
        
        except Exception as e:
            logger.error(str(e))
            logger.debug(f"completion: {completion}\n")

            # Extraer información de error desde el atributo error del objeto completion
            error_info = getattr(completion, 'error', None)
            error_msg = error_info.get("message", "No se proporcionó mensaje de error") if error_info else str(e)
            headers = error_info.get("metadata", {}).get("headers", {}) if error_info else {}
            x_rate_limit_reset = headers.get("X-RateLimit-Reset")

            # Definir mensaje especial si es "Rate limit exceeded"
            if "Rate limit exceeded" in error_msg or "check quota" in error_msg:
                if x_rate_limit_reset:
                    try:
                        # Convertir el timestamp de milisegundos a segundos
                        reset_timestamp = int(x_rate_limit_reset) / 1000
                        # Obtener el timestamp actual
                        now_timestamp = datetime.datetime.now().timestamp()
                        # Calcular la diferencia en segundos
                        diff_seconds = reset_timestamp - now_timestamp
                        if diff_seconds < 0:
                            diff_seconds = 0
                        # Convertir a horas y minutos
                        hours = int(diff_seconds // 3600)
                        minutes = int((diff_seconds % 3600) // 60)
                        error_detail = (f"Rate limit exceeded. Por favor, espera "
                                        f"{hours} hora{'s' if hours != 1 else ''} y "
                                        f"{minutes} minuto{'s' if minutes != 1 else ''} para el reset.")
                    except Exception as e:
                        error_detail = "Rate limit exceeded. No se pudo calcular el tiempo de espera."
                else:
                    error_detail = "Rate limit exceeded. No se proporcionó el tiempo de reset."
            else:
                error_detail = error_msg
        
            mensaje_enviar = f"⚠️ Warning en gpt_request con {ai_model}: {error_detail}\n\nReintentando... ({attempt + 1}/{max_retries})\n"
            logger.warning(mensaje_enviar)

            # Cambiar de modelo de forma global y actualizar la variable para el siguiente intento
            ai_model = cambiar_modelo_ia(ai_model, logger)

    if completion is None:
        mensaje_error = f"🚨 No se pudo obtener una respuesta de {ai_model} después de {max_retries} intentos.\n"
        logger.error(mensaje_error)
        enviar_mensaje_telegram(mensaje_error) 
        respuesta_dict = {"error": mensaje_error}


    execution_time_in_seconds = int(round(time.perf_counter() - start_time))
    str_tiempo_ejecucion = f"{ai_model}\nTime: {execution_time_in_seconds} seconds.\n"

    # Añadir el tiempo de ejecución al diccionario de respuesta
    respuesta_dict['tiempo_ejecucion'] = str_tiempo_ejecucion
    #logger.debug(json.dumps(respuesta_dict, indent=4, ensure_ascii=False))
        
    return respuesta_dict



def cambiar_modelo_ia(ai_model, logger):
    
    if ai_model == gemini_flash:
        nuevo_modelo = gpt_4_1_nano

    elif ai_model == gpt_4_1_nano:
        nuevo_modelo = gpt_4_mini

    elif ai_model == gpt_4_1_mini:
        nuevo_modelo = gemini_pro_2_5

    elif ai_model == gpt_4_1:
        nuevo_modelo = gemini_pro_2_5

    elif ai_model == llama4_scout_groq:
        nuevo_modelo = gpt_4_1_nano

    elif ai_model == llama4_maverick_groq:
        nuevo_modelo = gpt_4_1_mini

    elif ai_model == gemini_pro_2_5:
        nuevo_modelo = gemini_pro_2_0

    elif ai_model == gemini_pro_2_0:
        nuevo_modelo = gpt_4

    elif ai_model == gemini_flash_2_0_openrouter:
        nuevo_modelo = gemini_pro_2_0

    elif ai_model == deep_seek_v3_openrouter_free:
        nuevo_modelo = gemini_pro_2_5

    elif ai_model == deep_seek_r1_openrouter:
        nuevo_modelo = gemini_pro_2_5

    elif ai_model == gpt_4:
        nuevo_modelo =  gemini_pro_2_0 # Alterna a GEMINI 2.0 PRO

    elif ai_model == gpt_4_mini:
        nuevo_modelo = gemini_pro_2_0 # Alterna a GEMINI 2.0 PRO
    else:
        nuevo_modelo = ai_model



    if nuevo_modelo == ai_model:
        mensaje_enviar = f"🚨 Error - El modelo actual '{ai_model}' ha fallado y no está en la lista para ser cambiado por otro.\n"
    else: 
        mensaje_enviar = f"Cambiando modelo de IA de {ai_model} a {nuevo_modelo}\n"

    logger.warning(mensaje_enviar)
    enviar_mensaje_telegram(mensaje_enviar)

    return nuevo_modelo




def convert_schema(schema):
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_json_schema()  # Para Pydantic v2
        # return schema.schema()           # Si usas Pydantic v1
    return schema
