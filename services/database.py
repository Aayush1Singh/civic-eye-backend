from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
mongo_url = os.getenv("DB_URI", "mongodb://localhost:27017")
client=MongoClient(mongo_url)
db=client['civic-eye']

