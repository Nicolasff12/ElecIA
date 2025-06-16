import psycopg2
from psycopg2 import Error
from psycopg2.extras import Json
from src.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, logger
import json

def get_db_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode='verify-full'
        )
        logger.info("DATABASE: Conexión a la base de datos establecida.")
        return conn
    except Error as e:
        logger.critical(f"DATABASE_ERROR: Error al conectar a la base de datos: {e}")
        return None

def close_db_connection(conn):
    """Cierra la conexión a la base de datos."""
    if conn:
        conn.close()
        logger.info("DATABASE: Conexión a la base de datos cerrada.")

def init_db():
    """
    Inicializa la base de datos creando la tabla de candidatos si no existe.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Usamos TEXT para 'proposals' y 'experience' y 'education' por la variabilidad de la longitud.
            # Podemos usar JSONB para 'proposals' si queremos hacer consultas más complejas sobre ellas.
            # Para 'main_proposals' como lista de cadenas, JSONB es ideal.
            create_table_query = """
            CREATE TABLE IF NOT EXISTS candidates (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(255) UNIQUE NOT NULL,
                political_party VARCHAR(255),
                birth_date VARCHAR(50), -- Mantener como VARCHAR por el formato y la posible ausencia
                education TEXT,
                experience TEXT,
                main_proposals JSONB, -- Usar JSONB para almacenar listas de Python
                cv_link TEXT,
                alliances JSONB, -- Si planeas añadir este campo, JSONB es bueno para listas
                source_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            logger.info("DATABASE: Tabla 'candidates' verificada/creada exitosamente.")
        except Error as e:
            logger.critical(f"DATABASE_ERROR: Error al inicializar la base de datos: {e}")
            conn.rollback() # Revertir si hay un error
        finally:
            close_db_connection(conn)

def save_candidate_data(candidate_data: dict):
    """
    Guarda los datos de un candidato en la base de datos.
    Actualiza si el candidato ya existe por nombre completo.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Convertir listas a JSON si son main_proposals o alliances
            main_proposals_json = Json(candidate_data.get('main_proposals')) if candidate_data.get('main_proposals') else Json([])
            alliances_json = Json(candidate_data.get('alliances')) if candidate_data.get('alliances') else Json([])

            upsert_query = """
            INSERT INTO candidates (full_name, political_party, birth_date, education, experience, main_proposals, cv_link, alliances, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (full_name) DO UPDATE SET
                political_party = EXCLUDED.political_party,
                birth_date = EXCLUDED.birth_date,
                education = EXCLUDED.education,
                experience = EXCLUDED.experience,
                main_proposals = EXCLUDED.main_proposals,
                cv_link = EXCLUDED.cv_link,
                alliances = EXCLUDED.alliances,
                source_url = EXCLUDED.source_url,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id;
            """
            cursor.execute(upsert_query, (
                candidate_data.get('full_name'),
                candidate_data.get('political_party'),
                candidate_data.get('birth_date'),
                candidate_data.get('education'),
                candidate_data.get('experience'),
                main_proposals_json,
                candidate_data.get('cv_link'),
                alliances_json,
                candidate_data.get('source_url')
            ))
            candidate_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"DATABASE: Candidato '{candidate_data.get('full_name')}' guardado/actualizado con ID: {candidate_id}")
            return candidate_id
        except Error as e:
            logger.error(f"DATABASE_ERROR: Error al guardar candidato '{candidate_data.get('full_name')}': {e}")
            conn.rollback()
            return None
        finally:
            close_db_connection(conn)

def get_all_candidates_from_db():
    """
    Recupera todos los candidatos de la base de datos.
    """
    conn = get_db_connection()
    candidates = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, political_party, birth_date, education, experience, main_proposals, cv_link, alliances, source_url FROM candidates ORDER BY full_name;")
            rows = cursor.fetchall()
            for row in rows:
                candidate = {
                    'full_name': row[0],
                    'political_party': row[1],
                    'birth_date': row[2],
                    'education': row[3],
                    'experience': row[4],
                    'main_proposals': row[5], # JSONB se carga como lista/dicc de Python
                    'cv_link': row[6],
                    'alliances': row[7], # JSONB se carga como lista/dicc de Python
                    'source_url': row[8]
                }
                candidates.append(candidate)
            logger.info(f"DATABASE: Recuperados {len(candidates)} candidatos de la DB.")
        except Error as e:
            logger.error(f"DATABASE_ERROR: Error al obtener candidatos de la DB: {e}")
        finally:
            close_db_connection(conn)
    return candidates
