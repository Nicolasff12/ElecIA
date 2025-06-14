import requests
import os
from src.config import logger, is_domain_allowed # Importar logger y validador
import json # Importar json para manejar las respuestas de la API




def google_custom_search(query, num_results=10):
    api_key = os.getenv("CUSTOM_SEARCH_API_KEY")
    cx_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

    if not api_key or not cx_id:
        logger.error("CUSTOM_SEARCH_API_KEY o CUSTOM_SEARCH_ENGINE_ID no configurados en .env")
        return []

    params = {
        "key": api_key,
        "cx": cx_id,
        "q": query,
        "num": num_results
        # "cr": "countryCO"  # Descomenta solo si funciona
    }

    try:
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
        logger.info(f"URL enviada: {response.url}")
        response.raise_for_status()
        search_results = response.json()

        urls = [
            item['link']
            for item in search_results.get('items', [])
            if is_domain_allowed(item['link'])
        ]

        logger.info(f"Custom Search para '{query}': {len(urls)} URLs filtradas de {len(search_results.get('items', []))} resultados.")
        return urls

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la búsqueda de Google Custom Search para '{query}': {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON de la respuesta: {e}")
        return []

"""
def google_custom_search(query, num_results=10):
    
    Realiza una búsqueda web utilizando Google Custom Search API,
    filtrando los resultados por dominios confiables y restringiendo por país (Colombia).
    ""
    api_key = os.getenv("CUSTOM_SEARCH_API_KEY") # Obtener de las variables de entorno
    cx_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

    if not api_key or not cx_id:
        logger.error("CUSTOM_SEARCH_API_KEY o CUSTOM_SEARCH_ENGINE_ID no configurados en .env")
        return []

    # 'cr=countryCO' restringe la búsqueda a resultados de Colombia.
    search_url = (
        f"https://www.googleapis.com/customsearch/v1?"
        f"key={api_key}&cx={cx_id}&q={query}&num={num_results}&cr=countryCO"
    )

    try:
        response = requests.get(search_url, timeout=15) # Añadir timeout para evitar esperas infinitas
        response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        
        search_results = response.json()
        
        # Filtrar URLs para asegurar que solo se procesen de dominios permitidos
        urls = [
            item['link'] 
            for item in search_results.get('items', []) 
            if is_domain_allowed(item['link'])
        ]
        logger.info(f"Custom Search para '{query}': Encontradas {len(urls)} URLs filtradas de {len(search_results.get('items', []))} resultados brutos.")
        return urls
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la búsqueda de Google Custom Search para '{query}': {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON de la respuesta de Custom Search para '{query}': {e}")
        return []"""