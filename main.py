
from fastapi import FastAPI, Request, status, Depends, UploadFile, File, HTTPException
from routers.handle_sessions import create_session,load_old_sessions,end_session
from services.query_resolver import query_resolver
from typing import Annotated
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
    user_id=request.state.user_id
    session_id=create_session(user_id)
    return {'session_id':session_id}

@app.get("/session/query/{session_id}")
async def respond(session_id:str,request:Request):
    body=await request.body()
    data = json.loads(body)
    query=data.query
    response=query_resolver(session_id,query)
    return {"response":response}

@app.get('/session/load-chat/{session_id}')
async def load_prev_chat(session_id,request:Request):
    user_id=request.state.user_id
    session_id=create_session(user_id)
    summary,chat_history=load_old_sessions(session_id,user_id)
    return {"response":chat_history,"summary":summary}
    
@app.post('/session/upload-pdf/{session_id}')
async def embed_pdf(session_id,request:Request,file:UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = f"{upload_dir}/{session_id}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    uploadPDF('uploads/{session_id}',session_id)
    return {'response':'PDF successfully uploaded'}   


@app.post('/session/end-session/{session_id}')
async def delete_embeddings(session_id,request:Request,file: UploadFile):
    
    end_session(session_id)
    return {'response':'successfully deleted'}

@app.post('/session/delete-session/{session_id}')
def delete_session():
    return None