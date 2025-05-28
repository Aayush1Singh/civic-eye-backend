import os
from dotenv import load_dotenv
load_dotenv()
import requests
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"

# Map each label to the corresponding Redis index name
label_to_index = {
    "constitutional law":            "constitution_vector",
    "substantive criminal law":      "BNS_vector",       # BNS: Bharatiya Nyaya Sanhita
    "criminal procedure":            "BNSS_vector",      # BNSS: Bharatiya Nagarik Suraksha Sanhita
    "corporate law":                 "company_vector",
    "contract law":                  "contract_vector",
    "consumer protection law":       "consumer_vector",
    "evidence law":                  "evidence_vector",
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
  
  return output['labels'],output['scores']