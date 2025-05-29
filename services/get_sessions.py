from services.database import db
from services.summary_generator import new_summary_generator
from datetime import datetime
def get_session(session_id,creator):
  sessions=db['Sessions']
  chat_info=sessions.find_one({'session_id':session_id,"creator":creator})
  summary,chat_history=chat_info['summary'],chat_info['chat_history']
  return summary,chat_history

def get_summary(session_id):
  sessions=db['Sessions']
  chat_info=sessions.find_one({'session_id':session_id})
  summary=chat_info['summary']
  return summary

def write_chat_to_history(session_id,current_summary,new_chat):
  sessions=db['Sessions']
  new_summary=new_summary_generator(current_summary,new_chat)
  sessions.update_one({
    "session_id" : session_id
    }, {
    "$push": {
      "chat_history": new_chat
    },
    "$set":{
      "summary":new_summary
    }
  })

def push_session(user_id,session_id):
  current_datetime = datetime.now()
  obj={
   "summary":'',
   "chat_history":[],
   'creator':user_id,
   'session_id':session_id,
   'updated_at':current_datetime
  }
  sessions=db['Sessions']
  sessions.insert_one(obj)
  users=db['Users']
  users.update_one({'user_id':user_id},{
    '$push':{
      "all_sessions":session_id
    }
  })
  

  
def get_all_sessions(user_id):
  users=db['Users']
  user_details=users.find_one({'user_id':user_id})
  all_sessions=user_details['all_sessions']
  return all_sessions
  


  