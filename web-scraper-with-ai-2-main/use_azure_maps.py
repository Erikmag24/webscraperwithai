#use_azure_maps.py

from azure.core.credentials import AzureKeyCredential
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
import config

def analyze_local_image(image_path):
    """ 
    Analizza un'immagine locale utilizzando Azure Vision.
    
    Args:
        image_path (str): Percorso locale dell'immagine.
    
    Returns:
        dict: Risultato dell'analisi dell'immagine.
    """
    # Configura il client Azure Vision
    endpoint = config.AZURE_ENDPOINT_IMAGE
    api_key = config.AZURE_API_KEY_IMAGE
    myAzureKeyCredential = AzureKeyCredential(api_key)
    
    # Usa il metodo corretto: analyze
    myImageAnalysisClient = ImageAnalysisClient(endpoint=endpoint, credential=myAzureKeyCredential)
    
    # Leggi l'immagine come binario
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    # Effettua l'analisi dell'immagine
    try:
        # Il metodo corretto è 'analyze', non 'analyze_image'
        response = myImageAnalysisClient.analyze(
            image_data,
            visual_features=[
                VisualFeatures.CAPTION, 
                VisualFeatures.DENSE_CAPTIONS, 
                VisualFeatures.PEOPLE, 
                VisualFeatures.OBJECTS, 
                VisualFeatures.TAGS, 
                VisualFeatures.READ
            ],
            gender_neutral_caption=True
        )
        return response
    except Exception as e:
        print(f"Errore durante l'analisi dell'immagine: {e}")
        return None

