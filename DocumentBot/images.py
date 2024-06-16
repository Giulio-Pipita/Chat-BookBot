import aspose.words as aw
import glob
import mimetypes
import openai
import os
import requests
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient 
from azure.search.documents.models import *
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from PIL import Image

load_dotenv(r".\environment.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME=os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_DEPLOYMENT_VERSION=os.getenv("OPENAI_DEPLOYMENT_VERSION")
OPENAI_MODEL_NAME=os.getenv("OPENAI_MODEL_NAME")

OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME=os.getenv("OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME")
OPENAI_ADA_EMBEDDING_MODEL_NAME=os.getenv("OPENAI_ADA_EMBEDDING_MODEL_NAME")

openai.api_type = "azure"
openai.api_key = OPENAI_API_KEY
openai.api_version = OPENAI_DEPLOYMENT_VERSION

AZURE_SEARCH_SERVICE_ENDPOINT = "https://searchthesis.search.windows.net"
AZURE_SEARCH_SERVICE_API_KEY = os.environ["SEARCH_API_KEY"]
creds = AzureKeyCredential(AZURE_SEARCH_SERVICE_API_KEY)

VECTORIZE_IMAGE = "https://visionthesis.cognitiveservices.azure.com/computervision/retrieval:vectorizeImage?api-version=2023-02-01-preview&modelVersion=latest" 
VECTORIZE_TEXT = "https://visionthesis.cognitiveservices.azure.com/computervision/retrieval:vectorizeText?api-version=2023-02-01-preview&modelVersion=latest"
VISION_KEY = os.environ["VISION_KEY"]

images = []

text_fields = [
        SimpleField(name = "id", type = SearchFieldDataType.String, key = True),
        SimpleField(name = "content", type = SearchFieldDataType.String),
        SearchField(name = "embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),  
            vector_search_dimensions=1024,  
            vector_search_profile="HnswProfile",
        )        
]

image_fields = [
        SimpleField(name = "id", type = SearchFieldDataType.String, key = True),
        SimpleField(name  ="filepath", type = SearchFieldDataType.String),
        SearchField(name = "embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),  
            vector_search_dimensions=1024,  
            vector_search_profile="HnswProfile",
        )        
]

vector_search = VectorSearch(
    algorithms=[
        HnswVectorSearchAlgorithmConfiguration(
            name="algoHNSW",
            kind = VectorSearchAlgorithmKind.HNSW,
            parameters=HnswParameters(
                m=10,
                ef_construction = 1000,
                ef_search= 1000,
                metric= VectorSearchAlgorithmMetric.COSINE,
            ),
        ),
        ExhaustiveKnnVectorSearchAlgorithmConfiguration(
            name = "algoKNN",
            kind = VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
            parameters=ExhaustiveKnnParameters(
                metric= VectorSearchAlgorithmMetric.COSINE,
            ),
        ),
    ],
    profiles=[
        VectorSearchProfile(
            name= "HnswProfile",
            algorithm="algoHNSW",
        ),
        VectorSearchProfile(
            name="KnnProfile",
            algorithm="algoKNN",
        ),
    ],
    
)

semantic_config = SemanticConfiguration(
    name = "my-semantic-configuration",
    prioritized_fields= PrioritizedFields(
        prioritized_content_fields= [SemanticField(field_name="content")]
    )
)

semantic_settings = SemanticSettings(configurations= [semantic_config])

text_index = SearchIndex(name = "textindex",
                         fields = text_fields,
                         vector_search = vector_search,
                         semantic_settings = semantic_settings
)

text_index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name = "textindex", credential= creds)

text_search_client = SearchClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name= "textindex", credential= creds)

image_index = SearchIndex(name = "imageindex",
                    fields = image_fields,
                    vector_search = vector_search,
                    )

image_index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name = "imageindex", credential=creds)

image_search_client = SearchClient(endpoint=AZURE_SEARCH_SERVICE_ENDPOINT, index_name="imageindex", credential=creds)

def text_embedding(text):
    r = requests.post(VECTORIZE_TEXT, headers= {"Ocp-Apim-Subscription-Key": VISION_KEY}, json={"text": text})
    return r.json()["vector"]

