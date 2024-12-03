#filecomparison.py

import spacy
import difflib
import os
from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini  # Importo la funzione per gemini
import docx2txt
import PyPDF2
import openpyxl

def read_file(file_path):
    """
    Legge il contenuto del file in base all'estensione.
    Supporta file di tipo: .txt, .docx, .pdf, .xlsx.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif ext == '.docx':
            return docx2txt.process(file_path)
        elif ext == '.pdf':
            text = ''
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        elif ext == '.xlsx':
            return read_xlsx_file(file_path)
        else:
            print(f"Tipo di file non supportato: {ext}")
            return ''
    except Exception as e:
        print(f"Errore nella lettura del file {file_path}: {str(e)}")
        return ''

def read_xlsx_file(file_path):
    """
    Legge e concatena il testo dalle celle di un file Excel (.xlsx).
    """
    wb = openpyxl.load_workbook(file_path)
    text = ''
    
    # Itera su ogni foglio e su ogni cella per estrarre i dati
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value:  # Considera solo celle con valori
                    text += str(cell.value) + ' '
        text += '\n'
    
    return text


def process_text_files(file_paths, question, output_file, use_ollama, use_cohere, use_gpt, use_gemini):
    try:
        # Carica il modello SpaCy per l'italiano
        print("Caricamento del modello SpaCy...")
        nlp = spacy.load("it_core_news_lg")
        print("Modello SpaCy caricato.")

        texts = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"File non trovato: {file_path}")
                continue
            text = read_file(file_path)
            if text:
                texts.append(text)
            else:
                print(f"Impossibile leggere il file: {file_path}")
        if not texts:
            print("Nessun file di testo valido fornito.")
            return

        # Processa i testi
        processed_texts = []
        for idx, text in enumerate(texts):
            doc = nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            processed_texts.append({
                'text': text,
                'entities': entities
            })

        # Confronta i testi se ce ne sono più di uno
        differences = ""
        if len(texts) > 1:
            for i in range(len(texts)):
                for j in range(i+1, len(texts)):
                    diff = difflib.unified_diff(
                        texts[i].splitlines(),
                        texts[j].splitlines(),
                        lineterm='',
                        fromfile=f'Testo {i+1}',
                        tofile=f'Testo {j+1}'
                    )
                    differences += '\n'.join(diff) + '\n'

        # Raggruppa le entità per file e aggregale
        entities_per_file = []
        aggregated_entities = {}
        for idx, processed in enumerate(processed_texts):
            entities = processed['entities']
            entities_dict = {}
            for ent_text, ent_label in entities:
                entities_dict.setdefault(ent_label, set()).add(ent_text)
                aggregated_entities.setdefault(ent_label, set()).add(ent_text)
            entities_per_file.append({
                'file_index': idx + 1,
                'entities': entities_dict
            })

        # Converti i set in liste se necessario
        for ent_label in aggregated_entities:
            aggregated_entities[ent_label] = list(aggregated_entities[ent_label])

        # Prepara il prompt per i modelli AI
        context = "\n\n".join(texts)
        prompt = f"Contesto:\n{context}\n\nDomanda: {question}"

        # Genera la risposta utilizzando i modelli AI selezionati
        response_text = generate_response(
            prompt, use_ollama, use_cohere, use_gpt, use_gemini
        )

        # Scrivi i risultati nel file di output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== Testi ===\n")
            for idx, processed in enumerate(processed_texts):
                f.write(f"\n=== Testo {idx+1} ===\n")
                f.write(processed['text'] + '\n')

            f.write("\n=== Entità per file ===\n")
            for entities_info in entities_per_file:
                f.write(f"\nEntità nel Testo {entities_info['file_index']}:\n")
                for ent_label, ent_set in entities_info['entities'].items():
                    ent_list = ', '.join(ent_set)
                    f.write(f"{ent_label}: {ent_list}\n")

            f.write("\n=== Entità aggregate ===\n")
            for ent_label, ent_list in aggregated_entities.items():
                f.write(f"{ent_label}: {', '.join(ent_list)}\n")

            if differences.strip():
                f.write("\n=== Differenze tra i testi ===\n")
                f.write(differences + '\n')
            else:
                f.write("\nNessuna differenza da mostrare.\n")

            f.write("\n=== Risposta AI ===\n")
            f.write(response_text + '\n')

        print(f"Elaborazione completata. I risultati sono stati salvati in '{output_file}'.")

    except Exception as e:
        print(f"Si è verificato un errore durante l'elaborazione dei file di testo: {str(e)}")


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
        response_text_cohere = generate_with_cohere(prompt=prompt)
        responses.append(f"Cohere: {response_text_cohere}")

    if use_gpt:
        response_text_gpt = generate_with_gpt(prompt=prompt)
        responses.append(f"GPT: {response_text_gpt}")

    if use_gemini:
        response_text_gemini = generate_with_gemini(prompt=prompt)
        responses.append(f"Gemini: {response_text_gemini}")

    return "\n".join(responses) if responses else "No model selected."
