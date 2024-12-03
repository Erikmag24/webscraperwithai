#cohere.py

import cohere
import time
import logging
from httpx import RemoteProtocolError, ReadTimeout
from typing import Optional, List
from config import COHERE_API_KEY, COHERE_MODEL
def generate_with_cohere(
    prompt: str,
    temperature: float = 0.3,
    retries: int = 3,
    timeout: int = 60
) -> Optional[str]:
    """
    Generate a response using the Cohere API with retry mechanism and improved error handling.
    
    Args:
        prompt (str): The input prompt for the Cohere model.
        temperature (float): Controls randomness in generation. Default is 0.3.
        retries (int): Number of retry attempts in case of errors. Default is 3.
        timeout (int): Timeout for the API request in seconds. Default is 60.
    
    Returns:
        Optional[str]: The generated response, or None if all retries fail.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    co = cohere.Client(COHERE_API_KEY, timeout=timeout)
    
    for attempt in range(retries):
        try:
            stream = co.chat_stream(
                model=COHERE_MODEL,
                message=prompt,
                temperature=temperature,
                chat_history=[],
                prompt_truncation='AUTO',
                connectors=[{"id": "web-search"}]
            )
            
            response_parts: List[str] = []
            for event in stream:
                if event.event_type == "text-generation":
                    response_parts.append(event.text)
            
            response = "".join(response_parts)
            logger.info(f"Successfully generated response on attempt {attempt + 1}")
            return response
            
        except (RemoteProtocolError, ReadTimeout) as e:
            logger.warning(f"Attempt {attempt + 1} failed with error: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("All retry attempts failed.")
                return None
        except Exception as e:
            logger.error(f"Unexpected error occurred: {type(e).__name__}: {e}")
            return None
    
    return None  # This line should never be reached due to the return None in the except block