import os
from dotenv import load_dotenv
import itertools
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))
embedList=[]
counter=0
for i in GEMINI_LIST:
    try:
        embedder=GoogleGenerativeAIEmbeddings(
                  model="models/embedding-001",
                  google_api_key=i
                )
        embedList.append(embedder)
    except Exception as e:
        print(f"Error during model initialization: {e}")
        
def get_model():
  counter+=1;
  counter=(counter)%len(embedList)
  return embedList[counter];


embedder_cycle = itertools.cycle(embedList)   # round-robin iterator
def return_model():
  return next(embedder_cycle)

__all__ = ['get_model']