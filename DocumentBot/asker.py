from dotenv import load_dotenv
from langchain.callbacks import get_openai_callback
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import AzureChatOpenAI 
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser, HumanMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import FAISS
import openai
import os
import pickle


load_dotenv(r".\environment.env")

#gpt 3-5
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_DEPLOYMENT_ENDPOINT = os.getenv("OPENAI_DEPLOYMENT_ENDPOINT")
OPENAI_DEPLOYMENT_NAME=os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_DEPLOYMENT_VERSION=os.getenv("OPENAI_DEPLOYMENT_VERSION")
OPENAI_MODEL_NAME=os.getenv("OPENAI_MODEL_NAME")

OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME=os.getenv("OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME")
OPENAI_ADA_EMBEDDING_MODEL_NAME=os.getenv("OPENAI_ADA_EMBEDDING_MODEL_NAME")

#gpt 4

OPENAI_A4_KEY = os.getenv("API_KEY_4")
OPENAI_D4_ENDPOINT = os.getenv("DEPLOYMENT_ENDPOINT_4")
OPENAI_D4_NAME=os.getenv("DEPLOYMENT_NAME_4")
OPENAI_D4_VERSION=os.getenv("DEPLOYMENT_VERSION_4")
OPENAI_M4_NAME=os.getenv("MODEL_NAME_4")

#gpt3-5 16k
OPENAI_D16_NAME = os.getenv("DEPLOYMENT_NAME16")
OPENAI_D16_VERSION = os.getenv("DEPLOYMENT_VERSION16")
OPENAI_M16_NAME = os.getenv("MODEL_NAME16")

openai.api_type = "azure"
openai.api_base = OPENAI_DEPLOYMENT_ENDPOINT
openai.api_key = OPENAI_API_KEY
openai.api_version = OPENAI_DEPLOYMENT_VERSION

embeddings = OpenAIEmbeddings(
        deployment=OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME,
        model=OPENAI_ADA_EMBEDDING_MODEL_NAME, 
        openai_api_base=OPENAI_DEPLOYMENT_ENDPOINT,
        chunk_size=1,
        openai_api_type ="azure"
        )

llm = AzureChatOpenAI(
    azure_deployment= OPENAI_DEPLOYMENT_NAME,
    model_name = OPENAI_MODEL_NAME,
    azure_endpoint=OPENAI_DEPLOYMENT_ENDPOINT,
    openai_api_version="2023-07-01-preview",
    openai_api_key=OPENAI_API_KEY,
    openai_api_type="azure",
    temperature= 0.1,   
    max_tokens= 800, 
    )




text_fixer_sixteen = AzureChatOpenAI(
    azure_deployment= OPENAI_D16_NAME,
    model_name = OPENAI_M16_NAME,
    azure_endpoint=OPENAI_DEPLOYMENT_ENDPOINT,
    openai_api_version="2023-07-01-preview",
    openai_api_key=OPENAI_API_KEY,
    openai_api_type="azure",
    temperature= 0.5,           

)

text_fixer_for = AzureChatOpenAI(
    deployment_name= OPENAI_D4_NAME,
    model_name = OPENAI_M4_NAME,
    openai_api_base=OPENAI_D4_ENDPOINT,
    openai_api_version="2023-07-01-preview",
    openai_api_key=OPENAI_A4_KEY,
    openai_api_type="azure",
    temperature= 0.3,       
)


custom_template = """usando il seguente contesto genera un riassunto.
Se non sai qualcosa non inventarlo.
Non iniziare il riassunto con "il testo" o "il brano", evita informazioni inutili. 
{context}
Question:{question}
Riassunto:"""
CUSTOM_QUESTION_PROMPT = PromptTemplate.from_template(custom_template)

def chunk_summary_gen(chunk):
    mes = HumanMessage(
        content=f"genera un riassunto breve, massimo due frasi del seguente contesto che ne catturi le idee principali, qualora ci fossero informazioni relative ad 'Aspose' non inserirle. Sricordati che i nomi propri sono importanti. NON INIZIARE il riassunto con 'il testo' o 'il brano' o 'il protagonista' o 'la protagonista', riassumi  in modo molto sintetico. : {chunk.page_content}."
    )
    try:
        answer = llm([mes]).content
        mes2 = HumanMessage(
            content=f"senza usare le seguenti parole 'testo', 'brano', 'racconto', 'protagonista', rielabora il seguente testo in un discorso unico:{answer}"
        )
        risposta = llm([mes2]).content
    except Exception as e:
        print(f"error: {e}")
        risposta = ""    
    return risposta

def ask_summary(query):
    with open(r".\epub_to_pdf\riassunto_lungo.txt", "r", encoding = 'utf-8') as file:
        summary = file.read()
    mes = HumanMessage(
        content=f"{query} : {summary}"
    )
    risposta = text_fixer_sixteen([mes]).content
    return risposta


def text_sum(str):
    mes = HumanMessage(
        content=f"genera un riassunto breve del seguente contesto che ne catturi le idee principali, ricordati che i nomi propri sono importanti. NON INIZIARE il riassunto con 'il testo' o 'il brano' o 'il protagonista' o 'la protagonista', riassumi  in modo molto sintetico. : {str}."
    )
    risposta = text_fixer_sixteen([mes]).content
    return risposta







