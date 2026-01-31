from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from chat_engine import JEEBuddyEngine
from passlib.context import CryptContext
from memory_manager import MemoryManager
import os

app = FastAPI(title="JEE Buddy API", description="AI Study Partner Backend")

# Initialize Brain
print("Initializing Engine...")
engine = JEEBuddyEngine()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mount Static Files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Data Models ---
class UserAuth(BaseModel):
    email: str
    password: str

class UserRegister(UserAuth):
    name: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    
# --- Helpers ---
def get_user_manager():
    # Helper to get MM just for user management
    return MemoryManager(user_id="SYSTEM_AUTH")

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Endpoints ---

@app.get("/")
def home():
    # Serve the HTML frontend
    return FileResponse('static/index.html')

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/register")
def register(user: UserRegister):
    mm = MemoryManager(user_id=user.email) # Use email as ID for simplicity
    profile = mm.get_profile_dict() # Need to access raw dict
    
    if profile.get("password_hash"):
        raise HTTPException(status_code=400, detail="User already exists with this email")
    
    # Save new user
    profile["password_hash"] = hash_password(user.password)
    profile["email"] = user.email
    profile["name"] = user.name # Use provided name
    mm._save_profile(profile)
    
    return {"status": "created", "user_id": user.email}

@app.post("/login")
def login(user: UserAuth):
    mm = MemoryManager(user_id=user.email)
    profile = mm.get_profile_dict()
    
    if not profile.get("password_hash"):
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(user.password, profile["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    return {"status": "success", "user_id": user.email, "name": profile.get("name")}

@app.get("/profile/{user_id}")
def get_profile_data(user_id: str):
    mm = MemoryManager(user_id=user_id)
    return mm.get_profile_dict()

@app.get("/history/{user_id}")
def get_history(user_id: str):
    mm = MemoryManager(user_id=user_id)
    return {"history": mm.get_chat_history(limit=50)}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        mm = MemoryManager(user_id=request.user_id)
        
        # 1. Load recent history from DB (Context Window)
        # We fetch last 10 messages for context
        stored_history = mm.get_chat_history(limit=10)
        
        # 2. Generate Response
        response_text = engine.get_response(
            user_input=request.message,
            user_id=request.user_id,
            history_context=stored_history
        )
        
        # 3. Save this Turn to DB (User msg + Bot response)
        new_turn = [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": response_text}
        ]
        mm.append_chat_history(new_turn)
        
        return ChatResponse(response=response_text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
