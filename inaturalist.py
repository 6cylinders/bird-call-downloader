import os
import requests
import re
from dotenv import load_dotenv

# For example, this program will load samples of Australian Magpie calls

load_dotenv('naturalist.env')
base_dir = os.getenv("BASE_DIRECTORY") # substitute this with your folder path
scientific_name = "Gymnorhina tibicen" # serves as a unique identifier
request_url = f'https://api.inaturalist.org/v1/taxa?q={scientific_name}&rank=species' # rank=species added in to filter subspecies from response
species_response = requests.get(request_url).json() # turns API output into indexable JSON
# results is stored as a list in the response json to accommodate for multiple matches
# so we need to select the first value to index the JSON's attributes as intended
result = species_response['results'][0]
bird_taxon_id = result['id'] # needed for downloading from API
bird_name = result['preferred_common_name']

output_folder = base_dir + bird_name.replace(' ',  '_') # creating download directory

# Create output directory
if not os.path.exists(output_folder):
    os.makedirs(output_folder, exist_ok=True)


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def clean_extension(filename):
    base_name, extension = os.path.splitext(filename)
    if len(extension) > 4:  # If extension length is longer than 3 characters + dot
        extension = extension[:4]  # Keep only the dot and the first 3 characters
    return base_name + extension

per_page = 100  # Number of results per page
page = 1

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

