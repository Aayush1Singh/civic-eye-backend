
from fastapi import FastAPI, Request, status, Depends, UploadFile, File, HTTPException
from routers.handle_sessions import create_session,load_old_sessions,end_session,load_all_sessions
from services.query_resolver import query_resolver
from routers.chat import get_answer_to_similar_cases

import json
app = FastAPI()
import os
import shutil
from routers.handlePDF import uploadPDF
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/new_session")
async def create_new_session(request: Request):
    print(request)
    body=await request.body()
    data = json.loads(body)
    user_id=data['user_id']
    print(user_id)
    # user_id=request.state.user_id
    session_id=create_session(user_id)
    
    return {'session_id':session_id}

@app.get("/session/query/{session_id}")
async def respond(session_id:str,request:Request):
    body=await request.body()
    data = json.loads(body)
    query=data["query"]
    print(query,session_id)
    response=query_resolver(session_id,query)
    return {"response":response}
@app.get('/session/load_chat/{session_id}')
async def load_prev_chat(session_id,request:Request):
    
    body=await request.body()
    data = json.loads(body)
    user_id=data['user_id']
    summary,chat_history=load_old_sessions(session_id,user_id)
    return {"response":chat_history,"summary":summary}
    
@app.post('/session/upload_pdf/{session_id}')
async def embed_pdf(session_id,request:Request,file:UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    _, file_extension = os.path.splitext(file.filename)
    if file_extension.lower() != ".pdf":
        return {'error': 'Only PDF files are supported.'}  
      
    file_location = f"{upload_dir}/{session_id}{file_extension}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    uploadPDF(f'uploads/{session_id}{file_extension}',session_id)
    return {'response':'PDF successfully uploaded'}  
 
@app.post('/session/end_session/{session_id}')
async def delete_embeddings(session_id,request:Request):
    
    end_session(session_id)
    return {'response':'successfully deleted'}

@app.post('/session/delete-session/{session_id}')
def delete_session():
    return None

@app.get('/session/get_similar/{session_id}')
async def get_similar_cases(session_id,request:Request):
    print('ejl')
    body=await request.body()
    data = json.loads(body)
    query=data['query']  
    user_id=data['user_id']
    return {'response':get_answer_to_similar_cases(query,session_id,user_id)}
@app.get('/get_all_sessions')
async def loader(request:Request):
    body=await request.body()
    data = json.loads(body)
    user_id=data['user_id']
    sessions=load_all_sessions(user_id)
    return {'response':sessions}




    
    
    