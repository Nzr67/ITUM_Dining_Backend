from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Depends
from typing import Optional
from pydantic import BaseModel
from ...database import supabase
from ...dependencies import get_current_user

router = APIRouter(prefix="/api/user", tags=["9. Profile Management"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    division: Optional[str] = None
    student_id: Optional[str] = None

@router.put("/profile")
async def update_profile(payload: ProfileUpdate, user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
        
    try:
        supabase.table("profiles").update(update_data).eq("id", user.id).execute()
        return {"message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-profile-pic")
async def upload_profile_pic(file: UploadFile = File(...), user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    file_ext = file.filename.split(".")[-1]
    file_path = f"avatars/{user.id}.{file_ext}"
    
    try:
        contents = await file.read()
        supabase.storage.from_("avatars").upload(file_path, contents, {"upsert": "true"})
        public_url = supabase.storage.from_("avatars").get_public_url(file_path)
        
        supabase.table("profiles").update({"avatar_url": public_url}).eq("id", user.id).execute()
        return {"message": "Avatar uploaded", "avatar_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
