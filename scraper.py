import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
import os
import zipfile

# Fonction qui permet de vérifier si un fichier est un fichier zip (pas besoin de l'extension)
def is_zip_file(file_path):
    try:
        with zipfile.ZipFile(file_path) as _:
            return True
    except zipfile.BadZipFile:
        return False

# Créer le dossier ou l'on va tout stocker
if not os.path.exists('data'):
    os.makedirs('data')


# Récupération des URL de pages où se trouvent les liens de téléchargement
url = 'https://transport.data.gouv.fr/datasets?q=agr%C3%A9gat'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

links = [title.select_one('a')['href'] for title in soup.find_all(class_='dataset__title')]
absolute_links = [urljoin(response.url, uri) for uri in links]

# On va sur chaque lien pour lister et récupérer les ressources afin de les télécharger et les décompresser dans des dossiers
for link in absolute_links:
    print("Collecting on : "+urlparse(link).path)
    # Créer le dossier
    nom_dossier = link.split('/')[-1]
    if not os.path.exists('data/'+nom_dossier):
        os.makedirs('data/'+nom_dossier)
    page_dir = 'data/'+nom_dossier

    # Récupération des ressources
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    resources = soup.select('.ressources-list > .resource')

    # On boucle sur les ressources pour les télécharger et les décompresser
    for resource in resources:
        # Création du dossier
        nom_dossier = resource.select_one('h4').text
        if not os.path.exists(page_dir+'/'+nom_dossier):
            os.makedirs(page_dir+'/'+nom_dossier)
        
        # Récupération du lien de téléchargement
        download_link = resource.select_one('.download-button')['href']

        # Télécharger le fichier zip depuis l'URL
        response = requests.get(download_link)

        if response.status_code == 200:
            with open(page_dir+'/'+nom_dossier+'/'+download_link.split('/')[-1], 'wb') as file:
                file.write(response.content)
                print(f"Fichier {download_link.split('/')[-1]} téléchargé avec succès !")

            zip = page_dir+'/'+nom_dossier+'/'+download_link.split('/')[-1]
            # Décompression du fichier zip
            if(is_zip_file(zip)):
                with zipfile.ZipFile(zip, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(zip))
                    print("Le fichier zip a été décompressé avec succès.")
            # Suppression du fichier zip
            os.remove(zip)
            print("Le fichier zip a été supprimé avec succès.")
