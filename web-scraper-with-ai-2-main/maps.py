#maps.py

from use_azure_maps import *
import folium
from selenium import webdriver
import time
import os
import glob
from IPython.display import Image, display
import math
from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini

def generate_map_tiles_and_process(
    lat_center, lon_center, area_width_m, area_height_m,
    zoom_level, map_width_px, map_height_px,
    chatbot_choice, prompt_template, use_azure
):
    """
    Genera mappe satellitari in tiles, invia i percorsi delle immagini ai chatbot per generare prompt,
    e ritorna un dizionario con le immagini e i prompt generati.

    I file vengono salvati nella directory 'static/maps'.
    """
    def calculate_mpp(latitude, zoom):
        return 156543.03392 * math.cos(math.radians(latitude)) / (2 ** zoom)

    # Calcola i metri per pixel e altre metriche
    mpp = calculate_mpp(lat_center, zoom_level)
    map_width_m = mpp * map_width_px
    map_height_m = mpp * map_height_px
    tiles_x = max(1, math.ceil(area_width_m / map_width_m))
    tiles_y = max(1, math.ceil(area_height_m / map_height_m))
    delta_lat = map_height_m / 111320
    delta_lon = map_width_m / (111320 * math.cos(math.radians(lat_center)))

    # Configura la directory per salvare le immagini
    static_folder = "static/maps"
    os.makedirs(static_folder, exist_ok=True)

    # Pulizia: elimina i file PNG esistenti nella directory
    old_files = glob.glob(os.path.join(static_folder, "*.png"))
    for file in old_files:
        os.remove(file)

    driver = webdriver.Chrome()

    try:
        # Genera mappe e salva gli screenshot
        for i in range(tiles_x):
            for j in range(tiles_y):
                new_lat = lat_center + ((j - tiles_y // 2) * delta_lat)
                new_lon = lon_center + ((i - tiles_x // 2) * delta_lon)

                # Genera la mappa con Folium
                m = folium.Map(
                    location=[new_lat, new_lon],
                    zoom_start=zoom_level,
                    tiles='Esri WorldImagery',
                    width=map_width_px,
                    height=map_height_px
                )

                # Salva la mappa come HTML temporaneo
                map_filename = f'map_{i}_{j}.html'
                m.save(map_filename)
                map_path = 'file://' + os.path.abspath(map_filename)

                # Carica la mappa e salva lo screenshot come PNG nella directory statica
                driver.get(map_path)
                time.sleep(2)
                screenshot_filename = os.path.join(static_folder, f'map_{i}_{j}.png')
                driver.set_window_size(map_width_px, map_height_px)
                driver.save_screenshot(screenshot_filename)

                # Rimuovi il file HTML temporaneo
                os.remove(map_filename)

        # Processa i file generati nella directory
        results = {}
        image_files = sorted(glob.glob(os.path.join(static_folder, "*.png")))  # Ordina i file per sicurezza
        for file_path in image_files:
            print(f"Processing: {file_path}")  # Debugging

            # Genera il prompt utilizzando il percorso assoluto
            prompt = prompt_template+str(os.path.abspath(file_path))
            print(f"Generated Prompt: {prompt}")

            # Chiama il chatbot selezionato
            if use_azure:
                response=analyze_local_image(str(os.path.abspath(file_path)))
            elif chatbot_choice == 'gpt':
                response = generate_with_gpt(prompt)
            elif chatbot_choice == 'ollama':
                response = generate_with_ollama(prompt)
            elif chatbot_choice == 'cohere':
                response = generate_with_cohere(prompt)
            elif chatbot_choice == 'gemini':
                response = generate_with_gemini(prompt)
            else:
                response = "Invalid chatbot choice."

            # Salva il percorso relativo per l'integrazione con Flask
            relative_path = os.path.relpath(file_path, 'static')
            results[relative_path] = response

        return results

    finally:
        driver.quit()
