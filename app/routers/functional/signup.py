from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from ...database import supabase

router = APIRouter(prefix="/api/signup", tags=["1. Signup"])

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    division: str
    student_id: str

@router.post("/", status_code=status.HTTP_201_CREATED)
async def signup_user(payload: SignupRequest):
    try:
        auth_response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {
                    "full_name": payload.name,
                    "division": payload.division,
                    "student_id": payload.student_id
                }
            }
        })
        
        try:
            supabase.table("profiles").insert({
                "id": auth_response.user.id,
                "full_name": payload.name,
                "division": payload.division,
                "student_id": payload.student_id,
                "reputation": 1.0,
                "total_updates": 0
            }).execute()
        except Exception as profile_err:
            print(f"Profile creation error: {profile_err}")
            
        return {"message": "User registered successfully!", "user_id": auth_response.user.id}
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
