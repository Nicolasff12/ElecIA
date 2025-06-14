import google.generativeai as genai
import json
from google.api_core.exceptions import ResourceExhausted, InternalServerError
from src.config import logger # Importar logger

# Asegúrate de que genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
# se haga en app.py al iniciar la aplicación, ya que es global.

# Modelo de Gemini a usar (configurado en config.py si quieres que sea una variable)
GEMINI_MODEL = 'models/gemini-2.0-flash'

def call_gemini_api(prompt_parts: list):
    """
    Función auxiliar para interactuar con la API de Gemini, manejando errores comunes.
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            contents=[{
                "role": "user",
                "parts": prompt_parts
            }],
            # Aquí podrías añadir configuraciones como generation_config (temperatura, etc.)
            # o safety_settings si fuera necesario.
        )
        # Limpiar la respuesta para asegurar que sea solo JSON
        cleaned_response = response.text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response.lstrip('```json').rstrip('```')
        return cleaned_response
    except ResourceExhausted as e:
        logger.error(f"GEMINI_ERROR: Cuota de la API excedida: {e}")
        raise # Propagar el error para que el agente pueda manejarlo
    except InternalServerError as e:
        logger.error(f"GEMINI_ERROR: Error interno del servidor de Gemini: {e}")
        return None # Devuelve None para que la lógica de parseo JSON falle
    except Exception as e:
        logger.error(f"GEMINI_ERROR: Error inesperado al llamar a Gemini: {e}")
        return None

def extract_candidate_data(page_text: str):
    """
    Extrae información inicial de un candidato de un texto usando Gemini.
    Incluye una validación para asegurar que el candidato sea de Colombia.
    """
    initial_extraction_prompt = f"""
    Del siguiente texto sobre un candidato político, extrae la siguiente información y devuélvela en formato JSON.
    Es **CRUCIAL** que el candidato sea de **COLOMBIA**. Si no puedes confirmar que el candidato es de Colombia, o si el texto no menciona a Colombia o su contexto político (ej. 'Presidente de Colombia', 'Elecciones Colombia'), devuelve un JSON con 'full_name': 'null'.

    Información requerida:
    - full_name (Nombre completo del candidato)
    - political_party (Partido político actual o principal en Colombia)
    - birth_date (Fecha de nacimiento, formato YYYY-MM-DD si es posible)
    - education (Nivel de estudios o títulos universitarios más relevantes)
    - experience (Resumen conciso de experiencia política o laboral clave en Colombia)
    - main_proposals (Lista de 3 a 5 propuestas principales, cada una como una cadena corta. Si no hay propuestas, usa una lista vacía `[]`)
    - source_url (La URL de donde se extrajo la información)

    Texto a analizar:
    ---
    {page_text[:6000]} # Aumentado el límite de texto a pasar a Gemini
    ---
    DEVUELVE SOLO EL OBJETO JSON Y NADA MÁS. Asegúrate de que la salida sea un JSON válido y completo.
    """
    
    logger.info(f"LLM_PROCESSOR: Enviando texto a Gemini para extracción inicial (primeros 500 chars): {page_text[:500]}...")
    json_str = call_gemini_api([{"text": initial_extraction_prompt}])
    
    if json_str:
        try:
            extracted_data = json.loads(json_str)
            logger.info(f"LLM_PROCESSOR: Extracción inicial Gemini exitosa. Nombre: {extracted_data.get('full_name')}")
            return extracted_data
        except json.JSONDecodeError as e:
            logger.error(f"LLM_PROCESSOR_ERROR: Gemini no devolvió JSON válido en extracción inicial: {e}. Raw: {json_str[:200]}...")
            return None
    return None

def enrich_specific_field(candidate_name: str, page_text: str, field: str):
    """
    Extrae un campo específico de un texto dado sobre un candidato usando Gemini.
    """
    enrichment_prompt = f"""
    Del siguiente texto sobre {candidate_name} (candidato de Colombia), extrae específicamente la información para el campo '{field}'.
    Si la información no está presente, usa null (o una lista vacía para 'main_proposals').
    DEVUELVE SOLO UN OBJETO JSON con la clave '{field}' y su valor.

    Texto a analizar:
    ---
    {page_text[:3000]}
    ---
    """
    logger.info(f"LLM_PROCESSOR: Enviando texto a Gemini para enriquecimiento de '{field}' para {candidate_name}.")
    json_str = call_gemini_api([{"text": enrichment_prompt}])

    if json_str:
        try:
            enr_data = json.loads(json_str)
            logger.info(f"LLM_PROCESSOR: Enriquecimiento de '{field}' exitoso.")
            return enr_data.get(field)
        except json.JSONDecodeError as e:
            logger.error(f"LLM_PROCESSOR_ERROR: Gemini no devolvió JSON válido para enriquecimiento de '{field}': {e}. Raw: {json_str[:200]}...")
            return None
    return None