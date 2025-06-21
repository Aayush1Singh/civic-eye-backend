
from fastapi import FastAPI, Request, HTTPException, Cookie,Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.handle_sessions import create_session,load_old_sessions,end_session,load_all_sessions
from services.query_resolver import query_resolver
from routers.chat import get_answer_to_similar_cases
from starlette.middleware.base import BaseHTTPMiddleware
import json
app = FastAPI()
from cryptography.fernet import Fernet
from services.file_analyzer import analyze_document
import os
from services.database import db
import jwt
import datetime
from services.get_sessions import load_analysis_from_history,update_sesssion_document_array 
origins = [
    "https://localhost:5173",
     "http://127.0.0.1:5173",
     "http://localhost:8080",
    "https://query-interface-gleam.vercel.app",
    "https://kanun-legalai.vercel.app/"
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
    try:
        user_id = getattr(request.state, "user_id", None)
        session_id=create_session(user_id)
        if session_id is not None:
            return {'status':'success','session_id':session_id}
        else:
            return {'status':'failed','message':'Please try after some time, rate limit exceeded'}
    except Exception as e:
        return {'staus':'failed','message':'Session could not be created'}
    

@app.get("/session/query/{session_id}")
async def respond(session_id:str,request:Request,query:str = Query(None),isUpload:bool =Query(None)):
    try:
        print(query,session_id)
        user_id = getattr(request.state, "user_id", None)
        response=await query_resolver(session_id,query,user_id,isUpload)
        return {'status':'success',"response":response}
    except Exception as e:
        print(e)
        return {'status':'failed','message':'Server Could not respond'}

@app.get('/session/load_chat/{session_id}')
async def load_prev_chat(session_id,request:Request):
    try:
        print('in load_char ',session_id)
        user_id = getattr(request.state, "user_id", None)
        summary,chat_history=load_old_sessions(session_id,user_id)
        return {'status':'success',"response":chat_history,"summary":summary}
    except Exception:
        return {'status':'failed','message':'Could not load chat'}
     
@app.post('/session/end_session/{session_id}')
async def delete_embeddings(session_id):
    try:
        end_session(session_id)
        return {'status':'success','response':'successfully deleted'}
    except Exception:
        return {'status':'failed','message':'Could not delete Session'}

@app.post('/session/delete_session/{session_id}')
def delete_session():
    return None

@app.get('/session/get_similar/{session_id}')
async def get_similar_cases(session_id,request:Request,query:str = Query(None)):
    try:
        user_id = getattr(request.state, "user_id", None)
        res=await get_answer_to_similar_cases(query,session_id,user_id)
        return {'status':'success','response':res}
    except Exception as e:
        print(e)
        return {'status':'failed','message':'Could not respond to query'}
    
@app.get('/get_all_sessions')
async def loader(request:Request):
    try:
        user_id = getattr(request.state, "user_id", None)
        print("hellp ",user_id)
        sessions=load_all_sessions(user_id)
        return {'status':'success','response':sessions}
    except:
        return {'status':'failed','message':'Could not load previous chats'}

@app.get('/session/analyze/{session_id}')
async def analyze_doc(session_id,request:Request):
    try:
        print('hello')
        if(session_id==None or session_id=='null'):
            return {"status":'failed','response':[]}
        user_id = getattr(request.state, "user_id", None)
        op=await  analyze_document(session_id,user_id)
        return {'response':op,"status":'success'}
    except Exception:
        return {'status':'failed','message':'Could not analyze File'}

async def checkForDuplicate(email):
    try:
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
    except Exception:
        return False
def load_key():
    with open("secret.key", "rb") as key_file:
        return key_file.read()

def encrypt_password(password: str, key: bytes) -> bytes:
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted

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


def generate_jwt(payload: dict, expires_in_minutes=60) -> str:
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_in_minutes)
    token = jwt.encode(payload_copy, SECRET_KEY, algorithm="HS256")
    return token

