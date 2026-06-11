import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from .auth import get_current_user, supabase
from ..logic.consensus import ConsensusAlgorithm

router = APIRouter(
    prefix='/api/items',
    tags=['Items']
)

class ItemUpdatePayload(BaseModel):
    item_id: str
    reported_status: str
    ready_in_minutes: Optional[int] = None

class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    canteen: Optional[str]
    current_status: str
    ready_in_minutes: Optional[int]
    consensus_confidence: float

@router.get('/', response_model=List[MenuItem])
async def get_items(canteen: Optional[str] = None):
    query = supabase.table('menu_items').select('*')
    if canteen:
        query = query.eq('canteen', canteen)
    res = query.execute()
    return res.data

@router.post('/update')
async def submit_update(payload: ItemUpdatePayload, background_tasks: BackgroundTasks, user_data: tuple = Depends(get_current_user)):
    user, token = user_data
    
    # 1. Fetch user reputation for snapshot SAFELY
    try:
        prof_res = supabase.table('profiles').select('reputation').eq('id', str(user.id)).execute()
        
        if not prof_res.data:
            reputation = 1.0
            try:
                supabase.table('profiles').insert({
                    'id': str(user.id),
                    'full_name': user.user_metadata.get('full_name', 'Anonymous'),
                    'division': user.user_metadata.get('division', ''),
                    'reputation': reputation
                }).execute()
            except Exception as e:
                print(f'Failed to create profile: {e}')
        else:
            reputation = prof_res.data[0]['reputation']
    except Exception as e:
        print(f'Failed to fetch profile: {e}')
        reputation = 1.0

    # 2. Insert update vote
    update_data = {
        'item_id': payload.item_id,
        'user_id': str(user.id),
        'reported_status': payload.reported_status,
        'ready_in_minutes': payload.ready_in_minutes,
        'rep_snapshot': reputation
    }
    
    try:
        supabase.table('item_updates').insert(update_data).execute()
    except Exception as e:
        print(f'Failed to insert update: {e}')
        raise HTTPException(status_code=400, detail=f'Database error. Ensure RLS allows insert: {str(e)}')

    # 3. Trigger consensus algorithm in background
    algo = ConsensusAlgorithm(supabase)
    background_tasks.add_task(algo.run, payload.item_id)

    return {'message': 'Update submitted and consensus algorithm triggered'}

@router.get('/recent-updates')
async def get_recent_updates():
    # Attempting join, but falling back if it fails due to missing FK in DB
    try:
        res = supabase.table('item_updates')\
            .select('*, menu_items(name), profiles(full_name)')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        return res.data
    except Exception as e:
        print(f"Join failed: {e}")
        # Fallback to simple query without profiles join
        res = supabase.table('item_updates')\
            .select('*, menu_items(name)')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        return res.data

@router.get('/{item_id}/history')
async def get_item_history(item_id: str):
    try:
        res = supabase.table('item_updates')\
            .select('*, profiles(full_name)')\
            .eq('item_id', item_id)\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        return res.data
    except Exception as e:
        print(f"History join failed: {e}")
        res = supabase.table('item_updates')\
            .select('*')\
            .eq('item_id', item_id)\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        return res.data
