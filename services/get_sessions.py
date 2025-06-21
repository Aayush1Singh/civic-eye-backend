from services.database import db
from services.summary_generator import new_summary_generator
from datetime import datetime
from services.gemini_title_llm import llm_cycle
from langchain.prompts import PromptTemplate
from bson import ObjectId
def isAvailable(user_id):
  doc = db['Users'].find_one({ "_id": ObjectId(user_id) })
  sessions = doc.get("all_sessions") or []
  if sessions:
      last_session = sessions[-1]
      current_datetime = datetime.now()
      print((current_datetime-last_session['updated_at']).total_seconds())
      if((current_datetime-last_session['updated_at']).total_seconds()>60):
        return True   
      else:
        return False
  else:
      return True
      print("No sessions found for this user.")
      
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
prompt=PromptTemplate(template="""Title Generator for Legal Sessions
You are a specialized title-generation model. Your goal is to distill a full legal interaction into a concise, semantically rich headline of no more than 8 words. Leverage both the user’s question and the AI’s answer to capture the key legal concept, statute or outcome.

Inputs:
• query:   “{query}”
• response: “{response}”

Requirements:
 Max 6 words, no punctuation at ends  
 Emphasize the legal topic (e.g., statute name, doctrine, remedy)  
 Use domain-specific terms (e.g., “BNSS”, “Contract Act”, “Bail”)  
 Avoid generic modifiers (“Overview”, “Guide”, “Discussion”)  
 Output only the title on a single line  
 Direclt Answer,no **meta commentary**

Example:
query: “What are the penalties under Section 138 of the Negotiable Instruments Act?”  
response: “Section 138 NI Act imposes up to 2 years imprisonment or fine for cheque dishonor, subject to issuer’s intent and notice requirements…”

Generated title:
Cheque Dishonor Penalties under Section 138 NI Act
""",input_variables=['query','response'])
async def generate_title(chat):
  llm=next(llm_cycle)
  chain= prompt | llm
  title= await chain.ainvoke({'query':chat['query'],'response':chat['response']})
  return title

async def write_chat_to_history(session_id,current_summary,new_chat,user_id):
  sessions=db['Sessions']
  users=db['Users']
  new_summary=new_summary_generator(current_summary,new_chat)
  if(current_summary==""):
    title=await generate_title(new_chat)
    users.update_one({'_id':ObjectId(user_id),'all_sessions.session_id':session_id}, {'$set': {'all_sessions.$.title': title}})
    print("title set")
  
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
      "all_sessions":{"session_id":session_id,"title":'New Chat','updated_at':current_datetime}
    }
  })
  
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
