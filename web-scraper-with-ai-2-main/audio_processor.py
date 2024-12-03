#audio_processor.py
import whisper
from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini  # Importo la funzione per gemini

def generate_response(prompt, use_ollama, use_cohere, use_gpt, use_gemini):
    """
    Generates a response using selected AI models based on the provided flags.

    :param prompt: The text prompt to pass to the AI models.
    :param use_ollama, use_cohere, use_gpt, use_gemini: Flags indicating which AI models to use.
    :return: A combined response string from the selected models.
    """
    responses = []

    if use_ollama:
        response_text_ollama = generate_with_ollama(prompt=prompt)
        responses.append(f"Ollama: {response_text_ollama}")

    if use_cohere:
        response_text_cohere = generate_with_cohere(prompt=prompt, temperature=0.7)
        responses.append(f"Cohere: {response_text_cohere}")

    if use_gpt:
        response_text_gpt = generate_with_gpt(prompt=prompt, temperature=0.7)
        responses.append(f"GPT: {response_text_gpt}")

    if use_gemini:
        response_text_gemini = generate_with_gemini(prompt=prompt)
        responses.append(f"Gemini: {response_text_gemini}")

    return "\n".join(responses) if responses else "No model selected."

def process_audio(audio_file_path, query, output_file, use_ollama, use_cohere, use_gpt, use_gemini):
    """
    Processes the provided audio file by transcribing it using OpenAI's Whisper model
    and generating responses using selected AI models.

    :param audio_file_path: Path to the audio file to process.
    :param query: Search query to extract specific content from the transcribed text.
    :param output_file: File to save extracted text.
    :param use_ollama, use_cohere, use_gpt, use_gemini: Flags indicating which AI models to use.
    """
    try:
        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("small")  # You can choose 'tiny', 'base', 'small', 'medium', 'large'
        print("Transcribing audio using Whisper model...")

        # Transcribe the audio file
        result = model.transcribe(audio_file_path)
        transcribed_text = result['text']
        print("Transcription completed.")

        # Write the transcribed text to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Transcribed Text:\n{transcribed_text}\n")

        # Prepare the prompt for the AI models
        prompt = f'"{query}" {transcribed_text}.'

        # Generate response using selected AI models
        response_text = generate_response(
            prompt, use_ollama, use_cohere, use_gpt, use_gemini
        )

        # Save the response
        with open("files/model_responses.txt", 'w', encoding='utf-8') as model_f:
            model_f.write(f"Response:\n{response_text}\n")

        print("Processing completed. The response has been saved in 'model_responses.txt'.")

    except Exception as e:
        print(f"An error occurred while processing the audio file: {str(e)}")
