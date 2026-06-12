from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ...database import supabase

router = APIRouter(prefix="/api/login", tags=["2. Login"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/")
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
