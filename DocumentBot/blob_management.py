from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, BlobClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests

from speech_transcription import audio_transcription

enviropath = r".\environment.env"
load_dotenv(enviropath)

credential = DefaultAzureCredential()

storage_account_key = os.getenv('STORAGE_ACCOUNT_KEY') 
storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME')  
connection_string = os.getenv('CONNECTION_STRING') 
container_name = os.getenv('CONTAINER_NAME')

blob_service_client = BlobServiceClient.from_connection_string(conn_str = connection_string)


def add_blob_index(filename):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob="indexed.txt")
    download_stream = blob_client.download_blob()
    current_content = download_stream.readall()
    update_content = current_content + b"  \n" + filename.encode("utf-8")
    blob_client.upload_blob(data = update_content, overwrite = True)


def new_blob_index(filename):
    blob_client = blob_service_client.get_blob_client(container = container_name, blob = "indexed.txt")
    blob_client.upload_blob(data = filename.encode("utf-8"), overwrite = True )
    

def blob_reader():
    blob_client = blob_service_client.get_blob_client(container=container_name, blob="indexed.txt")
    download_stream = blob_client.download_blob()
    return(download_stream.content_as_text())

def upload_blob_file(path):
    audio_blob_client = BlobServiceClient.from_connection_string(conn_str = connection_string)
    container_client = audio_blob_client.get_container_client(container= "audio")
    filename = os.path.basename(path)[:-4]
    with open(path, "rb")as data:
        container_client.upload_blob(name=filename, data=data, overwrite = True)
    print("file caricato \n ")
    

