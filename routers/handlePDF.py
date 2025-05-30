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

pinecone_api_key = os.getenv("PINECONE")
GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))


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
    # vectorstore = Redis.from_documents(
    #     documents=docs,
    #     embedding=embeddings,
    #     redis_url="redis://localhost:6379",
    #     index_name=index_name
    # )
    
    embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",     # Gemini embedding model
    google_api_key=GEMINI_LIST[0]
    )   
    pc=Pinecone(api_key=pinecone_api_key)
    
    if not pc.has_index(index_name):
        pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    index = pc.Index(index_name) 
    
    vector_store=PineconeVectorStore(index=index, embedding=embeddings)

    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        ids = [str(uuid.uuid4()) for _ in range(len(batch_docs))]
        try:
            vector_store.add_documents(documents=batch_docs, ids=ids)
        except Exception as e:
            print(f"❌ Failed to upload batch {i // batch_size + 1}: {e}")  
    # ids = [str(uuid.uuid4()) for _ in range(len(docs))]
    
    # vector_store.add_documents(documents=docs, ids=ids)
    
    # return vectorstore




def uploadPDF(pdf_path:str,session_id:str):
  print(pdf_path)
  text = extract_text_from_pdf(pdf_path)
  documents = chunk_text(text)
  if not documents:
    raise ValueError(f"No text found in PDF at {pdf_path}")  
  store_in_redis(documents, index_name=session_id)


__all__=['uploadPDF','end_session']
