from fastapi import APIRouter, HTTPException
from ...database import supabase

router = APIRouter(prefix="/api/leaderboard", tags=["7. Leaderboard"])

@router.get("/")
async def get_leaderboard(limit: int = 20):
    try:
        # Try full query first
        res = supabase.table("profiles")            .select("full_name, student_id, total_updates, reputation, avatar_url")            .order("total_updates", desc=True)            .limit(limit)            .execute()
        return res.data
    except Exception as e:
        # Fallback if columns are missing
        try:
            res = supabase.table("profiles")                .select("full_name, total_updates, reputation")                .order("total_updates", desc=True)                .limit(limit)                .execute()
            return res.data
        except Exception as e2:
            raise HTTPException(status_code=400, detail=str(e2))
