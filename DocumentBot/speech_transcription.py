import requests
from dotenv import load_dotenv
import json
import os
from time import sleep

envpath = r".\environment.env"
load_dotenv(envpath) 

SPEECH_ENDPOINT  = os.getenv('SPEECH_ENDPOINT_NEW')
SPEECH_KEY = os.getenv('SPEECH_KEY')
url = SPEECH_ENDPOINT
headers = {
    "Ocp-Apim-Subscription-Key": SPEECH_KEY,
    "Content-Type": "application/json",
}



def audio_transcription(filename):
    payload = {
        "contentUrls": [
            f"https://audiostorage00.blob.core.windows.net/audio/{filename}"
        ],
        "locale": "en-US",
        "displayName": "My Transcription",
        "model": None,
        "properties": {
            "wordLevelTimestampsEnabled": True,
            "languageIdentification": {"candidateLocales": ["en-US", "de-DE", "es-ES", "it-IT"]},
        },
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = json.loads(response.text)
    files_url = response_data["links"]["files"]

    while True:
        response2 = requests.get(files_url,headers=headers)
        data = json.loads(response2.text)
        values = data["values"]
        print(values)
        if values:
            break
        sleep(2)

    print("\n")

    for value in values:
        text_url = value.get("links", {}).get("contentUrl", None)
        if text_url:
            print(text_url)
            break

    print("\n")

    response3 =requests.get(text_url, headers=headers)
    text_data = json.loads(response3.text)
    text = text_data["combinedRecognizedPhrases"][0]["lexical"]
    with open (r".\audio_transcription.txt", "w")as transcription:
        transcription.write(text)
    print("file copiato")
    





