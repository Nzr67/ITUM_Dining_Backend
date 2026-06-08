import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status, Header, UploadFile, File
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from typing import Optional


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

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    division: Optional[str] = None

# Helper to verify token and get user
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    try:
        # Fetch user data using the provided token
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user, token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

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

# 3. Update Profile Route
@router.put("/user/profile")
async def update_profile(payload: ProfileUpdate, authorization: str = Header(None)):
    user, token = await get_current_user(authorization)
    
    update_data = {}
    if payload.full_name:
        update_data["full_name"] = payload.full_name
    if payload.division:
        update_data["division"] = payload.division
        
    try:
        # Using service_role/admin to update user metadata
        response = supabase.auth.admin.update_user_by_id(
            user.id,
            attributes={"user_metadata": {**user.user_metadata, **update_data}}
        )
        return {"message": "Profile updated", "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 4. Upload Profile Picture Route
@router.post("/user/upload-profile-pic")
async def upload_profile_pic(file: UploadFile = File(...), authorization: str = Header(None)):
    user, token = await get_current_user(authorization)
    
    file_ext = file.filename.split(".")[-1]
    file_path = f"avatars/{user.id}.{file_ext}"
    
    try:
        # Read file content
        contents = await file.read()
        
        # Upload to Supabase Storage (assume 'avatars' bucket exists)
        # Using upsert=True to overwrite old avatar
        supabase.storage.from_("avatars").upload(
            file_path, 
            contents,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # Get public URL
        public_url_response = supabase.storage.from_("avatars").get_public_url(file_path)
        # get_public_url in some versions returns a string, in others an object with publicUrl
        public_url = public_url_response if isinstance(public_url_response, str) else public_url_response.get("publicURL") or public_url_response
        
        # Update user metadata with new avatar URL
        supabase.auth.admin.update_user_by_id(
            user.id,
            attributes={"user_metadata": {**user.user_metadata, "avatar_url": public_url}}
        )
        
        return {"message": "Avatar uploaded", "avatar_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
