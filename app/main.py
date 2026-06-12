from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import Functional Routers
from .routers.functional import (
    signup, login, menu, updates, 
    reputation, leaderboard, profile, security
)
from .logic.scheduler import periodic_consensus_sweep

app = FastAPI(
    title='ITUM Dining API - Functional Presentation Version',
    description='Backend decomposed into 10 key functional parts for demonstration.'
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Registering the 10 Functional Parts (Routers)
app.include_router(signup.router)      # Part 1
app.include_router(login.router)       # Part 2
app.include_router(menu.router)        # Part 3
app.include_router(updates.router)     # Part 4
# Note: Part 5 (Consensus) is the logic used inside Part 4 and 8
app.include_router(reputation.router)  # Part 6
app.include_router(leaderboard.router) # Part 7
# Note: Part 8 (Scheduler) is registered in startup below
app.include_router(profile.router)     # Part 9
app.include_router(security.router)    # Part 10

scheduler = AsyncIOScheduler()

@app.on_event('startup')
async def startup_event():
    # Part 8: Real-time Synchronization & Background Tasks
    scheduler.add_job(periodic_consensus_sweep, 'interval', minutes=5)
    scheduler.start()

@app.on_event('shutdown')
def shutdown_event():
    scheduler.shutdown()
