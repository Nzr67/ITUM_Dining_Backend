from fastapi import APIRouter, Depends
from ...database import supabase
from ...dependencies import get_current_user

router = APIRouter(prefix="/api/reputation", tags=["6. Reputation System"])

@router.get("/my-stats")
async def get_my_reputation(user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    res = supabase.table('profiles').select('reputation, total_updates, correct_updates').eq('id', user.id).single().execute()
    return res.data
