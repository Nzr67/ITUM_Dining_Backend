from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from ...database import supabase
from ...dependencies import get_current_user
from ...logic.consensus import ConsensusAlgorithm

router = APIRouter(prefix="/api/items", tags=["4. User Contributions"])

class ItemUpdatePayload(BaseModel):
    item_id: str
    reported_status: str
    ready_in_minutes: Optional[int] = None

@router.post('/update')
async def submit_update(payload: ItemUpdatePayload, background_tasks: BackgroundTasks, user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    
    # Fetch user reputation snapshot
    try:
        prof_res = supabase.table('profiles').select('reputation').eq('id', str(user.id)).execute()
        reputation = prof_res.data[0]['reputation'] if prof_res.data else 1.0
    except:
        reputation = 1.0

    update_data = {
        'item_id': payload.item_id,
        'user_id': str(user.id),
        'reported_status': payload.reported_status,
        'ready_in_minutes': payload.ready_in_minutes,
        'rep_snapshot': reputation
    }
    
    supabase.table('item_updates').insert(update_data).execute()

    # Trigger consensus algorithm
    algo = ConsensusAlgorithm(supabase)
    background_tasks.add_task(algo.run, payload.item_id)

    return {'message': 'Update submitted and consensus algorithm triggered'}

@router.get('/recent-updates')
async def get_recent_updates():
    try:
        res = supabase.table('item_updates')            .select('*, menu_items(name, canteen), profiles(full_name)')            .order('created_at', desc=True)            .limit(10)            .execute()
        return res.data
    except:
        res = supabase.table('item_updates')            .select('*, menu_items(name, canteen)')            .order('created_at', desc=True)            .limit(10)            .execute()
        return res.data

@router.get('/{item_id}/history')
async def get_item_history(item_id: str):
    try:
        res = supabase.table('item_updates')            .select('*, menu_items(canteen), profiles(full_name)')            .eq('item_id', item_id)            .order('created_at', desc=True)            .limit(20)            .execute()
        return res.data
    except:
        res = supabase.table('item_updates')            .select('*')            .eq('item_id', item_id)            .order('created_at', desc=True)            .limit(20)            .execute()
        return res.data
