import os
from flask import Flask, render_template, request
import google.generativeai as genai
from src.agent import run_ai_agent_for_data_collection
from src.config import logger, GOOGLE_API_KEY, SECRET_KEY, INITIAL_MESSAGES
from src.database import init_db, get_all_candidates_from_db # <-- NUEVAS IMPORTACIONES
from src.analysis import generate_candidates_analysis

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.error("GOOGLE_API_KEY no configurada. La funcionalidad de IA no estará disponible.")

# --- Rutas de la aplicación Flask ---
@app.route('/')
def index():
    existing_candidates = get_all_candidates_from_db()
    ia_analysis = None

    if existing_candidates:
        try:
            logger.info("AGENT: Generando análisis inicial de los candidatos guardados.")
            ia_analysis = generate_candidates_analysis(existing_candidates)
        except Exception as e:
            error_message = str(e)
            if '429' in error_message:
                logger.error("ANALYSIS: Límite de cuota alcanzado en Gemini API al iniciar la app.")
                ia_analysis = "Límite de cuota alcanzado. Por favor intenta más tarde."
            else:
                logger.error(f"ANALYSIS: Error al generar el análisis inicial: {e}")
                ia_analysis = "Ocurrió un error al generar el análisis inicial."

    return render_template(
        'index.html',
        candidatos=existing_candidates,
        message=None,
        ia_analysis=ia_analysis,
        initial_messages=INITIAL_MESSAGES
    )



@app.route('/iniciar_recoleccion', methods=['POST'])
def iniciar_recoleccion():
    target_election = request.form.get('eleccion', 'elecciones presidenciales Colombia 2026')
    candidates_info, message, _ = run_ai_agent_for_data_collection(target_election)

    # Siempre generamos un análisis de TODOS los candidatos al buscar nuevos
    all_candidates_final = get_all_candidates_from_db()
    ia_analysis = None

    if all_candidates_final:
        try:
            logger.info("AGENT: Generando análisis con IA para los candidatos finales después de búsqueda.")
            ia_analysis = generate_candidates_analysis(all_candidates_final)
        except Exception as e:
            error_message = str(e)
            if '429' in error_message:
                logger.error("ANALYSIS: Límite de cuota alcanzado en Gemini API tras la búsqueda.")
                ia_analysis = "Límite de cuota alcanzado. Por favor intenta más tarde."
            else:
                logger.error(f"ANALYSIS: Error al generar el análisis tras búsqueda: {e}")
                ia_analysis = "Ocurrió un error al generar el análisis tras la búsqueda."

    return render_template(
        'index.html',
        candidatos=all_candidates_final,
        message=message,
        ia_analysis=ia_analysis,
        initial_messages=INITIAL_MESSAGES
    )



import os

if __name__ == '__main__':
    # Inicializar la base de datos al iniciar la aplicación
    init_db() 
    
    for msg in INITIAL_MESSAGES:
        logger.info(msg)
    
    port = int(os.environ.get('PORT', 5000))  # Render asigna el puerto dinámicamente
    app.run(host='0.0.0.0', port=port, debug=False)  # ¡Escucha en todas las interfaces!
