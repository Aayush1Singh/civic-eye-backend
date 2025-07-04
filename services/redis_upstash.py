import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import httpx
def create_index(index_name):
    data = {"name":index_name,"region":"us-east-1","similarity_function":"COSINE","dimension_count":768}
    data = json.dumps(data)
    data=str(data)
    response = requests.post('https://api.upstash.com/v2/vector/index', data=data, auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API')))
    
async def get_index(index_name):
    print(index_name)
    async with httpx.AsyncClient(auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API'))) as client:
        response = await client.get(f"https://api.upstash.com/v2/vector/index/{index_name}")
        response.raise_for_status()  # optional: raise if we got 4xx/5xx
    op=response.json()
    return op['endpoint'],op['token']

def delete_index(index_name):
    response = requests.delete('https://api.upstash.com/v2/redis/database/:{index_name}' ,auth=(os.getenv('EMAIL'), os.getenv('UPSTASH_API')))
    op=response.content
    return op

    
    