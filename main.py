
from fastapi import FastAPI, Request, status, Depends, UploadFile, File, HTTPException, Cookie,Query
from routers.handle_sessions import create_session,load_old_sessions,end_session,load_all_sessions
from services.query_resolver import query_resolver
from routers.chat import get_answer_to_similar_cases
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

import os
from dotenv import load_dotenv
import shutil
from routers.handlePDF import uploadPDF
from services.database import db
import jwt
import datetime
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "https://localhost:5173",
     "http://127.0.0.1:5173",
     "http://localhost:8080",
    "https://localhost.tiangolo.com",
    "https://query-interface-gleam.vercel.app",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET_KEY=os.getenv('JWT_KEY')
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/new_session")
async def create_new_session(request: Request):
    print(request)
    user_id = getattr(request.state, "user_id", None)
    print('lolololo ',user_id)
    # user_id=request.state.user_id
    session_id=create_session(user_id)
    
    return {'message':'success','session_id':session_id}

@app.get("/session/query/{session_id}")
async def respond(session_id:str,request:Request,query:str = Query(None)):
    
    # query=data["query"]
    print(query,session_id)
    user_id = getattr(request.state, "user_id", None)
    response=query_resolver(session_id,query,user_id)
    return {'message':'success',"response":response}

@app.get('/session/load_chat/{session_id}')
async def load_prev_chat(session_id,request:Request):
    
    # body=await request.body()
    # data = json.loads(body)
    # user_id=data['user_id']
    print('in load_char ',session_id)
    user_id = getattr(request.state, "user_id", None)
    summary,chat_history=load_old_sessions(session_id,user_id)
    return {'message':'success',"response":chat_history,"summary":summary}
    
@app.post('/session/upload_pdf/{session_id}')
async def embed_pdf(session_id,request:Request,file:UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    _, file_extension = os.path.splitext(file.filename)
    if file_extension.lower() != ".pdf":
        return {'message':'failed','error': 'Only PDF files are supported.'}  
      
    file_location = f"{upload_dir}/{session_id}{file_extension}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)    
    uploadPDF(f'uploads/{session_id}{file_extension}',session_id)
    return {'message':'success','response':'PDF successfully uploaded'}  
 
@app.post('/session/end_session/{session_id}')
async def delete_embeddings(session_id,request:Request):
    
    end_session(session_id)
    return {'message':'success','response':'successfully deleted'}

@app.post('/session/delete-session/{session_id}')
def delete_session():
    return None

@app.get('/session/get_similar/{session_id}')
async def get_similar_cases(session_id,request:Request,query:str = Query(None)):
    print('ejl')
    
    user_id = getattr(request.state, "user_id", None)
    print(user_id,query,session_id)
    res=await get_answer_to_similar_cases(query,session_id,user_id)
    print(res)
    return {'message':'success','response':res}
@app.get('/get_all_sessions')
async def loader(request:Request):
    user_id = getattr(request.state, "user_id", None)
    print("hellp ",user_id)
    sessions=load_all_sessions(user_id)
    return {'messaage':'success','response':sessions}


async def checkForDuplicate(email):
    if(email is None): 
        return False
    users=db['Users']
    print(users)
    op=users.find_one({'email':email})
    
    print(op)
    if(op is None):
        return False
    if len(op)>0:
        return True
    else:
        return False
# Generate a key (only do this once and save the key securely)

# Load the previously generated key
def load_key():
    with open("secret.key", "rb") as key_file:
        return key_file.read()

# Encrypt the password
def encrypt_password(password: str, key: bytes) -> bytes:
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted

# Decrypt the password
def decrypt_password(encrypted_password: bytes, key: bytes) -> str:
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_password)
    return decrypted.decode()

def create_new_user(email,password):
    users=db['Users']
    key = load_key()

    encrypted = encrypt_password(password, key)

    new_user=users.insert_one({'email':email,'password':encrypted,'chat_history':[]})
    return new_user
    # decrypted = decrypt_password(encrypted, key)
    # print(f"Decrypted: {decrypted}")
    
