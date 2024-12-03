#unisci_codici.py

import os

def salva_codici_in_txt(cartella, output_file):
    # Ottieni il percorso completo del file attuale
    file_corrente = os.path.abspath(__file__)
    
    # Apri il file di output per scrivere
    with open(output_file, 'w') as outfile:
        # Scorri tutti i file nella cartella
        for nome_file in os.listdir(cartella):
            percorso_file = os.path.join(cartella, nome_file)
            
            # Verifica che sia un file .py e non il file corrente
            if nome_file.endswith('.py') and os.path.abspath(percorso_file) != file_corrente:
                with open(percorso_file, 'r') as infile:
                    contenuto = infile.read()
                    outfile.write(f"{nome_file} -> {contenuto}\n")
                    outfile.write('\n' + '-'*40 + '\n')  # Separatore tra file

# Usa il percorso della cartella dove si trovano i file .py e il file di output
cartella = './'  # Cartella corrente, cambia se necessario
output_file = 'codici_uniti.txt'
salva_codici_in_txt(cartella, output_file)
