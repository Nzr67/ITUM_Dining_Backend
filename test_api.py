import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

try:
    print("Trying join with profiles via user_id...")
    res = supabase.table('item_updates')\
        .select('*, menu_items(name), profiles(full_name)')\
        .limit(1)\
        .execute()
    print("User ID Join Success:", res.data)
except Exception as e:
    print("User ID Join Error:", e)
