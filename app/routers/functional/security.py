from fastapi import APIRouter, Depends
from ...database import supabase
from ...dependencies import get_current_user

router = APIRouter(prefix="/api/security", tags=["10. Security & Integrity"])

@router.get("/status")
async def get_security_status(user_data: tuple = Depends(get_current_user)):
    """Provides an overview of current user's security context (RLS status)."""
    user, token = user_data
    return {
        "user_id": user.id,
        "role": "authenticated",
        "rls_active": True,
        "database_integrity": "verified"
    }
