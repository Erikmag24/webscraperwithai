#use_azure_textcomparison.py

from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from config import AZURE_ENDPOINT, AZURE_KEY  # Ensure these are defined in your config.py
import os
import docx2txt
import PyPDF2
import openpyxl

def read_file(file_path):
    """
    Reads the content of the file based on its extension.
    Supports files of type: .txt, .docx, .pdf, .xlsx.
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
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            return text
        elif ext == '.xlsx':
            return read_xlsx_file(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return ''
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return ''

def read_xlsx_file(file_path):
    """
    Reads and concatenates text from the cells of an Excel file (.xlsx).
    """
    wb = openpyxl.load_workbook(file_path)
    text = ''
    
    # Iterate over each sheet and cell to extract data
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value:  # Consider only cells with values
                    text += str(cell.value) + ' '
            text += '\n'
    
    return text

def split_text_into_chunks(text, max_size):
    """
    Splits the text into chunks of maximum 'max_size' characters, attempting to split at sentence boundaries.
    """
    import re

    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ''

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_size:
            current_chunk += sentence + ' '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If the sentence itself is longer than max_size, split it
            while len(sentence) > max_size:
                chunks.append(sentence[:max_size])
                sentence = sentence[max_size:]
            current_chunk = sentence + ' '
    
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def process_text_with_azure(file_paths):
    """
    Processes text files using Azure Text Analytics to recognize entities.

    :param file_paths: List of file paths to process.
    :return: A string containing aggregated entities recognized by Azure.
    """
    try:
        # Initialize Azure Text Analytics client
        text_analytics_client = TextAnalyticsClient(
            endpoint=AZURE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_KEY)
        )

        # Read the content of the files using the read_file function
        documents = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
            text = read_file(file_path)
            if text:
                # Split the text into chunks to comply with Azure's size limit
                max_size = 5120  # Azure's limit for text elements per document
                chunks = split_text_into_chunks(text, max_size)
                documents.extend(chunks)
            else:
                print(f"Unable to read file: {file_path}")
                continue

        if not documents:
            print("No valid documents to process.")
            return "No valid documents to process."

        # Analyze entities with Azure
        aggregated_entities = {}
        batch_size = 5  # Azure's limit for documents per request is 5

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            response = text_analytics_client.recognize_entities(batch)
            # Process the result and aggregate by category
            for doc in response:
                if not doc.is_error:
                    for entity in doc.entities:
                        category = entity.category
                        if category not in aggregated_entities:
                            aggregated_entities[category] = set()
                        aggregated_entities[category].add(entity.text)
                else:
                    print(f"Error processing document: {doc.error.code} - {doc.error.message}")

        if not aggregated_entities:
            return "No entities were recognized in the provided documents."

        # Build the aggregated output
        aggregated_output = ""
        for category, entities in aggregated_entities.items():
            aggregated_output += f"{category}:\n"
            aggregated_output += ", ".join(entities)  # Entities are already unique due to set
            aggregated_output += "\n\n"

        return aggregated_output.strip()

    except Exception as e:
        print(f"An error occurred while processing with Azure: {str(e)}")
        return f"An error occurred: {str(e)}"
