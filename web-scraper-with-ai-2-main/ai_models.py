#ai_models.py
from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini  # Importo la funzione per gemini

def send_request_to_ai(prompt, use_ollama=False, use_cohere=False, use_gpt=False, use_gemini=False):
    """
    Invia una richiesta di generazione di testo al modello AI selezionato (Ollama, GPT, Cohere o Gemini).

    :param prompt: Testo del prompt da inviare ai modelli.
    :param use_ollama: Flag per usare Ollama.
    :param use_cohere: Flag per usare Cohere.
    :param use_gpt: Flag per usare GPT.
    :param use_gemini: Flag per usare Gemini.
    :return: Risposta generata dal modello.
    """
    responses = []

    if use_gpt:
        response_text_gpt = generate_with_gpt(prompt=prompt, temperature=0.7)
        responses.append(f"GPT: {response_text_gpt}")

    elif use_ollama:
        response_text_ollama = generate_with_ollama(prompt=prompt)
        responses.append(f"Ollama: {response_text_ollama}")

    elif use_cohere:
        response_text_cohere = generate_with_cohere(prompt=prompt, temperature=0.7)
        responses.append(f"Cohere: {response_text_cohere}")

    elif use_gemini:
        response_text_gemini = generate_with_gemini(prompt=prompt)
        responses.append(f"Gemini: {response_text_gemini}")

    return "\n".join(responses) if responses else "Nessun modello selezionato."

def process_request(query, use_ollama=False, use_cohere=False, use_gpt=False, use_gemini=False):
    """
    Processa una richiesta e genera una risposta usando il modello AI selezionato.

    :param query: Testo del prompt che viene elaborato.
    :param use_ollama: Flag per usare Ollama.
    :param use_cohere: Flag per usare Cohere.
    :param use_gpt: Flag per usare GPT.
    :param use_gemini: Flag per usare Gemini.
    :return: Risposta generata dal modello AI selezionato.
    """
    prompt = f"Genera una risposta per la richiesta: {query}"

    # Usa la funzione send_request_to_ai per inviare il prompt al modello AI corretto.
    response = send_request_to_ai(
        prompt=prompt, 
        use_ollama=use_ollama, 
        use_cohere=use_cohere, 
        use_gpt=use_gpt,
        use_gemini=use_gemini
    )

    return response

def handle_request(input_text, output_file, use_ollama=False, use_cohere=False, use_gpt=False, use_gemini=False):
    """
    Gestisce la richiesta inviata e genera una risposta usando il modello AI selezionato.
    Scrive anche il risultato su un file di output.

    :param input_text: Testo della richiesta da elaborare.
    :param output_file: File in cui salvare il testo generato.
    :param use_ollama: Flag per usare Ollama.
    :param use_cohere: Flag per usare Cohere.
    :param use_gpt: Flag per usare GPT.
    :param use_gemini: Flag per usare Gemini.
    """
    print(f"Processing request: {input_text}")
    
    # Genera la risposta
    response = process_request(
        query=input_text,
        use_ollama=use_ollama,
        use_cohere=use_cohere,
        use_gpt=use_gpt,
        use_gemini=use_gemini
    )

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(f"Testo di input: {input_text}\nRisposta:\n{response}\n\n{'='*50}\n\n")
