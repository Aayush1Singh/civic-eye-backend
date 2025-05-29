import os
from dotenv import load_dotenv
load_dotenv()
import requests
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"

# Map each label to the corresponding Redis index name
label_to_index = {
    "rights":            "constitution-vector",
    "substantive criminal law":      "bns-vector",       # BNS: Bharatiya Nyaya Sanhita
    "criminal procedure":            "bnss-vector",      # BNSS: Bharatiya Nagarik Suraksha Sanhita
    "corporate law":                 "company-vector",
    "contract law":                  "contract-vector",
    "consumer protection law":       "consumer-vector",
    "evidence law":                  "evidence-vector",
}

DOCUMENT_CLASSES = list(label_to_index.keys())

def classifier(user_query):    
  headers = {
    "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
  }
  def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()
  output = query({
    "inputs": user_query,
    "parameters": {"candidate_labels": DOCUMENT_CLASSES,"multi_label":True},
  })
  print(output)
  
  return output['labels'],output['scores']