def local_image_embed(image_file):
    with open(image_file, 'rb') as file:
        image_data = file.read()
        requested = requests.post(VECTORIZE_IMAGE, headers={"Ocp-Apim-Subscription-Key": VISION_KEY, "content-type" : "application/octet-stream"}, data=image_data)  
    if requested.status_code == 200:
        try:
            image_vector = requested.json()["vector"]
        except Exception as e:
            print(f"errore {e}")
            image_vector = None
        return image_vector
    else:
        print(f"errore nella richiesta di POST: {requested.status_code}, {requested.text}")

def extract_images(filepath):
    pdf = aw.Document(filepath)
    pdf.save(r".\extracted_images\pdf.docx")
    doc = aw.Document(r".\extracted_images\pdf.docx")

    shapes = doc.get_child_nodes(aw.NodeType.SHAPE, True)
    imageIndex = 0
    for shape in shapes:
        shape = shape.as_shape()
        if(shape.has_image):
            if shape.width > 150 and shape.height > 150:
                imageFileName = f"extracted_images/Image.ExportImages.{imageIndex}{aw.FileFormatUtil.image_type_to_extension(shape.image_data.image_type)}"
                shape.image_data.save(imageFileName)    
                embedded_image = local_image_embed(imageFileName)        
                images.append({
                    "id" : str(imageIndex),
                    "filepath" : imageFileName,
                    "embedding" :embedded_image
                })
                print("il documento " + os.path.basename(imageFileName)+ " è stato estratto")
                imageIndex += 1
    try:
        image_search_client.upload_documents(documents=images)
    except Exception as e:
        print(f"errore: {e}")
    print("indicizzazione completa")

def create_image_index():
    try:
        print("inizio creazione indice")
        image_index_client.create_index(image_index)
        print(f"l'indice {image_index.name} è stato creato")
    except Exception as e:
        print(f"errore: {e}")

def create_text_index():
    try:
        print("inizio creazione indice")
        text_index_client.create_index(text_index)
        print(f"l'indice {text_index.name} è stato creato")
    except Exception as e:
        print(f"errore: {e}")
    
def delete_text_index():
    target_folder = "epub_to_pdf"
    text_index_client.delete_index(text_index)
    for root, dirs, files in os.walk(os.getcwd()):
            if target_folder == os.path.basename(root):
                for file in files:
                    if file.endswith(".pdf"):
                        pathfile = os.path.join(root, file)
                        os.remove(pathfile)

def delete_image_index():
    target_folder = "extracted_images"
    image_index_client.delete_index(image_index)
    for root, dirs, files in os.walk(os.getcwd()):
            if target_folder == os.path.basename(root):
                for file in files:
                    if file.endswith(".jpeg") or file.endswith(".png") or file.endswith(".pdf"):
                        pathfile = os.path.join(root, file)
                        os.remove(pathfile)

def check_if_images():
    target_folder = "extracted_images"
    for root, dirs, files in os.walk(os.getcwd()):
            if target_folder == os.path.basename(root):
                if files:
                    return True
                else:
                    return False


def text_query(question):
    vector_query = VectorizableTextQuery(text=question, k=1, fields="embedding", exhaustive=True)
    r = text_search_client.search(search_text=None,
                                  vector_queries= [vector_query],
                                  select= ["id", "content"],
                                  top = 1
                                  )
    contents  = []
    print("step 2")
    for doc in r:
        print("step 3")
        if(doc["@search.score"] >= 0.70):
            print(f"id: {doc['id']}")
            print(f"score: {doc['@search.score']}")
            print(f"content: {doc['content']}")
            contents.append(doc['content'])


def text_image_query(question):
    text_vector = text_embedding(question)
    r = image_search_client.search(search_text= "*",
                             include_total_count= True,
                             vector_queries= [RawVectorQuery(vector=text_vector, k = 4, fields= "embedding")]
                             )
    all = []
    for doc in r:
        if doc["@search.score"] >=0.50:
            print(f"{doc['id']} -> score : {doc['@search.score']}")
            if doc["@search.score"] >=0.55:
                print("\n")
                all.append(doc["id"])    
                break
    try:
        img= Image.open("./extracted_images/Image.ExportImages." + all[0] + ".png").resize((200,150))
    except:
        try:
            img= Image.open("./extracted_images/Image.ExportImages." + all[0] + ".jpeg").resize((200,150)) 
        except:
            img = None        
    return img   
