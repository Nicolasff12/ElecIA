import os
from src.config import logger
from src.search import google_custom_search
from src.scraper import scrape_and_extract_text
from src.llm_processor import extract_candidate_data, enrich_specific_field
from src.database import save_candidate_data, get_all_candidates_from_db
from google.api_core.exceptions import ResourceExhausted

def run_ai_agent_for_data_collection(target_election: str):
    """
    Orquesta la recolección de datos de candidatos presidenciales de Colombia.
    """
    logger.info(f"AGENT: Iniciando recolección para: {target_election}")

    existing_candidates = get_all_candidates_from_db()
    collected_candidate_names = set(c['full_name'].strip().lower() for c in existing_candidates if c.get('full_name'))
    
    # Paso 1: Búsqueda inicial de URLs relevantes
    # Consulta simplificada para evitar errores 400
    """search_query = f"candidatos {target_election} Colombia"
    logger.info(f"AGENT: Realizando búsqueda inicial con query: '{search_query}'")
    initial_urls = google_custom_search(search_query, num_results=15)"""
    search_query = f"principales candidatos {target_election}"
    logger.info(f"AGENT: Realizando búsqueda inicial con query: '{search_query}'")
    initial_urls = google_custom_search(search_query, num_results=10)

    if not initial_urls:
        logger.warning("AGENT: No se encontraron URLs relevantes para los candidatos.")
        return existing_candidates, "No se encontraron candidatos iniciales."

    logger.info(f"AGENT: Encontradas {len(initial_urls)} URLs iniciales para análisis.")
    
    newly_collected_candidates = []

    max_initial_urls_to_check = 10
    target_unique_candidates = 5

    urls_processed_count = 0

    for url in initial_urls:
        if len(newly_collected_candidates) >= target_unique_candidates or urls_processed_count >= max_initial_urls_to_check:
            logger.info(f"AGENT: Alcanzado objetivo de candidatos únicos en esta ejecución ({len(newly_collected_candidates)}) o límite de URLs procesadas ({urls_processed_count}). Deteniendo.")
            break
        
        urls_processed_count += 1
        logger.info(f"AGENT: Procesando URL inicial ({urls_processed_count}/{max_initial_urls_to_check}): {url}")
        
        page_text = scrape_and_extract_text(url)

        if not page_text:
            logger.warning(f"AGENT: No se pudo extraer texto de {url}. Saltando.")
            continue
        
        try:
            extracted_data = extract_candidate_data(page_text)

            if not extracted_data or extracted_data.get('full_name', '').lower() == 'null':
                logger.info(f"AGENT: Candidato de {url} no es de Colombia o no se pudo determinar su nacionalidad/nombre. Descartando.")
                continue

            candidate_name = extracted_data.get('full_name')
            normalized_candidate_name = candidate_name.strip().lower()

            if normalized_candidate_name in collected_candidate_names:
                logger.info(f"AGENT: Candidato '{candidate_name}' ya existe en la DB o ya se recopiló en esta ejecución. Saltando.")
                continue
            
            logger.info(f"AGENT: Nuevo candidato '{candidate_name}' detectado. Iniciando enriquecimiento.")
            
            enriched_candidate = extracted_data.copy()
            enriched_candidate['source_url'] = url

            fields_to_enrich = ['birth_date', 'education', 'experience', 'main_proposals']
            for field in fields_to_enrich:
                is_missing = False
                current_value = enriched_candidate.get(field)
                if current_value is None or str(current_value).lower() == 'null' or (isinstance(current_value, list) and not current_value):
                    is_missing = True
                
                if is_missing:
                    logger.info(f"AGENT: Enriqueciendo campo '{field}' para {candidate_name}.")
                    # Aquí el enriquecimiento se hace con el texto ya raspado o con nuevas búsquedas más específicas
                    # para ese campo (las cuales también usarán cr=countryCO en search.py)
                    enriched_value = enrich_specific_field(candidate_name, page_text, field)
                    if enriched_value is not None and (field != 'main_proposals' or (isinstance(enriched_value, list) and enriched_value)):
                        enriched_candidate[field] = enriched_value
                        logger.info(f"AGENT: Campo '{field}' de {candidate_name} enriquecido con valor: {enriched_value}")
                    else:
                        logger.info(f"AGENT: No se pudo enriquecer '{field}' para {candidate_name} con valor útil.")
            
            if save_candidate_data(enriched_candidate):
                newly_collected_candidates.append(enriched_candidate)
                collected_candidate_names.add(normalized_candidate_name)
                logger.info(f"AGENT: Candidato '{candidate_name}' añadido y guardado en DB. Total nuevos: {len(newly_collected_candidates)}.")
            else:
                logger.error(f"AGENT: Falló el guardado del candidato '{candidate_name}' en la DB. No se añadirá a la lista de esta ejecución.")


        except ResourceExhausted as re:
            logger.error(f"AGENT_ERROR: Cuota de API excedida. Deteniendo recolección: {re}")
            break
        except Exception as e:
            logger.error(f"AGENT_ERROR: Error al procesar URL {url}: {e}")
            continue

    all_candidates_final = get_all_candidates_from_db()
    final_message = f"Recolección de datos completada. Se encontraron {len(all_candidates_final)} candidatos únicos de Colombia en total ({len(newly_collected_candidates)} nuevos en esta ejecución)."
    logger.info(f"AGENT: {final_message}")
    
    for candidate in all_candidates_final: # Cambiado a all_candidates_final para mostrar todos
        logger.info(f"Candidato Final: {candidate.get('full_name')} - Partido: {candidate.get('political_party')} - Propuestas: {candidate.get('main_proposals')[:2] if candidate.get('main_proposals') else 'N/A'}")

    return all_candidates_final, final_message