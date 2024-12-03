#file_processor.py
import pandas as pd
import pdfplumber
import xlrd
import openpyxl
from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini  # Importo la funzione per gemini
import requests
from bs4 import BeautifulSoup
import urllib3
from requests.exceptions import ConnectTimeout, RequestException, HTTPError
from urllib3.exceptions import MaxRetryError

def fetch_and_extract_text(content):
    """
    Extracts text from the provided content.

    :param content: The content to extract text from (could be HTML or plain text).
    :return: Extracted text.
    """
    if isinstance(content, str) and content.strip().startswith('<'):
        # Assume it's HTML content
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    else:
        # Assume it's already plain text
        return content

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

    return "\n".join(responses) if responses else "Nessun modello selezionato."

def process_pages(pages, query, output_file, use_ollama, use_cohere, use_gpt, use_gemini):
    """
    Processes the provided pages by extracting text and generating responses using selected AI models.

    :param pages: List of page contents to process.
    :param query: Search query to extract specific content from the text.
    :param output_file: File to save extracted text.
    :param use_ollama, use_cohere, use_gpt, use_gemini: Flags to select AI models.
    :return: List of summaries for each page and the final reduced response.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    all_summaries = []
    page_summaries = []

    for i, page_content in enumerate(pages, 1):
        print(f"Processing page {i}")
        text = fetch_and_extract_text(page_content)

        # Write extracted text to the output file
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"Page {i}:\n\nTesto:\n{text}\n\n{'='*50}\n\n")

        prompt = f'"{query}" {text}.'

        response_text = generate_response(
            prompt, use_ollama, use_cohere, use_gpt, use_gemini
        )

        if response_text:
            print(f"Risposta per la pagina {i}: {response_text}")
            all_summaries.append(response_text)
            page_summaries.append(f"Page {i}: {response_text}")

            with open("files/model_responses.txt", 'a', encoding='utf-8') as model_f:
                model_f.write(f"Page {i}:\nRisposta:\n{response_text}\n{'='*50}\n\n")

            with open("files/model_output_file_no_link.txt", 'a', encoding='utf-8') as no_link_f:
                no_link_f.write(f"\n{response_text},\n")

    # Reduce responses
    if len(all_summaries) > 1:
        print("Avvio della riduzione delle risposte finali...")
        X = 20  # Size of response groups to aggregate
        reduced_responses = []

        for i in range(0, len(all_summaries), X):
            subset = all_summaries[i:i + X]
            aggregated_text = " ".join(subset)
            prompt = f'"{query}" : {aggregated_text}'

            reduced_response = generate_response(
                prompt, use_ollama, use_cohere, use_gpt, use_gemini
            )

            if reduced_response:
                reduced_responses.append(reduced_response)

        final_summary = "\n".join(reduced_responses)
        print("Sintesi finale:", final_summary)
    else:
        final_summary = all_summaries[0] if all_summaries else "Nessuna sintesi disponibile."
        print("Sintesi finale:", final_summary)

    return page_summaries, final_summary

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.

    :param file_path: Path to the PDF file.
    :return: Extracted text.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n\n"
    return text

def extract_text_from_xls(file_path):
    """
    Extracts text from an XLS file.

    :param file_path: Path to the XLS file.
    :return: Extracted text.
    """
    text = ""
    book = xlrd.open_workbook(file_path)
    sheet = book.sheet_by_index(0)
    for row in range(sheet.nrows):
        text += " ".join(map(str, sheet.row_values(row))) + "\n"
    return text

def extract_text_from_xlsx(file_path):
    """
    Extracts text from an XLSX file.

    :param file_path: Path to the XLSX file.
    :return: Extracted text.
    """
    text = ""
    book = openpyxl.load_workbook(file_path)
    sheet = book.active
    for row in sheet.iter_rows(values_only=True):
        text += " ".join(map(str, row)) + "\n"
    return text

def process_file(file_path, query, output_file, use_ollama, use_cohere, use_gpt, use_gemini):
    """
    Processes the provided file by extracting text and generating responses using selected AI models.

    :param file_path: Path to the file to process.
    :param query: Search query to extract specific content from the text.
    :param output_file: File to save extracted text.
    :param use_ollama, use_cohere, use_gpt, use_gemini: Flags to select AI models.
    """
    try:
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.xls'):
            text = extract_text_from_xls(file_path)
        elif file_path.lower().endswith('.xlsx'):
            text = extract_text_from_xlsx(file_path)
        else:
            raise ValueError("Tipo di file non supportato")

        # Split the text into pages (you may need to adjust this based on your needs)
        pages = text.split('\n\n')  # Assuming double line breaks separate pages
        
        page_summaries, final_summary = process_pages(pages, query, output_file, use_ollama, use_cohere, use_gpt, use_gemini)
        # Save page summaries and final summary
        with open("files/page_summaries.txt", 'w', encoding='utf-8') as f:
            f.write("\n\n".join(page_summaries))

        with open("files/final_summary.txt", 'w', encoding='utf-8') as f:
            f.write(final_summary)

        print("Elaborazione completata. I riassunti delle pagine sono stati salvati in 'page_summaries.txt' e la sintesi finale in 'final_summary.txt'.")

    except Exception as e:
        print(f"Si è verificato un errore durante l'elaborazione del file: {str(e)}")
