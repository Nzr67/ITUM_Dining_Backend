import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client


load_dotenv()


router = APIRouter(
    prefix="/api",  
    tags=["Authentication"] 
)


supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")


if not supabase_url or not supabase_key:
    raise ValueError("CRITICAL ERROR: Supabase credentials not found. Is your .env file in the root directory?")


supabase: Client = create_client(supabase_url, supabase_key)


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    division: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 1. Signup Route
@router.post("/signup", status_code=status.HTTP_201_CREATED)
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

# 2. Login Route
@router.post("/login")
async def login_user(payload: LoginRequest):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
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
        raise HTTPException(status_code=401, detail=str(error))