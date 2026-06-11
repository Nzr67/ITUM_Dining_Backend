import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from .auth import get_current_user, supabase
from ..logic.consensus import ConsensusAlgorithm

router = APIRouter(
    prefix="/api/items",
    tags=["Items"]
)

class ItemUpdatePayload(BaseModel):
    item_id: str
    reported_status: str
    ready_in_minutes: Optional[int] = None

class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    current_status: str
    ready_in_minutes: Optional[int]
    consensus_confidence: float

@router.get("/", response_model=List[MenuItem])
async def get_items():
    res = supabase.table("menu_items").select("*").execute()
    return res.data

@router.post("/update")
async def submit_update(payload: ItemUpdatePayload, background_tasks: BackgroundTasks, user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    
    # 1. Fetch user reputation for snapshot
    prof_res = supabase.table("profiles").select("reputation").eq("id", user.id).single().execute()
    if not prof_res.data:
        # Create profile if it doesn't exist
        reputation = 1.0
        supabase.table("profiles").insert({
            "id": user.id,
            "full_name": user.user_metadata.get("full_name"),
            "division": user.user_metadata.get("division"),
            "reputation": reputation
        }).execute()
    else:
        reputation = prof_res.data['reputation']

    # 2. Insert update vote
    update_data = {
        "item_id": payload.item_id,
        "user_id": user.id,
        "reported_status": payload.reported_status,
        "ready_in_minutes": payload.ready_in_minutes,
        "rep_snapshot": reputation
    }
    supabase.table("item_updates").insert(update_data).execute()

    # 3. Trigger consensus algorithm in background
    algo = ConsensusAlgorithm(supabase)
    background_tasks.add_task(algo.run, payload.item_id)

    return {"message": "Update submitted and consensus algorithm triggered"}

@router.get("/{item_id}/history")
async def get_item_history(item_id: str):
    res = supabase.table("item_updates")\
        .select("*, profiles(full_name)")\
        .eq("item_id", item_id)\
        .order("created_at", desc=True)\
        .limit(20)\
        .execute()
    return res.data
