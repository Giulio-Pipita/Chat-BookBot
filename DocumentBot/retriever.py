from dotenv import load_dotenv
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import AzureChatOpenAI 
from langchain.embeddings.azure_openai import AzureOpenAIEmbeddings  
from langchain.vectorstores import FAISS 
import os
import openai

from langchain.schema import HumanMessage



envpath = r".\environment.env"
load_dotenv(envpath) 
#gpt 3-5
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


embeddings = AzureOpenAIEmbeddings(
    azure_deployment=OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME,
    openai_api_version="2023-05-15",
    azure_endpoint=OPENAI_DEPLOYMENT_ENDPOINT,
    chunk_size=1000,
)

def asking(query):
    vectorstore = FAISS.load_local(r"C:\Users\giuli\OneDrive\Desktop\RepositoryWork\OpenAiSamples\DocumentBot\FAISS_index", embeddings) 
    embedding_vector = embeddings.embed_query(query)
    docs = vectorstore.similarity_search_by_vector(embedding_vector)
    chain = load_qa_chain(llm= llm, chain_type="stuff")
    answer = chain.run(input_documents = docs, question = f" rispondi alla seguente domanda, ma solo se pertinente ai documenti forniti altrimenti non rispondere: {query}")
    return answer
