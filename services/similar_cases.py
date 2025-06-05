import requests
url = "https://api.perplexity.ai/chat/completions"
import os
from dotenv import load_dotenv
load_dotenv()
from services.get_sessions import get_session
from services.get_sessions import get_summary,write_chat_to_history
import json
system_prompt={
              "role": "system",
              "content": """You are an AI legal research assistant specialized exclusively in Indian case law. You must:
1. Accept a user’s factual description of their legal scenario.
2. Identify key legal issues, statutes, and jurisdictional hints (e.g., “Delhi High Court,” “Supreme Court of India,” “Bombay High Court”).
3. Search only on verified sites like www.indiankanoon.org or related sites for relevant judgments.
   • If a specific court is mentioned, restrict your search to that court.
   • Otherwise, consider all Indian courts but prioritize higher courts first.
4. Return the top 5-10 most on-point cases, each with:
   a. A direct link to the judgment on indiankanoon.org.
   b. The case name, citation, and court.
   c. A 2-3-sentence summary of facts and holding.
   d. A brief note on why it's relevant to the user's described scenario.
5. Do not reference or search any sources outside India or indiankanoon.org.
6. Present your answer in clear, numbered sections.
7. Just output the legal answer directly. No meta-commentary.
"""
}
async def get_similar_cases(query,session_id,user_id):
  summary,chat_history=get_session(session_id,user_id)
  new_chat_history=[]
  new_chat_history.append(system_prompt)
  chat_history=chat_history[-5:]
  for i in chat_history:
    #   print(i)
      new_chat_history.append({"role":'user',"content":i['query']})
      new_chat_history.append({'role':'assistant','content':i['response']})
      
  new_chat_history.append({
              "role": "user",
              "content": query
          })
  
  payload = {
      "model": "sonar",
      "messages": new_chat_history
  }
  headers = {
      "Authorization": f"Bearer {os.getenv('PERPLEXITY')}",
      "Content-Type": "application/json"
  }
  response =requests.request("POST", url, json=payload, headers=headers)
  op=response.text
  op = json.loads(op)
  print(op,type(op))
  # op=eval(op)
  print(op)
  output=op['choices'][0]['message']['content']
  write_chat_to_history(session_id,summary,{'query':query,'response':op['choices'][0]['message']['content']})
  return output



  
# get_similar_cases('tell me about cases where animal owner was plead guilty for mishandling animals leading to road accidents.')
