from langchain_community.vectorstores.upstash import UpstashVectorStore
import os
from dotenv import load_dotenv
load_dotenv()
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import requests
import json
def create_index(index_name):
    data = {"name":index_name,"region":"us-east-1","similarity_function":"COSINE","dimension_count":768}
    data = json.dumps(data)
    data=str(data)
    print(data)
    response = requests.post('https://api.upstash.com/v2/vector/index', data=data, auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API')))
    print(response.text)
    
def get_index(index_name):
    print(index_name)
    response = requests.get(f"https://api.upstash.com/v2/vector/index/{index_name}",auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API')))
    op=response.json()
    print(op)
    return op['endpoint'],op['token']

def delete_index(index_name):
    response = requests.delete('https://api.upstash.com/v2/redis/database/:{index_name}' ,auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API')))
    op=response.content
    return op

    
    