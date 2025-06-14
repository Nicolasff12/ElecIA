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
    """
    Ruta principal que muestra el formulario de inicio.
    Carga y muestra los candidatos ya existentes en la base de datos.
    """
    # Cargar candidatos existentes al cargar la página por primera vez
    existing_candidates = get_all_candidates_from_db()
    
    return render_template('index.html', candidatos=existing_candidates, message=None, initial_messages=INITIAL_MESSAGES)



@app.route('/iniciar_recoleccion', methods=['POST'])
def iniciar_recoleccion():
    """
    Ruta para iniciar la recolección de datos basada en la elección seleccionada.
    """
    target_election = request.form.get('eleccion', 'e   lecciones presidenciales Colombia 2026')
    logger.info(f"APP: Solicitud recibida para '{target_election}'.")
    
    candidates_info, message = run_ai_agent_for_data_collection(target_election)
    analysis = generate_candidates_analysis(candidates_info)
    

    return render_template(
    'index.html',
    candidatos=candidates_info,
    message=message,
    initial_messages=INITIAL_MESSAGES,
    analysis=analysis
)


if __name__ == '__main__':
    # Inicializar la base de datos al iniciar la aplicación
    init_db() 
    
    for msg in INITIAL_MESSAGES:
        logger.info(msg)
    
    app.run(debug=True)