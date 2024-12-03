# gpt_api.py
import requests
import time
from typing import Optional
from config import GPT_API_URL, GPT_API_KEY

def generate_with_gpt(
    prompt: str, 
    model: str = "gpt-4o-mini", 
    max_tokens: int = 2000, 
    temperature: float = 0.7, 
    retries: int = 3
) -> Optional[str]:
    """
    Generate text using the GPT API with retry mechanism.

    Args:
        prompt (str): The input prompt for the GPT model.
        model (str): The GPT model to use. Default is "gpt-4o-mini".
        max_tokens (int): Maximum number of tokens in the response. Default is 150.
        temperature (float): Controls randomness in generation. Default is 0.7.
        retries (int): Number of retry attempts in case of errors. Default is 3.

    Returns:
        Optional[str]: The generated response, or None if all retries fail.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GPT_API_KEY}"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    for attempt in range(retries):
        try:
            response = requests.post(GPT_API_URL, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:  # Too Many Requests
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limit reached. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                print(f"HTTP Error: {err}")
                break
        except requests.exceptions.RequestException as err:
            print(f"Request Error: {err}")
            if attempt < retries - 1:
                print(f"Retrying... (Attempt {attempt + 2}/{retries})")
                time.sleep(1)
            else:
                break

    print("All retry attempts failed.")
    return None





# This file provides an interface to interact with the GPT API (likely OpenAI's API or a similar service).
# It contains a function generate_with_gpt() which sends prompts to the GPT model and retrieves responses.
# Key features:
# - Uses API key and URL from a config file for authentication and endpoint specification.
# - Allows customization of model, max tokens, and temperature for the API request.
# - Implements a retry mechanism with exponential backoff for handling rate limiting (HTTP 429 errors).
# - Handles various HTTP and request exceptions, providing robustness to the API interaction.
# This function is called by link_processor.py when GPT-based text generation is requested.