@app.post('/verify')
async def verify_user(token: str = Cookie(None)):
    try:
        return verify_jwt(token)
    except Exception:
        return {'status':'failed','message':'Could not verify User'}

@app.get('/session/load_analysis/{session_id}')
async def load_analysis(session_id,doc_id:str=Query(None)):
    try:
        print(session_id,doc_id)
        analysis=load_analysis_from_history(session_id,doc_id)
        return {'response': analysis,'status':'success'}
    except Exception:
        return {'status':'failed','message':'Could not load Analysis'}

@app.post('/session/add_document/{session_id}')
async def add_document_to_session(session_id,request:Request):
    try:
        body=await request.body()
        data = json.loads(body)
        update_sesssion_document_array(data['id'],session_id)
        return  {'status':'success'}
    except Exception:
        return {'status':'failed','message':'Could not add document to Session'}
@app.post('/signup')
async def signup(request:Request):
    body=await request.body()
    data = json.loads(body)
    print(data)
    email,password=data['email'],data['password']
    print(email,password)
    if( await checkForDuplicate(email)):
        return {"staus":"failed",'message':'User with same email already exsists'}
    else:
        try:
            user_id=create_new_user(email,password)
            token=generate_jwt({'user_id':str(user_id.inserted_id),'email':email})
            print(token)
            response = JSONResponse(content={"status": "success"})
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,      # True = JavaScript can't read it; False = JS can read
                max_age=3600,
                secure=True,        # True only for HTTPS; you're on HTTP
                samesite="none"      # Required for cross-origin cookies
            )
            return response
        except Exception:
            return {'status':'failed','message':'Could not create User'}

def checkCred(email,password):
    try:
        key = load_key()
        users=db['Users']
        user=users.find_one({'email':email})
        encrypted=user['password']
        decrypted = decrypt_password(encrypted, key)
        if(decrypted==password):
            return True
        else:
            return False
    except Exception:
        return False

# Function to decode and verify JWT token
def verify_jwt(token: str) -> dict:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"decoded":decoded,"status":'success'}
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired",'status':'failed'}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token",'status':'failed'}
    
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
        if request.url.path.startswith("/signin") or request.url.path.startswith("/signup") or request.url.path.startswith("/verify") or request.url.path.startswith("/docs") :
            return await call_next(request)
        if(result["status"]=='success'):
            request.state.user_id=result['decoded']['user_id']
            request.state.email=result['decoded']['email']
        elif result["status"] == 'failed' and result['error'] == 'Invalid token':
            raise HTTPException(status_code=402, detail="Invalid token")
        else:
            raise HTTPException(status_code=401, detail="Token expired")        
        return await call_next(request)

# Add the middleware to the app
app.add_middleware(JWTAuthMiddleware)
@app.post('/signin')
async def signin(request:Request):
    body=await request.body()
    data = json.loads(body)
    email,password=data['email'],data['password']
    if checkCred(email,password):
        # print(email,password)
        user_id=load_user_id(email)
        token=generate_jwt({"user_id":str(user_id),"email":email})
        response = JSONResponse(content={"status": "success"})
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
        return {'status':'failed','message':'Invalid email or password'}
    
@app.post('/reset_password')
async def reset_pass(request:Request):
    body=await request.body()
    data = json.loads(body) 
    email = getattr(request.state, "email", None)
    if(email=='hello@gmail.com'): 
        return {'status':'failed','message':'Changing password not allowed in test cred., create your own account.'}
    password,new_password=data['password'] ,data['new_password']  
    if checkCred(email,password):
            key = load_key()
            encrypted = encrypt_password(new_password, key)
            db['Users'].update_one({'email':email},{
                '$set':{'password':encrypted}
            })
            return {"status":'success','message':'Password Changed'}
    else:
        return {"status":'failed','message':'Password is incorrect'}
            

        
