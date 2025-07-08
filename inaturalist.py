import os
import requests
import re
from dotenv import load_dotenv

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def clean_extension(filename):
    base_name, extension = os.path.splitext(filename)
    if len(extension) > 4:  # If extension length is longer than 3 characters + dot
        extension = extension[:4]  # Keep only the dot and the first 3 characters
    return base_name + extension

def inaturalist_dl(common_name, bird_taxon_id, output_folder):
    per_page = 100  # Number of results per page
    page = 1

    print(f"Downloading audio recordings of the {common_name}...")

    while True:
    # Fetch observations with audio
        url = f"https://api.inaturalist.org/v1/observations?taxon_id={bird_taxon_id}&has[]=sounds&per_page=100&page={page}"
        response = requests.get(url).json()

        if 'results' not in response or not response['results']:
                print(f"No more results found on page {page}.")
                break

        # Loop through results and download audio
        for result in response.get("results", []):
            if "sounds" in result:
                for sound in result["sounds"]:
                    audio_url = sound["file_url"]

                    try:
                        filename = sanitize_filename(os.path.basename(audio_url))
                        filename = clean_extension(filename)
                        filepath = os.path.join(output_folder, filename)

                        if os.path.exists(filepath):
                            print(f"File already exists, skipping: {filename}")
                            continue

                        with requests.get(audio_url, stream=True) as audio_response:
                            with open(filepath, 'wb') as audio_file:
                                audio_file.write(audio_response.content)
                        print(f"Downloaded: {filename}")
                    except TypeError:
                        continue


        if len(response['results']) < per_page:
                print(f"Downloaded all available data (page {page}).")
                break
        else:
            page += 1

def xeno_dl(scientific_name, common_name, output_folder):

    print('(xeno) fetching data on the', common_name)
    load_dotenv("naturalist.env")
    key = os.getenv("XENO_API_KEY")
    base_url = "https://xeno-canto.org/api/3/recordings"
    page = 1
    species = scientific_name.replace(" ", "+")

    print("(xeno) downloading data for the", common_name)
    while True:
        url = f'{base_url}?query=sp:"{species}"&key={key}&page={page}'
        response = requests.get(url)
        contents = response.json()
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
        for rec in contents.get("recordings", []):
            file_url = rec['file']  # file URL is relative
            ext = file_url.split('.')[-1]
            file_name = f"{rec['id']}.{ext}"
            file_path = os.path.join(output_folder, file_name)


            if not os.path.exists(file_path):
                print(f"Downloading {file_name}...")
                audio = requests.get(file_url)
                if audio.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(audio.content)
                else:
                    print(f"Failed to download {file_name}: HTTP {audio.status_code}")
            else:
                print(f"{file_name} already exists, skipping.")

        if page >= int(contents.get("numPages", 0)):
            break
        page += 1

        print("Download complete.")


def download(scientific_name):
    """
    Downloads all recordings of a given species from both iNaturalist and xeno-canto
    :param scientific_name: Genus name followed by the species name e.g. 'Corvus Orru' for the Torresian Crow
    :return: None
    """

    print('Getting species data...')
    load_dotenv('naturalist.env')
    base_dir = os.getenv("BASE_DIRECTORY")  # substitute this with your folder path
    request_url = f'https://api.inaturalist.org/v1/taxa?q={scientific_name}&rank=species'  # rank=species added in to filter subspecies from response
    species_response = requests.get(request_url).json()  # turns API output into indexable JSON
    # results is stored as a list in the response json to accommodate for multiple matches
    # so we need to select the first value to index the JSON's attributes as intended
    result = species_response['results'][0]
    bird_taxon_id = result['id']  # needed for downloading from API
    bird_name = result['preferred_common_name']
    output_folder = base_dir + bird_name.replace(' ', '_')  # crafting download directory

    # Create output directory
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    print('Initialising iNaturalist download...')
    inaturalist_dl(common_name=bird_name, bird_taxon_id=bird_taxon_id, output_folder=output_folder)
    xeno_dl(scientific_name, common_name=bird_name, output_folder=output_folder)


if __name__ == '__main__':
    dl_list = [
    "Ninox boobook",  # Australian Boobook
    "Threskiornis molucca", # Australian Ibis
    "Gymnorhina tibicen", # Australian Magpie
    "Scythrops novaehollandiae", # Channel-Billed Cuckoo
    "Psophodes olivaceus", # Eastern Whipbird
    "Cacomantis flabelliformis", # Fan-Tailed Cuckoo
    "Dacelo novaeguineae", # Laughing Kookaburra
    "Philemon corniculatus", # Noisy Friarbird
    "Eudynamys orientalis", # Pacific/Eastern Koel
    "Strepera graculina", # Pied Currawong
    "Trichoglossus moluccanus", # Rainbow Lorikeet
    "Anthochaera carunculata", # Red Wattlebird
    "Pardalotus punctatus", # Spotted Pardalote
    "Cacatua galerita", # Sulphur-Crested Cockatoo
    "Polytelis swainsonii", # Superb Parrot
    "Corvus orru" # Torresian Crow
]
    for i in dl_list:
        download(i)



