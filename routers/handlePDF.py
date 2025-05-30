from dotenv import load_dotenv
import os
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import fitz
# from langchain_community.vectorstores.redis import Redis
from services.gemini_embedder import get_model
# import redis
load_dotenv()
from pinecone import ServerlessSpec
# from langchain.vectorstores.redis import Redis
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
import uuid
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from services.redis_upstash import create_index,get_index,delete_index
from langchain_community.vectorstores.upstash import UpstashVectorStore
pinecone_api_key = os.getenv("PINECONE")
GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))
from upstash_vector import Index

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
  
  

def store_in_redis(docs, index_name,batch_size=50):
    print(create_index(index_name))
    url,token=get_index(index_name)
    print(url)
    try:
      index = Index(url=f"https://{url}", token=token)
      embeddings = GoogleGenerativeAIEmbeddings(
      model="models/embedding-001",     # Gemini embedding model
      google_api_key=GEMINI_LIST[0]
      )   
      
      vectorstore = UpstashVectorStore(
      embedding=embeddings,
      index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
      index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
      index=index,
      )
      vectorstore.add_documents(docs)
    except Exception as e:
      print(e)
      
    




def uploadPDF(pdf_path:str,session_id:str):
  print(pdf_path)
  text = extract_text_from_pdf(pdf_path)
  documents = chunk_text(text)
  if not documents:
    raise ValueError(f"No text found in PDF at {pdf_path}")  
  store_in_redis(documents, index_name=session_id)


__all__=['uploadPDF','end_session']
