# gemini_api.py

from typing import Optional
import requests
from config import GEMINI_API_KEY, GEMINI_API_URL

def generate_with_gemini(prompt: str, timeout: Optional[int] = 60, verbose: bool = False) -> Optional[str]:
    """
    Genera contenuto utilizzando l'API di Gemini.

    Args:
        prompt (str): Il testo di input per generare la risposta.
        timeout (Optional[int]): Tempo massimo in secondi per la richiesta.
        verbose (bool): Se True, stampa la risposta completa dell'API per il debug.

    Returns:
        Optional[str]: Il testo generato o None in caso di errore.
    """
    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': GEMINI_API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            params=params,
            json=data,
            timeout=timeout
        )
        response.raise_for_status()  # Solleva un'eccezione per codici di risposta HTTP 4xx/5xx
        result = response.json()

        # Opzionale: Stampa la risposta completa per debug
        if verbose:
            import json

        # Estrae il testo generato dalla struttura della risposta
        if 'candidates' in result:
            candidate = result['candidates'][0]
            if 'content' in candidate:
                content = candidate['content']
                if 'parts' in content:
                    generated_text = content['parts'][0].get('text', None)
                    if generated_text:
                        return generated_text
                    else:
                        print("Il campo 'text' non è presente in 'parts'.")
                        return None
                else:
                    print("Il campo 'parts' non è presente in 'content'.")
                    return None
            else:
                print("Il campo 'content' non è presente nel candidato.")
                return None
        else:
            print("Struttura della risposta non riconosciuta.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta all'API di Gemini: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Errore nell'interpretazione della risposta: {e}")
        return None

