from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
mongo_url = os.getenv("DB_URI", "mongodb://localhost:27017")
client=MongoClient(mongo_url)
# client = MongoClient(os.getenv('DB_URL'))
db=client['civic-eye']

# print(db['Users'].insert_one({'user_id':'6630c4cb3107b768cfeee508'}))
