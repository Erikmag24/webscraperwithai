from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from translator import translate_text, get_available_languages
from web_scraper import scrape_and_process
import config
import os
import logging
import secrets
from ai_models import send_request_to_ai  # Importa la funzione per gestire la richiesta AI
from datetime import datetime  # Importa datetime per l'anno corrente
from execute_scraping import execute_scraping
from maps import generate_map_tiles_and_process
import json
from gpt_api import generate_with_gpt
import re
from use_azure_textcomparison import *

app = Flask(__name__)

# Set the secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Configure logging

logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Configure upload folder
UPLOAD_FOLDER = os.path.abspath('uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'docx', 'webm', 'wav', 'mp3'}  # Added audio file extensions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template(
        'index.html',
        languages=get_available_languages(),
        search_engines=config.SEARCH_ENGINES,
        default_process_type='audio'  # Add a default process type for audio
    )

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    if request.method == 'POST':
        # Update config with form data
        config.GPT_API_URL = request.form.get('GPT_API_URL', config.GPT_API_URL)
        config.GPT_API_KEY = request.form.get('GPT_API_KEY', config.GPT_API_KEY)
        config.OLLAMA_API_URL = request.form.get('OLLAMA_API_URL', config.OLLAMA_API_URL)
        config.COHERE_API_URL = request.form.get('COHERE_API_URL', config.COHERE_API_URL)
        config.COHERE_API_KEY = request.form.get('COHERE_API_KEY', config.COHERE_API_KEY)
        config.COHERE_MODEL = request.form.get('COHERE_MODEL', config.COHERE_MODEL)
        config.OUTPUT_FILE_PATH = request.form.get('OUTPUT_FILE_PATH', config.OUTPUT_FILE_PATH)
        
        # Update config.SEARCH_ENGINES with new entries
        search_engine_names = request.form.getlist('search_engine_name[]')
        search_engine_urls = request.form.getlist('search_engine_url[]')
        config.SEARCH_ENGINES = {name: url for name, url in zip(search_engine_names, search_engine_urls) if name and url}
        
        # Save the updated configuration to the config file
        with open('config.py', 'w') as f:
            for key, value in vars(config).items():
                if not key.startswith('__'):
                    f.write(f"{key} = {repr(value)}\n")
        
        flash('Configuration updated successfully', 'success')
        return redirect(url_for('index'))
    
    return render_template('config.html', config=config)

