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
# from langchain.vectorstores.redis import Redis
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import fitz
import uuid
from pinecone import ServerlessSpec
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
  

embedList=[]
for i in GEMINI_LIST:
    try:
        temp = genai.configure(api_key=i)
        
        embedder= genai.GenerativeModel("embedding-001")
        embedList.append(embedder)
    except Exception as e:
        print(f"Error during model initialization: {e}")
        
        

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",     # Gemini embedding model
    google_api_key=GEMINI_LIST[0]
)
counter=0;
def get_embedding(text):
    counter+=1
    counter%=len(GEMINI_LIST)
    model = embedList[counter]
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
  
  

def store_in_redis(docs, index_name,batch_size=50):
    # vectorstore = Redis.from_documents(
    #     documents=docs,
    #     embedding=embeddings,
    #     redis_url="redis://localhost:6379",
    #     index_name=index_name
    # )
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
    ids = [str(uuid.uuid4()) for _ in range(len(docs))]
    
    # vector_store.add_documents(documents=docs, ids=ids)
    
    # return vectorstore

  
# 🔹 Load Constitution PDF
# "./preprocessed_docs/cropped_evidence_act.pdf","./preprocessed_docs/cropped_contract_act.pdf","./preprocessed_docs/cropped_consumer_act.pdf","./preprocessed_docs/cropped_constitution_of_india.pdf","./preprocessed_docs/cropped_company_act.pdf",

# 'evidence-vector','contract-vector','consumer-vector','constitution-vector','company-vector','
lt=["./preprocessed_docs/cropped_BNSS.pdf","./preprocessed_docs/cropped_BNS.pdf"]
pt=['bns-vector','bnss-vector']

for i in range(len(lt)):
    pdf_path = lt[i]
    text = extract_text_from_pdf(pdf_path)

    # 🔹 Chunk it
    documents = chunk_text(text)

    # 🔹 Store in Redis
    store_in_redis(documents, index_name=pt[i])
