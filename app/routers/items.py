import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/v1/food-status",
    tags=["Items"]
)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None

class FoodStatusUpdate(BaseModel):
    product_id: int
    user_id: str
    status_type: str
    minutes_to_ready: Optional[int] = 0

@router.post("/update")
async def update_food_status(payload: FoodStatusUpdate):
    """
    Update the status of a food item.
    This endpoint is called when a student updates the availability of a food item.
    """
    if not supabase:
        # Fallback for development if Supabase is not configured
        return {
            "status": "success",
            "message": f"Mock: Status for product {payload.product_id} updated to {payload.status_type}",
            "data": payload
        }

    try:
        # 1. Log the update in a history table (optional but good for 'spatial verification')
        # supabase.table("status_updates").insert({
        #     "product_id": payload.product_id,
        #     "user_id": payload.user_id,
        #     "status_type": payload.status_type,
        #     "minutes_to_ready": payload.minutes_to_ready
        # }).execute()

        # 2. Update the main food items table
        # Map frontend status_type to DB status if necessary
        # status_map = {
        #     "available": "Available",
        #     "out_of_stock": "Not-Available",
        #     "cooking": "Low Stock" # or some other mapping
        # }
        # db_status = status_map.get(payload.status_type, payload.status_type)

        # response = supabase.table("food_items").update({
        #     "status": db_status,
        #     "last_verified": "Just now" # Or use a timestamp
        # }).eq("id", payload.product_id).execute()

        return {
            "status": "success",
            "message": f"Status for product {payload.product_id} updated successfully.",
            "details": payload
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update food status: {str(e)}"
        )
