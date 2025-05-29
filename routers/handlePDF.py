from dotenv import load_dotenv
import os
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import fitz
from langchain_community.vectorstores.redis import Redis
from services.gemini_embedder import get_model
import redis
load_dotenv()
GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))


def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]
  
# embeddings = GoogleGenerativeAIEmbeddings(
#     model="models/embedding-001",     # Gemini embedding model
#     google_api_key=GEMINI_LIST[0]
# )

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])
  
  

def store_in_redis(docs, index_name):
    vectorstore = Redis.from_documents(
        documents=docs,
        embedding=get_model(),
        redis_url="redis://redis:6379",
        index_name=index_name
    )
    return vectorstore


def uploadPDF(pdf_path:str,session_id:str):
  print(pdf_path)
  text = extract_text_from_pdf(pdf_path)
  documents = chunk_text(text)
  if not documents:
    raise ValueError(f"No text found in PDF at {pdf_path}")  
  store_in_redis(documents, index_name=session_id)


__all__=['uploadPDF','end_session']
