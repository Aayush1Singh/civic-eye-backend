import uuid
# import redis
from services.get_sessions import push_session,get_session,get_all_sessions,isAvailable
from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()
from services.redis_upstash import delete_index
def generate_session_id(user_id):
  return f"{user_id}_{uuid.uuid4()}"

def create_session(user_id):
    if isAvailable(user_id):
      print('ok')
      session_id=generate_session_id(user_id)
      push_session(user_id,session_id)
      return session_id
    else:
      return None
    
    

def end_session(session_id: str):
  delete_index(session_id)      

def load_old_sessions(session_id,user_id):
  return get_session(session_id,user_id)

def load_all_sessions(user_id):
  return get_all_sessions(user_id)
