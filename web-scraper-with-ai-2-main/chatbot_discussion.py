# chatbot_discussion.py

from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini
import os

# Mappatura dei chatbot disponibili
CHATBOT_FUNCTIONS = {
    'gpt': generate_with_gpt,
    'ollama': generate_with_ollama,
    'cohere': generate_with_cohere,
    'gemini': generate_with_gemini
}

def load_input(query: str = None, file_path: str = None) -> str:
    """
    Carica l'input da una query, un file o entrambi.
    """
    input_text = ""
    if query:
        input_text += query + "\n"
    if file_path:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Il file {file_path} non esiste.")
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            input_text += file_content
    return input_text.strip()

def conduct_discussion(
    initial_input: str,
    chatbot_instances: list,
    cycles: int = 3
) -> (str, list):
    """
    Conduci una discussione tra varie istanze di chatbot.

    :param initial_input: Input iniziale per la discussione.
    :param chatbot_instances: Lista di dizionari con 'name' e 'type' dei chatbot.
    :param cycles: Numero di cicli di discussione.
    :return: Sintesi finale e intera conversazione.
    """
    conversation_history = [f"Utente: {initial_input}"]
    
    for cycle in range(cycles):
        for idx, bot in enumerate(chatbot_instances):
            bot_name = f"{bot['type']}_{idx+1}"
            prompt = "\n".join(conversation_history) + f"\n{bot_name}:"
            try:
                response = CHATBOT_FUNCTIONS[bot['type']](prompt)
                response = response.strip()
                conversation_history.append(f"{bot_name}: {response}")
            except Exception as e:
                conversation_history.append(f"{bot_name}: Errore nella generazione della risposta. Dettagli: {str(e)}")
    
    return conversation_history

def generate_summary(conversation_history: list, summary_bot: dict) -> str:
    """
    Genera un riassunto della conversazione usando un chatbot specifico.

    :param conversation_history: Lista delle interazioni della conversazione.
    :param summary_bot: Dizionario con 'name' e 'type' del chatbot per il riassunto.
    :return: Riassunto della conversazione.
    """
    bot_name = f"{summary_bot['type']}_summary"
    prompt = "\n".join(conversation_history) + f"\n{bot_name}: Per favore, fornisci un riassunto della discussione sopra."
    try:
        summary = CHATBOT_FUNCTIONS[summary_bot['type']](prompt)
        return summary.strip()
    except Exception as e:
        return f"Errore nella generazione del riassunto: {str(e)}"

