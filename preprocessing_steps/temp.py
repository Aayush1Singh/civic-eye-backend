import langchain
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('GEMINI_KEY_LIST'))
GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores.redis import Redis
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import fitz
import uuid
from pinecone import ServerlessSpec
from urllib.parse import urlparse
from langchain_community.vectorstores.upstash import UpstashVectorStore
import os
from services.gemini_embedder import embedder_cycle
from routers.handlePDF import store_in_redis

# Build Upstash Redis connection string
endpoint = os.getenv("UPSTASH_REDIS_REST_URL").replace("https://", "")
token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

REDIS_URL = f"rediss://:{token}@{endpoint}:6379"
# from langchain.vectorstores.redis import Redis
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
pinecone_api_key = os.getenv("PINECONE")
def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]
  
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embedList=[]
for i in GEMINI_LIST:
    
    try:
        temp = genai.configure(api_key=i)
        
        embedder= GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        embedList.append(embedder)
    except Exception as e:
        print(f"Error during model initialization: {e}")
        
        

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",     # Gemini embedding model
    google_api_key=GEMINI_LIST[1]
)

def get_embedding(text):
    counter=1
    counter%=len(GEMINI_LIST)
    model = embedList[counter]
    
    print(model.embed_content(content=text))
    return model.embed_content(text=text)["embedding"]
  
  
def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]



def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])
  
  
# def store_in_redis(docs, index_name,batch_size=50):
#     # vectorstore = Redis.from_documents(
#     #     documents=docs,
#     #     embedding=embeddings,
#     #     redis_url=REDIS_URL,
#     #     index_name=index_name
#     # )
#     store = UpstashVectorStore(
#     embedding=embeddings,
#     index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
#     index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
#     index=index_name
#     )   
#     store.add_documents(documents=docs)
    
    
#     # vectorstore.add_documents(documents=docs, index_name=index_name)
    
#     # return vectorstore
    

  
# 🔹 Load Constitution PDF
# "./preprocessed_docs/cropped_evidence_act.pdf","./preprocessed_docs/cropped_contract_act.pdf","./preprocessed_docs/cropped_consumer_act.pdf","./preprocessed_docs/cropped_constitution_of_india.pdf","./preprocessed_docs/cropped_company_act.pdf",

# 'evidence-vector','contract-vector','consumer-vector','constitution-vector','company-vector','
lt=["./preprocessed_docs/cropped_evidence_act.pdf","./preprocessed_docs/cropped_contract_act.pdf","./preprocessed_docs/cropped_consumer_act.pdf","./preprocessed_docs/cropped_constitution_of_india.pdf","./preprocessed_docs/cropped_company_act.pdf","./preprocessed_docs/cropped_BNSS.pdf","./preprocessed_docs/cropped_BNS.pdf"]

pt=['evidence-vector','contract-vector','consumer-vector','constitution-vector','company-vector','bns-vector','bnss-vector']

for i in range(len(lt)):
    pdf_path = lt[i]
    text = extract_text_from_pdf(pdf_path)

    # 🔹 Chunk it
    documents = chunk_text(text)

    # 🔹 Store in Redis
    
    store_in_redis(documents, index_name=pt[i])



# for pdf_path, index_name in zip(lt, pt):
#     # 1. extract full text
#     text = extract_text_from_pdf(pdf_path)
    
#     # 2. split into chunks
#     documents = chunk_text(text)
    
#     # 3. embed & store each chunk in Upstash Redis
#     store_embeddings(
#         docs=documents,
#         index_name=index_name,
#         get_embedding_fn=get_embedding
#     )