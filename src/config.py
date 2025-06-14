import os
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse

load_dotenv()

# --- Configuración de la aplicación ---
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')

# --- Configuración de APIs ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CUSTOM_SEARCH_API_KEY = os.getenv('CUSTOM_SEARCH_API_KEY')
CUSTOM_SEARCH_ENGINE_ID = os.getenv('CUSTOM_SEARCH_ENGINE_ID')

# --- Configuración de PostgreSQL ---
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AgenteElecciones')

# --- Dominios permitidos para scraping ---
ALLOWED_DOMAINS = [
     'eltiempo.com',
    'elespectador.com',
    'semana.com',
    'caracol.com.co',
    'rcnradio.com',
    'noticiasrcn.com',
    'bluradio.com',
    'infobae.com',
    # puedes dejar oficiales también si quieres
    'registraduria.gov.co',
    'cne.gov.co',
]

def is_domain_allowed(url):
    """Verifica si el dominio de la URL está en la lista de dominios permitidos."""
    try:
        domain = urlparse(url).netloc
        # Corregido: Usar ALLOWED_DOMAINS en lugar de ALLOWED_DOMBNS
        return any(domain.endswith(allowed_domain) for allowed_domain in ALLOWED_DOMAINS)
    except Exception as e:
        logger.error(f"Error al parsear dominio para {url}: {e}")
        return False

# Mensajes informativos
INITIAL_MESSAGES = [
    "⚠️ Asegúrate de cumplir las leyes de privacidad y uso de datos en Colombia.",
    "🏛️ Este software busca únicamente promover transparencia informativa.",
    "La recolección de datos puede tardar unos minutos. Por favor, sé paciente."
]