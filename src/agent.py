import os
from src.config import logger
from src.search import google_custom_search
from src.scraper import scrape_and_extract_text
from src.llm_processor import extract_candidate_data, enrich_specific_field, generate_ai_analysis
from src.database import save_candidate_data, get_all_candidates_from_db
from google.api_core.exceptions import ResourceExhausted

def run_ai_agent_for_data_collection(target_election: str):
    logger.info(f"AGENT: Iniciando recolección para: {target_election}")

    existing_candidates = get_all_candidates_from_db()
    collected_candidate_names = set(c['full_name'].strip().lower() for c in existing_candidates if c.get('full_name'))

    search_query = f"principales candidatos {target_election}"
    logger.info(f"AGENT: Realizando búsqueda inicial con query: '{search_query}'")
    initial_urls = google_custom_search(search_query, num_results=10)

    if not initial_urls:
        logger.warning("AGENT: No se encontraron URLs relevantes para los candidatos.")
        return existing_candidates, "No se encontraron candidatos iniciales.", None

    logger.info(f"AGENT: Encontradas {len(initial_urls)} URLs iniciales para análisis.")
    
    newly_collected_candidates = []
    max_initial_urls_to_check = 10
    target_unique_candidates = 5
    urls_processed_count = 0

    for url in initial_urls:
        if len(newly_collected_candidates) >= target_unique_candidates or urls_processed_count >= max_initial_urls_to_check:
            break

        urls_processed_count += 1
        logger.info(f"AGENT: Procesando URL inicial ({urls_processed_count}/{max_initial_urls_to_check}): {url}")
        
        page_text = scrape_and_extract_text(url)
        if not page_text:
            continue
        
        try:
            extracted_data = extract_candidate_data(page_text)
            candidate_name = extracted_data.get('full_name')
            if not candidate_name or candidate_name.lower() == 'null':
                continue

            normalized_candidate_name = candidate_name.strip().lower()
            if normalized_candidate_name in collected_candidate_names:
                continue

            enriched_candidate = extracted_data.copy()
            enriched_candidate['source_url'] = url

            fields_to_enrich = ['birth_date', 'education', 'experience', 'main_proposals']
            for field in fields_to_enrich:
                current_value = enriched_candidate.get(field)
                is_missing = not current_value or current_value == 'null' or (isinstance(current_value, list) and not current_value)
                if is_missing:
                    enriched_value = enrich_specific_field(candidate_name, page_text, field)
                    if enriched_value:
                        enriched_candidate[field] = enriched_value

            if save_candidate_data(enriched_candidate):
                newly_collected_candidates.append(enriched_candidate)
                collected_candidate_names.add(normalized_candidate_name)

        except ResourceExhausted as re:
            logger.error(f"AGENT_ERROR: Cuota de API excedida. Deteniendo recolección: {re}")
            break
        except Exception as e:
            logger.error(f"AGENT_ERROR: Error al procesar URL {url}: {e}")
            continue

    all_candidates_final = get_all_candidates_from_db()

    # --- Generar análisis IA ---
    try:
        logger.info("AGENT: Generando análisis con IA para los candidatos finales.")
        analysis_text = generate_ai_analysis(all_candidates_final)
    except Exception as e:
        logger.error(f"ANALYSIS: Error al generar el análisis: {e}")
        analysis_text = "⚠️ Ocurrió un error al generar el análisis. Intenta nuevamente más tarde."

    final_message = (
    f"Recolección de datos completada. "
    f"Se encontraron {len(all_candidates_final)} candidatos únicos de Colombia en total "
    f"({len(newly_collected_candidates)} nuevos en esta ejecución)."
)   
    logger.info(f"AGENT: {final_message}")

    for candidate in all_candidates_final:
        logger.info(
            f"Candidato Final: {candidate.get('full_name')} - "
            f"Partido: {candidate.get('political_party')} - "
            f"Propuestas: {candidate.get('main_proposals')[:2] if candidate.get('main_proposals') else 'N/A'}"
        )

    return all_candidates_final, final_message, analysis_text