from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone

load_dotenv()

from .routers import auth, items
from .logic.consensus import ConsensusAlgorithm
from .routers.auth import supabase

app = FastAPI(title='ITUM Dining API')

# FIX: allow_credentials=True is NOT allowed with allow_origins=['*']
# Setting allow_credentials=False or specifying origins fixes 'failed to fetch'
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(items.router)

scheduler = AsyncIOScheduler()

async def periodic_consensus_sweep():
    algo = ConsensusAlgorithm(supabase)
    await algo.load_config()
    time_window = algo.config.get('algo.time_window_minutes', 30)
    since = (datetime.now(timezone.utc) - timedelta(minutes=time_window)).isoformat()
    
    res = supabase.table('item_updates').select('item_id').gt('created_at', since).execute()
    item_ids = set(row['item_id'] for row in res.data)
    
    for item_id in item_ids:
        await algo.run(item_id)

@app.on_event('startup')
async def startup_event():
    scheduler.add_job(periodic_consensus_sweep, 'interval', minutes=5)
    scheduler.start()

@app.on_event('shutdown')
def shutdown_event():
    scheduler.shutdown()