@app.route('/process', methods=['POST'])
def process():
    query = request.form.get('query')
    languages_to_translate = request.form.getlist('languages')
    selected_models = request.form.getlist('model')
    search_engines = request.form.getlist('search_engines')
    numero_pagine = int(request.form.get('numero_pagine', 1))
    process_type = request.form.get('process_type', 'web')

    use_ollama = 'Ollama' in selected_models  
    use_cohere = 'Cohere' in selected_models
    use_gpt = 'GPT' in selected_models
    use_gemini = 'Gemini' in selected_models  # Aggiunto supporto per Gemini

    translations = translate_text(query, languages_to_translate)

    try:
        if process_type == 'web':
            scrape_and_process(
                query=query,
                translations=translations,
                numero_pagine=numero_pagine,
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                search_engines=search_engines
            )
        elif process_type == 'file':
            if 'file' not in request.files or not allowed_file(request.files['file'].filename):
                flash('Invalid file type or no file selected', 'error')
                return redirect(url_for('index'))
            
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            scrape_and_process(
                query=query,
                translations=translations,
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                process_file_path=filepath
            )
        elif process_type == 'audio':
            if 'audio_file' not in request.files or not allowed_file(request.files['audio_file'].filename):
                flash('Invalid audio file type or no audio file uploaded', 'error')
                return redirect(url_for('index'))
            
            audio_file = request.files['audio_file']
            filename = secure_filename(audio_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            scrape_and_process(
                query=query,
                translations={},
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                process_audio_path=filepath
            )
        else:
            flash('Invalid process type', 'error')
            return redirect(url_for('index'))

        # Read the output from the model responses
        with open('files/model_responses.txt', 'r', encoding='utf-8') as file:
            output_content = file.read()

        ai_response = send_request_to_ai(
            prompt=query + "::ATTENZIONE sulla base della precedente query genera un codice html, js e css che sia visualizzabile all'interno di una textarea html come se fosse uno snippett di codice, questo per visualizzare al meglio graficamente, in modo interattivo, come fosse uno snippett che si modifica in base al prompt, una mappa, un grafico o qualunque cosa che meglio descriva la query e i dati, grazie mille, ovviamentre non darlo così '```html' altrimenti non si può visualizzare correttamente, deve essere uno snippet di html che viene visualizzato come se fosse uno snippet e quindi non in formato codice ma di pagina, capito, non scrivere nemmeno testo altyriemntio si visualizza il testo, se decidi di creare un grafico fornisci solo html, css e js per fgare il grafico e nulla di più, non serve partire dal tag html poichè sei già al suo interno dati::" + output_content,
            use_ollama=use_ollama,
            use_cohere=use_cohere,
            use_gpt=use_gpt,
            use_gemini=use_gemini  # Aggiunto supporto per Gemini
        ).removeprefix("GPT: ```html").removesuffix("```")

        # List specific .txt files based on process_type
        if process_type == 'audio':
            text_files = ['model_responses.txt', 'scraped_texts.txt']
        elif process_type == 'file':
            text_files = ['final_summary.txt', 'page_summaries.txt', 'scraped_texts.txt']
        else:  # web
            text_files = ['model_output_file_no_link.txt', 'scraped_texts.txt', 'model_responses.txt']
        
        # Filter the list to include only existing files
        text_files = [f for f in text_files if os.path.exists(os.path.join('files/', f))]
        
    except FileNotFoundError:
        logging.error(f"Output file not found: model_responses.txt")
        flash('Output file not found. Please try again.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logging.exception("Error during processing")
        flash(f'Error during processing: {str(e)}', 'error')
        return redirect(url_for('index'))

    return render_template(
        'process_result.html',
        query=query,
        translations=translations,
        output=output_content,
        ai_response=ai_response,
        text_files=text_files,
        get_file_preview=get_file_preview,
        current_year=datetime.now().year
    )

def get_file_preview(filename, max_length=100):
    try:
        with open('files/'+filename, 'r', encoding='utf-8') as file:
            content = file.read(max_length)  # Read only the first max_length characters
            return content.replace('\n', ' ')  # Replace newlines with spaces for better formatting
    except Exception:
        return "Could not preview file."

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('files/', filename, as_attachment=True)

@app.route('/discussion', methods=['GET', 'POST'])
def discussion_page():
    if request.method == 'POST':
        # Fetch form data
        input_source = request.form.get('input_source')
        query = request.form.get('query') or ""  # Inizializziamo la query come stringa vuota se non esiste
        cycles = int(request.form.get('cycles'))
        chatbots = request.form.getlist('chatbots')
        summary_bot = request.form.get('summary_bot')
        uploaded_file = request.files.get('file')

        # Handle file upload if present
        if uploaded_file:
            file_content = uploaded_file.read().decode('utf-8')  # assuming text files
            query += "\n" + file_content  # Concatenare il contenuto del file alla query
        
        # Creiamo una lista di istanze di chatbot
        chatbot_instances = [{'type': bot} for bot in chatbots]
        
        # Import and invoke chatbot discussion function
        from chatbot_discussion import conduct_discussion, generate_summary
        conversation_history = conduct_discussion(query, chatbot_instances, cycles)
        summary = generate_summary(conversation_history, {'type': summary_bot})
        
        # Pass results to the HTML template for display
        return render_template('chatbot_discussion.html', summary=summary, conversation=conversation_history)
    
    # On GET request, render the discussion page
    return render_template('chatbot_discussion.html')



@app.route('/discussion_full', methods=['GET', 'POST'])
def discussion_page_full():
    if request.method == 'POST':
        initial_input = request.form.get('initial_input') or ""
        
        instance_numbers = set()
        for key in request.form.keys():
            if key.startswith('chatbot_name_'):
                instance_number = key.split('_')[-1]
                if instance_number.isdigit():
                    instance_numbers.add(int(instance_number))
        instance_numbers = sorted(instance_numbers)
        
        from chatbot_discussion_full import ChatbotInstance, conduct_pipeline
        
        chatbot_instances = {}
        
        for instance_number in instance_numbers:
            name = request.form.get(f'chatbot_name_{instance_number}')
            type = request.form.get(f'chatbot_type_{instance_number}')
            inputs = request.form.getlist(f'chatbot_inputs_{instance_number}')
            additional_text = request.form.get(f'chatbot_additional_text_{instance_number}')
            
            chatbot_instance = ChatbotInstance(
                name=name,
                type=type,
                inputs=[],
                additional_text=additional_text
            )
            chatbot_instances[name] = {
                'instance_number': instance_number,
                'name': name,
                'type': type,
                'inputs': inputs,
                'additional_text': additional_text,
                'instance': chatbot_instance
            }
        
        for name, data in chatbot_instances.items():
            inputs = []
            for input_name in data['inputs']:
                if input_name == 'initial_input':
                    inputs.append(initial_input)
                else:
                    if input_name in chatbot_instances:
                        inputs.append(chatbot_instances[input_name]['instance'])
                    else:
                        flash(f"Input {input_name} for chatbot {name} not found.", 'error')
                        return redirect(url_for('discussion_page_full'))
            data['instance'].inputs = inputs
        
        pipeline = [data['instance'] for data in chatbot_instances.values()]
        
        final_outputs, conversation_history = conduct_pipeline(pipeline)
        
        return render_template('chatbot_discussion_full.html', final_outputs=final_outputs, conversation_history=conversation_history)
    
    return render_template('chatbot_discussion_full.html')



@app.route('/text_comparison', methods=['GET', 'POST'])
def text_comparison_page():
    if request.method == 'POST':
        use_azure = request.form.get('use_azure') == 'True'
        if use_azure:
            print("Azure integration activated.")

            # List of file paths to process
            file_paths = []  # Populate this list with the paths to your files

            # Example: Assuming you have obtained the file paths from the uploaded files
            uploaded_files = request.files.getlist('files')
            for file in uploaded_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    file_paths.append(file_path)
                    print(f"File saved: {file_path}")

            # Call the Azure processing function
            aggregated_output = process_text_with_azure(file_paths)

            # Now you can render the output in your template or handle it as needed
            return render_template('text_comparison.html', result=aggregated_output)


        else:
            # Debugging
            print("Form Data:", request.form)
            print("Files:", request.files)

            # Ottenere i file caricati
            uploaded_files = request.files.getlist('files')  # Correzione qui: usa 'files'
            print("Numero di file caricati:", len(uploaded_files))

            if not uploaded_files or uploaded_files[0].filename == '':
                flash('Nessun file selezionato.')
                return redirect(request.url)

            # Salvare i file caricati
            file_paths = []
            for file in uploaded_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    file_paths.append(file_path)
                    print(f"File salvato: {file_path}")

            if not file_paths:
                flash('Nessun file valido caricato.')
                return redirect(request.url)

            # Ottenere gli altri dati del form
            question = request.form.get('question', '')
            output_file = request.form.get('output_file', 'output.txt')

            # Selezione dei modelli AI
            use_gpt = request.form.get('use_gpt') == 'True'
            use_ollama = request.form.get('use_ollama') == 'True'
            use_cohere = request.form.get('use_cohere') == 'True'
            use_gemini = request.form.get('use_gemini') == 'True'

            # Chiamare la funzione di elaborazione del testo
            from filecomparison import process_text_files
            process_text_files(file_paths, question, output_file, use_ollama, use_cohere, use_gpt, use_gemini)

            # Leggere il risultato dal file di output
            with open(output_file, 'r', encoding='utf-8') as f:
                result = f.read()

            return render_template('text_comparison.html', result=result)
    else:
        return render_template('text_comparison.html')
    
@app.route('/generate_maps', methods=['GET', 'POST'])
def generate_maps():
    """
    Gestisce la generazione delle mappe e restituisce i risultati in una pagina HTML.
    """
    if request.method == 'POST':
        # Ottieni i dati dal modulo
        use_azure = request.form.get('use_azure') == 'True'
        lat_center = float(request.form['lat_center'])
        lon_center = float(request.form['lon_center'])
        area_width_m = float(request.form['area_width_m'])
        area_height_m = float(request.form['area_height_m'])
        zoom_level = int(request.form['zoom_level'])
        map_width_px = int(request.form['map_width_px'])
        map_height_px = int(request.form['map_height_px'])
        chatbot_choice = request.form['chatbot_choice']
        prompt_template = request.form['prompt_template']

        # Chiama la funzione generate_map_tiles_and_process da maps.py
        results = generate_map_tiles_and_process(
            lat_center, lon_center, area_width_m, area_height_m,
            zoom_level, map_width_px, map_height_px,
            chatbot_choice, prompt_template, use_azure
        )

        # Prepara i risultati per la visualizzazione nell'HTML
        return render_template('maps_results.html', results=results)

    # GET: Visualizza la pagina iniziale
    return render_template('maps_results.html', results=None)

@app.route('/scraping_interface', methods=['GET', 'POST'])
def scraping_interface():
    if request.method == 'POST':
        query = request.form.get('query')
        search_engine = request.form.get('search_engine')
        num_pages = int(request.form.get('num_pages'))
        recursion_depth = int(request.form.get('recursion_depth'))
        enable_gpt = request.form.get('enable_gpt')  # Controlla se il flag è presente
        gpt_recursion_depth = int(request.form.get('gpt_recursion_depth'))
        model_2 = request.form.get('model_2')  # Controlla se il flag è presente

        if enable_gpt:  # Se il flag è attivato
            # Perform the scraping
                    try:
                        json_output=""
                        for i in range(gpt_recursion_depth):
                            if model_2:
                                from prova import execute_scraping as execute_scraping2
                                summaries=execute_scraping2(query, search_engine, num_pages, recursion_depth)
                            else:
                                summaries = execute_scraping(query, search_engine, num_pages, recursion_depth)

                            # Prompt to generate JSON with GPT
                            prompt= f"""
                            Genera esclusivamente un JSON valido che includa informazioni dettagliate su {query} o e 
                            altri dati rilevanti. Non aggiungere spiegazioni o testo aggiuntivo, restituisci solo il JSON:
                            {summaries}
                            """
                            output= generate_with_gpt(prompt)
                            if output is not None:
                                json_output+=output
                                logging.debug(f"GPT Output: {json_output}")


                            
                            QUERY2 = f"""
                            Genera esclusivamente una query valida che includa informazioni dettagliate su {query} o e 
                            altri dati rilevanti. Non aggiungere spiegazioni o testo aggiuntivo, restituisci solo una query per ottenere informazioni rilevanti come fossi uno studioso che dato delle informazioni acquisisce ricerche su quall'argomento da internet :
                            {json_output}
                            """
                            print(QUERY2)
                            
                        print(json_output)
                        return render_template(
                            'scraping_interface.html',
                            result=summaries,
                            gpt_json=json_output
                        )


                    except json.JSONDecodeError as e:
                        logging.exception("Errore durante la decodifica del JSON")
                        flash(f"Errore nella decodifica del JSON generato: {e.msg}", 'error')
                        return redirect(url_for('scraping_interface'))

                    except Exception as e:
                        logging.exception("Errore durante lo scraping o la generazione del JSON")
                        flash(f"Errore durante l'elaborazione: {str(e)}", "error")
                        return redirect(url_for('scraping_interface'))


        else:
                try:
                    if model_2:
                        from prova import execute_scraping as execute_scraping2
                        summaries=execute_scraping2(query, search_engine, num_pages, recursion_depth)
                    else:
                        summaries = execute_scraping(query, search_engine, num_pages, recursion_depth)

                    # Prompt to generate JSON with GPT
                    prompt = f"""
                    Genera esclusivamente un JSON valido che includa informazioni dettagliate su {query} o e 
                    altri dati rilevanti. Non aggiungere spiegazioni o testo aggiuntivo, restituisci solo il JSON, in caso il json deve contenere le informazioni più rilevamenti ad esempio il modello più popolare tra i vari testi, in ordine di rilevanza e popolarità facendo la media del più famoso grazie:
                    {summaries}
                    """

                    json_output = generate_with_gpt(prompt)
                    logging.debug(f"GPT Output: {json_output}")
                    if json_output is not None:

                        # Attempt to extract JSON from the output
                        match = re.search(r'\{.*\}', json_output, re.DOTALL)
                        if match:
                            json_str = match.group(0)
                            json_data = json.loads(json_str)
                        else:
                            raise ValueError("No JSON object found in GPT output.")

                        return render_template(
                            'scraping_interface.html',
                            result=summaries,
                            gpt_json=json_data
                        )
                    else:
                        return render_template(
                            'scraping_interface.html',
                            result=summaries,
                            gpt_json=summaries
                        )

                except json.JSONDecodeError as e:
                    logging.exception("Errore durante la decodifica del JSON")
                    flash(f"Errore nella decodifica del JSON generato: {e.msg}", 'error')
                    return redirect(url_for('scraping_interface'))

                except Exception as e:
                    logging.exception("Errore durante lo scraping o la generazione del JSON")
                    flash(f"Errore durante l'elaborazione: {str(e)}", "error")
                    return redirect(url_for('scraping_interface'))

    return render_template('scraping_interface.html')

if __name__ == '__main__':
    app.run(debug=True)
