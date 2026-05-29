import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# PRINT STATEMENTS TO TRACK THE VALUES IN YOUR TERMINAL
print("--- DEBUG INITIALIZATION ---")
print("READ URL:", os.getenv("https://zxdqavfrvqwgfbcgmbsj.supabase.co"))
print("----------------------------")

app = FastAPI()
# 1. Create a validation schema for the incoming login payload
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 2. Add the POST login route
@app.post("/api/login")
async def login_user(payload: LoginRequest):
    try:
        # Sign in using Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        
        # Return the access token and user info to the frontend
        return {
            "message": "Login successful!",
            "access_token": auth_response.session.access_token,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "metadata": auth_response.user.user_metadata
            }
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )


# Enable CORS so your Next.js repo can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js local server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", "https://zxdqavfrvqwgfbcgmbsj.supabase.co"), 
    os.getenv("SUPABASE_KEY", "sb_publishable_ceFU_joo05kk-HFvHjjH7A_eNgabbU6")
)

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    division: str

@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
async def signup_user(payload: SignupRequest):
    try:
        auth_response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {
                    "full_name": payload.name,
                    "division": payload.division
                }
            }
        })
        return {"message": "User registered successfully!", "user_id": auth_response.user.id}
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
