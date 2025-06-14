import google.generativeai as genai
from src.config import logger

def generate_candidates_analysis(candidates_info):
    """
    Genera un análisis general de los candidatos usando IA.
    """
    if not candidates_info:
        logger.warning("ANALYSIS: No hay candidatos para analizar.")
        return "No se encontraron candidatos para generar un análisis."

    # Armar el prompt
    candidate_summaries = []
    for c in candidates_info:
        summary = f"Nombre: {c.get('full_name', 'Desconocido')}, "
        summary += f"Partido: {c.get('political_party', 'Desconocido')}, "
        summary += f"Propuestas: {', '.join(c.get('main_proposals', [])) if c.get('main_proposals') else 'No disponibles'}"
        candidate_summaries.append(summary)
    
    prompt = (
        "A continuación te presento un conjunto de candidatos presidenciales de Colombia "
        "y un resumen de sus partidos y principales propuestas. Por favor genera un análisis general "
        "de sus enfoques, diferencias, y puntos comunes, destacando los temas clave:\n\n"
    )
    prompt += "\n".join(candidate_summaries)

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        analysis_text = response.text.strip()
        logger.info("ANALYSIS: Análisis generado correctamente.")
        return analysis_text or "La IA no devolvió un análisis."
    except Exception as e:
        logger.error(f"ANALYSIS: Error al generar el análisis: {e}")
        return "Ocurrió un error al generar el análisis."
