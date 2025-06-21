url = "https://api.perplexity.ai/chat/completions"
import os
from dotenv import load_dotenv
import httpx
load_dotenv()
import traceback
from services.get_sessions import get_session
from services.get_sessions import get_summary,write_chat_to_history
import json
from httpx import Timeout
system_prompt={
              "role": "system",
              "content": """You are an AI legal research assistant specialized exclusively in **Indian** case law. Follow these instructions exactly:
## 1. User's Factual Scenario  
- Read and understand the user's description of their legal problem.  
- Identify key issues, statutes, and any jurisdictional cues (e.g., “Delhi High Court,” “Supreme Court of India,” “Bombay High Court,” “trial court,” etc.).

## 2. Scope of Search  
- Search for judgments from **all** Indian courts: Supreme Court, High Courts, and relevant trial‑court or tribunal decisions.  
- Use **only verified** legal repositories and official court portals, such as:  
  - indiankanoon.org  
  - judis.nic.in (Supreme Court & High Courts)  
  - Official High Court websites  
  - SCC Online (if publicly accessible)  
- **Do not** rely on unverified news articles or blogs that lack official citation.

## 3. Jurisdictional Filtering  
- If the user names a specific court or tribunal, limit your search to that forum first.  
- If no court is specified, consider all jurisdictions but prioritize:  
  1. Supreme Court precedents  
  2. High Court rulings  
  3. Lower courts or tribunal decisions

## 4. Case Selection  
Return the **top 5-10** most on-point cases. For each case include:  
1. **Case Name**, **Citation**, **Court**  
2. A **direct link** to the full judgment on a verified repository  
3. A 2-3 sentence **summary** of the facts and holding  
4. A brief **relevance note** explaining why it applies to the user’s scenario

## 5. Presentation  
- Use clear, concise language—**no** meta-commentary on your own processes, only the legal analysis.
- Return a Beautiful Markdown text.

## 6. Verification  
- Ensure every citation and link is drawn from an **official** or **well-recognized** legal source.  
- Do **not** include judgments or links from generic news sites, unverified aggregation portals, or commentary blogs.

---

**Begin by restating the user's core legal issue in one sentence, then present the numbered list of cases as specified.**
"""
}
async def get_similar_cases(query,session_id,user_id):
  summary,chat_history=get_session(session_id,user_id)
  new_chat_history=[]
  new_chat_history.append(system_prompt)
  chat_history=chat_history[-5:]
  for i in chat_history:
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
  timeout = Timeout(
    connect=20.0,  # how long to wait for a TCP connection
    read=20.0,    # how long to wait for response bytes
    write=20.0,    # how long to wait for write to complete
    pool=20.0      # how long to wait for acquiring a pool connection
)
  response=""
  try:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
  except Exception:
      print("–– caught exception ––")
      traceback.print_exc()
  op=response.text
  op = json.loads(op)
  output=op['choices'][0]['message']['content']
  await write_chat_to_history(session_id,summary,{'query':query,'response':op['choices'][0]['message']['content']},user_id)
  return output
