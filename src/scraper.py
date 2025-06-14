import requests
from bs4 import BeautifulSoup
from src.config import logger, is_domain_allowed # Importar logger y validador

def scrape_and_extract_text(url):
    """
    Realiza web scraping en la URL dada y extrae el texto principal,
    eliminando scripts y estilos. Solo raspa dominios permitidos.
    """
    if not is_domain_allowed(url):
        logger.warning(f"SCRAPER_REJECTED: URL no permitida por dominio: {url}")
        return None

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8' # Preferir español
        }
        response = requests.get(url, headers=headers, timeout=15) # Añadir timeout
        response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Eliminar elementos de script y estilo
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        
        # Obtener todo el texto, dividir en líneas, limpiar y unificar
        lines = (line.strip() for line in soup.get_text().splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) # Doble espacio para algunos casos de separación
        text = '\n'.join(chunk for chunk in chunks if chunk) # Unir solo chunks no vacíos
        
        logger.info(f"SCRAPER_SUCCESS: Texto extraído de {url} (primeros 100 chars): {text[:100]}...")
        return text
    except requests.exceptions.HTTPError as e:
        logger.warning(f"SCRAPER_HTTP_ERROR: Error HTTP {e.response.status_code} al hacer scraping de {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"SCRAPER_CONNECTION_ERROR: Error de conexión al hacer scraping de {url}: {e}")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"SCRAPER_TIMEOUT: Tiempo de espera agotado al hacer scraping de {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"SCRAPER_UNKNOWN_ERROR: Error RequestException al hacer scraping de {url}: {e}")
        return None
    except Exception as e:
        logger.critical(f"SCRAPER_UNEXPECTED_ERROR: Error inesperado al hacer scraping de {url}: {e}")
        return None