import uuid
import redis
from datetime import datetime
from ..services.database import db
from ..services.get_sessions import push_session,get_session

def generate_session_id(user_id):
  return f"{user_id}_{uuid.uuid4()}"

def create_session(user_id):
  session_id=generate_session_id(user_id)
  push_session(user_id,session_id)
  return session_id

def end_session(session_id: str):
    """
    Drop the RediSearch index created for this session and delete its docs.
    Safe to call even if the index is already gone.
    """
    r = redis.Redis(host="localhost", port=6379)
    try:
        # DD = “Drop Docs” – removes every hash belonging to the index.
        r.execute_command(f"FT.DROPINDEX {session_id} DD")
    except redis.exceptions.ResponseError:
        # Index might not exist yet / anymore – ignore.
        pass
      

def load_old_sessions(session_id,user_id):
  return get_session(session_id,user_id)
