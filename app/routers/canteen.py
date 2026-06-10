import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api",
    tags=["Canteen"]
)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None

class StatusUpdate(BaseModel):
    student_id: str
    food_id: int
    status: str

@router.get("/get-menu")
async def get_menu():
    # In a real app, you'd fetch from Supabase:
    # try:
    #     if supabase:
    #         response = supabase.table("menu_items").select("*").execute()
    #         return {"status": "success", "menu": response.data}
    # except Exception as e:
    #     print(f"Error fetching from Supabase: {e}")
    
    # Returning mock data for now to match frontend expectations
    mock_menu = [
        {"food_id": 1, "food_name": "Rice and Curry", "status": "Available", "last_verified": "10:30 AM"},
        {"food_id": 2, "food_name": "Kottu", "status": "Low Stock", "last_verified": "11:00 AM"},
        {"food_id": 3, "food_name": "Fried Rice", "status": "Available", "last_verified": "11:15 AM"},
        {"food_id": 4, "food_name": "Hoppers", "status": "Not-Available", "last_verified": "09:00 AM"},
        {"food_id": 5, "food_name": "Paratha", "status": "Available", "last_verified": "10:45 AM"},
    ]
    return {"status": "success", "menu": mock_menu}

@router.post("/verify-spatial-update")
async def verify_spatial_update(update: StatusUpdate):
    # Logic to handle status update
    # In a real app, you'd save this to Supabase
    # try:
    #     if supabase:
    #         supabase.table("status_updates").insert({
    #             "student_id": update.student_id,
    #             "food_id": update.food_id,
    #             "status": update.status
    #         }).execute()
    # except Exception as e:
    #     print(f"Error saving update to Supabase: {e}")

    return {
        "status": "success", 
        "message": f"Status for food item {update.food_id} updated to {update.status}."
    }
