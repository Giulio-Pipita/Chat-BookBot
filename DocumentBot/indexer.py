from dotenv import load_dotenv
import openai
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.azure_openai import AzureOpenAIEmbeddings  
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS 
import os
from time import sleep

from aspose.pdf import EpubLoadOptions, Document
from asker import chunk_summary_gen, ask_summary, text_sum

#carico le variabili situate nel file .env per poter utilizzare l'API di openAI
load_dotenv(r".\environment.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME=os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_DEPLOYMENT_VERSION=os.getenv("OPENAI_DEPLOYMENT_VERSION")
OPENAI_MODEL_NAME=os.getenv("OPENAI_MODEL_NAME")

OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME=os.getenv("OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME")
OPENAI_ADA_EMBEDDING_MODEL_NAME=os.getenv("OPENAI_ADA_EMBEDDING_MODEL_NAME")

openai.api_type = "azure"
openai.api_base = OPENAI_DEPLOYMENT_ENDPOINT
openai.api_key = OPENAI_API_KEY
openai.api_version = OPENAI_DEPLOYMENT_VERSION

faiss_folder = "FAISS_index"
#serve per fare lo split dei caratteri
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 100,
    length_function = len
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME,
    azure_endpoint=OPENAI_DEPLOYMENT_ENDPOINT,
    chunk_size=1000
)


#riceve come input il path di un file pdf e lo restituisce 'loaded'
def loader(path):
    if(path.endswith(".pdf")):
        loader = PyPDFLoader(path)
    else:
        loader = TextLoader(path, encoding= 'latin-1')
    print("loaded!")
    return loader.load()


#creo i chunk da uno o più documenti loaded
def chopper(document):
    chunks = text_splitter.split_documents(documents= document)
    print("chopped! \n")
    return chunks


def new_faiss(chunks):
    print("nuova indicizzazione")
    vectorstore = FAISS.from_documents(documents = chunks, embedding =embeddings)
    vectorstore.save_local(r"C:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\FAISS_index")


def add_faiss(chunks):
    print("aggiungi indicizzazione")
    newIndex = FAISS.from_documents(documents = chunks, embedding =embeddings)
    vectorstore = FAISS.load_local(r"C:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\FAISS_index", embeddings)
    newIndex.merge_from(vectorstore)
    newIndex.save_local(r"C:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\FAISS_index")


def remove_faiss():
    for root, dirs, files in os.walk(os.getcwd()):
            if faiss_folder == os.path.basename(root) :
                for file in files:
                    if file.endswith(".faiss") or file.endswith(".pkl"):
                        pathfile = os.path.join(root, file)
                        os.remove(pathfile)
            if os.path.basename(root) == "epub_to_pdf":
                        for file in files:
                            if file.endswith(".pdf"):
                                pathfile = os.path.join(root, file)
                                os.remove(pathfile)


def delete_indexed_files():
    for root, dirs, files in os.walk(os.getcwd()):
            if "indexed_documents" == os.path.basename(root) :
                for file in files:
                    if file.endswith(".pdf") or file.endswith(".mp3") or file.endswith(".epub"):
                        pathfile = os.path.join(root, file)
                        os.remove(pathfile)

def index_document(chunks):
    selected_pages = []
    current_chars = 0
    i = 0
    chunk_lenght = 2500
    #chopped = chopper(loaded)
    j = 0
    print("inizio indicizzazione")
    for chunk in chunks:
        if current_chars + chunk_lenght <= 15000:
            selected_pages.append(chunk)
            current_chars += chunk_lenght
        else:
            sleep(2)
            if i == 0:
                new_faiss(selected_pages)    
            else: 
                add_faiss(selected_pages)
            selected_pages = []
            current_chars = 0
            selected_pages.append(chunk)
            current_chars += chunk_lenght
            print(f"totale pagine indicizzate: {j}")
            i+=1
        j+=1
    if selected_pages:
        if i == 0:
            new_faiss(selected_pages)
        else:
            add_faiss(selected_pages)
    print("fine indicizzazione del documento")


def add_document(loaded):
    selected_pages = []
    current_chars = 0
    i = 0
    chunk_lenght = 2500
    chopped = chopper(loaded)
    j = 0
    print("inizio indicizzazione")
    for chunk in chopped:
        if current_chars + chunk_lenght <= 15000:
            selected_pages.append(chunk)
            current_chars += chunk_lenght
        else:
            sleep(2)
            add_faiss(selected_pages)
            selected_pages = []
            current_chars = 0
            selected_pages.append(chunk)
            current_chars += chunk_lenght
            print(f"totale pagine indicizzate: {j}")
            i+=1
        j+=1
    if selected_pages:
        add_faiss(selected_pages)
    print("fine indicizzazione del documento")

#bookbot

def ePub_to_Pdf(path_ePub):
    file_path = os.path.basename(path_ePub)
    option = EpubLoadOptions()
    document = Document(path_ePub, option)
    document.save(f".\epub_to_pdf\{file_path[:-4]}pdf") 
    path = f".\epub_to_pdf\{file_path[:-4]}pdf"
    print("documento salvato")
    return path

def index_for_summary(chunks):
    i = 1
    summary = []
    for chunk in chunks:
        sum_chunks = chunk_summary_gen(chunk)
        summary.append(sum_chunks)
        if i %10 == 0:
            print(f"è stato fatto il riassunto di {i} chunk")
        i+=1
    print("fine chunks")    
    joined =' \n'.join(summary)
    with open(r".\epub_to_pdf\temp.txt", "w", encoding='utf-8') as file:
        file.write(joined)
    print("fatto")
    short_and_long(joined)

def short_and_long(joined):
    i = 1
    summary = []
    loaded = loader(r".\epub_to_pdf\temp.txt")
    chunks = chopper(loaded)
    if len(joined) <=20000:
        with open(r".\epub_to_pdf\riassunto_lungo.txt", "w", encoding='utf-8') as file:
            file.write(joined)
        long_summary_fixed = ask_summary("""dato il seguente testo, 
                                         che rappresenta il riassunto di un libro,
                                         NON è un discorso, rielaboralo mantenendo 
                                         la sua lunghezza e tutte le sue informazioni
                                         per renderlo più leggibile e comprensibile:""")
        with open(r".\epub_to_pdf\riassunto_lungo_fixed.txt", "w", encoding='utf-8') as f:
            f.write(long_summary_fixed)
        mini_riassunto = text_sum(chunks)
        with open(r".\epub_to_pdf\riassunto_corto.txt", "w", encoding= 'utf-8') as sum:
            sum.write(mini_riassunto)
        print("ho scritto i riassunti \n")
        return
    
    for chunk in chunks:
        sum_chunks = chunk_summary_gen(chunk)
        summary.append(sum_chunks)
        if i %10 == 0:
            print(f"è stato fatto il riassunto di {i} chunk ")
        i+= 1
    new_joined = ' \n'.join(summary)
    with open(r".\epub_to_pdf\temp.txt", "w", encoding = 'utf-8') as file:
        file.write(new_joined)
    print("here we go again")
    short_and_long(new_joined)

