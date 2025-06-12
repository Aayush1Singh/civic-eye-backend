from services.database import db
from services.summary_generator import new_summary_generator
from datetime import datetime
def get_session(session_id,creator):
  sessions=db['Sessions']
  chat_info=sessions.find_one({'session_id':session_id,"creator":creator})
  summary,chat_history=chat_info['summary'],chat_info['chat_history']
  return summary,chat_history

def get_summary(session_id,user_id):
  sessions=db['Sessions']
  chat_info=sessions.find_one({'session_id':session_id,'creator':user_id})
  summary,new_upload,documents=chat_info['summary'],chat_info['new_upload'],chat_info['documentIds']
  new_doc=-1;
  if(len(documents)>0):
    new_doc=documents[-1] 
  return summary,new_upload,new_doc

def write_chat_to_history(session_id,current_summary,new_chat):
  sessions=db['Sessions']
  new_summary=new_summary_generator(current_summary,new_chat)
  if(current_summary==""):
    print("")
  sessions.update_one({
    "session_id" : session_id
    }, {
    "$push": {
      "chat_history": new_chat
    },
    "$set":{
      "summary":new_summary,
      'new_upload':False
    }
  })

def push_session(user_id,session_id):
  current_datetime = datetime.now()
  obj={
   "summary":'',
   "chat_history":[],
   'creator':user_id,
   'session_id':session_id,
   'updated_at':current_datetime,
   'new_upload':0,
   'documentIds':[]
  }
  sessions=db['Sessions']
  sessions.insert_one(obj)
  users=db['Users']
  users.update_one({'_id':ObjectId(user_id)},{
    '$push':{
      "all_sessions":session_id
    }
  })
  
from bson import ObjectId
def update_sesssion_document_array(random,session_id):
  sessions=db['Sessions']
  sessions.update_one({'session_id':session_id},{
    '$push':{
      "documentIds":random
    },
    '$set':{
      "new_upload":True
    }
  })

def get_all_sessions(user_id):
  print('hellllppp',user_id)
  users=db['Users']
  user_details=users.find_one({'_id':ObjectId(user_id)})
  print(user_details)
 
  
  all_sessions=user_details['all_sessions']
  return all_sessions
  

def write_analysis_to_history(analysis,session_id,last_id):
  analysis_collection=db['Analysis']
  op= analysis_collection.insert_one({
    'session_id':session_id,
    'doc_id':last_id,
    'analysis':analysis
  })
  print('hello',op)
  
def load_analysis_from_history(session_id,doc_id):
  analysis_collection=db['Analysis']
  res= analysis_collection.find_one({
    'session_id':session_id,
    'doc_id':doc_id
  }) 
  
  return res['analysis']