def generate_jwt(payload: dict, expires_in_minutes=60) -> str:
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_in_minutes)
    token = jwt.encode(payload_copy, SECRET_KEY, algorithm="HS256")
    return token
  
@app.post('/signup')
async def signup(request:Request):
    body=await request.body()
    data = json.loads(body)
    print(data)
    email,password=data['email'],data['password']
    print(email,password)
    if( await checkForDuplicate(email)):
        return {"message":"failed"}
    else:
        user_id=create_new_user(email,password)
        token=generate_jwt({'user_id':str(user_id.inserted_id),'email':email})
        print(token)
        response = JSONResponse(content={"message": "success"})
        response.set_cookie(
    key="token",
    value=token,
    httponly=True,      # True = JavaScript can't read it; False = JS can read
    max_age=3600,
    secure=True,        # True only for HTTPS; you're on HTTP
    samesite="none"      # Required for cross-origin cookies
)
        return response

def checkCred(email,password):
    key = load_key()
    users=db['Users']
    user=users.find_one({'email':email})
    encrypted=user['password']
    decrypted = decrypt_password(encrypted, key)
    if(decrypted==password):
        return True
    else:
        return False
  
  
  

# Function to decode and verify JWT token
def verify_jwt(token: str) -> dict:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"decoded":decoded,"message":'success'}
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired",'message':'failed'}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token",'message':'failed'}
    
def load_user_id(email):
    key = load_key()
    users=db['Users']
    user=users.find_one({'email':email})
    return user['_id']
import http.cookies
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next,token:str=Cookie(None)):
        if request.method == "OPTIONS":
            return await call_next(request)
        # print('jell',token)
        raw_cookie = request.headers.get("cookie") 
        print(raw_cookie)
        
        token=None
        if raw_cookie:
            cookies = http.cookies.SimpleCookie()
            cookies.load(raw_cookie)
            if "token" in cookies:
                token = cookies["token"].value
                print(token)
        
        print(token)
        result=verify_jwt(token)
        print(result)
        if request.url.path.startswith("/signin") or request.url.path.startswith("/signup") or request.url.path.startswith("/verify") :
            return await call_next(request)
        if(result["message"]=='success'):
            request.state.user_id=result['decoded']['user_id']
        elif result["message"] == 'failed' and result['error'] == 'Invalid token':
            raise HTTPException(status_code=402, detail="Invalid token")
        else:
            raise HTTPException(status_code=401, detail="Token expired")
            
            
        # auth_header = request.headers.get("Authorization")
        # if not auth_header or not auth_header.startswith("Bearer "):
        #     raise HTTPException(status_code=401, detail="Unauthorized")
        # token = auth_header.split(" ")[1]
        # try:
        #     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        #     request.state.user = payload  # Attach user info to the request if needed
        # except jwt.ExpiredSignatureError:
        #     raise HTTPException(status_code=401, detail="Token expired")
        # except jwt.InvalidTokenError:
        #     raise HTTPException(status_code=401, detail="Invalid token")
        # if request.url.path.startswith("/verify"):
        #     return {'messgae':'success'}
        
        return await call_next(request)

# Add the middleware to the app
app.add_middleware(JWTAuthMiddleware)
@app.post('/signin')
async def signin(request:Request):
    body=await request.body()
    data = json.loads(body)
    email,password=data['email'],data['password']
    if checkCred(email,password):
        user_id=load_user_id(email)
        token=generate_jwt({"user_id":str(user_id),"email":email})
        response = JSONResponse(content={"message": "success"})
        response.set_cookie(
    key="token",
    value=token,
    httponly=True,      # True = JavaScript can't read it; False = JS can read
    max_age=3600,
    secure=True,        # True only for HTTPS; you're on HTTP
    samesite="none"      # Required for cross-origin cookies
)
        return response
    else:
        return {'message':'failed'}
    


@app.post('/verify')
async def verify_user(token: str = Cookie(None)):
    return verify_jwt(token)