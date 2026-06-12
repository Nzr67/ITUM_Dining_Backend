from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
from ...database import supabase

router = APIRouter(prefix="/api/items", tags=["3. Menu Catalog"])

class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    canteen: Optional[str]
    current_status: str
    ready_in_minutes: Optional[int]
    consensus_confidence: float

@router.get("/", response_model=List[MenuItem])
async def get_items(canteen: Optional[str] = None):
    query = supabase.table('menu_items').select('*')
    if canteen:
        query = query.eq('canteen', canteen)
    res = query.execute()
    return res.data
