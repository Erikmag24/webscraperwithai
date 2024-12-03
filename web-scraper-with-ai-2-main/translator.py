#trsnslator.py

import logging
from deep_translator import GoogleTranslator
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def translate_text(text: str, languages: List[str]) -> Dict[str, str]:
    """
    Translate the given text into specified languages with retry for failures.

    :param text: Text to be translated.
    :param languages: List of language codes to translate into.
    :return: Dictionary with translations.
    """
    translations = {}
    for lang in languages:
        retry_attempts = 3
        while retry_attempts > 0:
            try:
                translated = GoogleTranslator(source='auto', target=lang).translate(text)
                translations[lang] = translated
                logging.info(f"Translation to {lang} successful.")
                break
            except Exception as e:
                retry_attempts -= 1
                logging.error(f"Error translating to {lang}: {e}")
                if retry_attempts == 0:
                    logging.critical(f"Failed to translate to {lang} after multiple attempts.")
    return translations

def get_available_languages() -> Dict[str, str]:
    """
    Retrieves all available languages for translation as a dictionary with logging.
    """
    try:
        translator = GoogleTranslator()
        languages = translator.get_supported_languages()
        logging.info("Retrieved available languages for translation.")
        return {lang: lang.title() for lang in languages}
    except Exception as e:
        logging.error(f"Error retrieving available languages: {e}")
        return {}
