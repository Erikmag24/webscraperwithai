#web_scraper.py

import logging
from typing import Dict, List, Optional
from search_engines import get_search_results
from get_google_search_links import get_google_search_links
from file_processor import process_file
from audio_processor import process_audio
from link_processor import process_links

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_and_process(
    query: str,
    translations: Dict[str, str],
    numero_pagine: int = 1,
    use_ollama: bool = True,
    use_cohere: bool = False,
    use_gpt: bool = False,
    use_gemini: bool = False,
    search_engines: Optional[List[str]] = None,
    process_file_path: Optional[str] = None,
    process_audio_path: Optional[str] = None
) -> List[str]:
    output_files = {
        "scraped_texts": "files/scraped_texts.txt",
        "model_responses": "files/model_responses.txt",
        "model_output_no_link": "files/model_output_file_no_link.txt"
    }

    # Initialize output files with retry in case of IO errors
    for file_path in output_files.values():
        retry_attempts = 3
        while retry_attempts > 0:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                logging.info(f"Initialized file: {file_path}")
                break
            except IOError as e:
                retry_attempts -= 1
                logging.error(f"Failed to initialize {file_path}: {e}")
                if retry_attempts == 0:
                    logging.critical(f"Could not initialize {file_path} after multiple attempts.")
                    return []

    results = []

    if process_file_path:
        logging.info(f"Processing file: {process_file_path}")
        try:
            process_file(
                process_file_path,
                translations.items(),
                output_files["scraped_texts"],
                use_ollama,
                use_cohere,
                use_gpt,
                use_gemini,
            )
        except Exception as e:
            logging.error(f"Error processing file {process_file_path}: {e}")

    elif process_audio_path:
        logging.info(f"Processing audio file: {process_audio_path}")
        try:
            process_audio(
                process_audio_path,
                translations.items(),
                output_files["scraped_texts"],
                use_ollama,
                use_cohere,
                use_gpt,
                use_gemini,
            )
        except Exception as e:
            logging.error(f"Error processing audio file {process_audio_path}: {e}")

    else:
        for language, translation in translations.items():
            logging.info(f"Processing translation for {language.title()}: {translation}")

            if search_engines:
                for search_engine in search_engines:
                    retry_attempts = 3
                    while retry_attempts > 0:
                        try:
                            logging.info(f"Searching on {search_engine}...")
                            links = get_search_results(
                                translation,
                                search_engine,
                                numero_pagine
                            )
                            process_links(
                                links,
                                query,
                                output_files["scraped_texts"],
                                results,
                                use_ollama,
                                use_cohere,
                                use_gpt,
                                use_gemini,
                            )
                            break
                        except Exception as e:
                            retry_attempts -= 1
                            logging.error(f"Error retrieving search results from {search_engine}: {e}")
                            if retry_attempts == 0:
                                logging.critical(f"Failed to retrieve results from {search_engine} after multiple attempts.")

            else:
                retry_attempts = 3
                while retry_attempts > 0:
                    try:
                        logging.info("Using Google as fallback search engine...")
                        links = get_google_search_links(
                            translation,
                            numero_pagine
                        )
                        process_links(
                            links,
                            query,
                            output_files["scraped_texts"],
                            results,
                            use_ollama,
                            use_cohere,
                            use_gpt,
                            use_gemini,
                        )
                        break
                    except Exception as e:
                        retry_attempts -= 1
                        logging.error(f"Error retrieving search results from Google: {e}")
                        if retry_attempts == 0:
                            logging.critical("Failed to retrieve results from Google after multiple attempts.")

    logging.info("Final result: %s", results)
    return results
