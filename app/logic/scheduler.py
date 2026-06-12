from datetime import datetime, timedelta, timezone
from ..database import supabase
from .consensus import ConsensusAlgorithm

async def periodic_consensus_sweep():
    algo = ConsensusAlgorithm(supabase)
    await algo.load_config()
    time_window = algo.config.get('algo.time_window_minutes', 30)
    since = (datetime.now(timezone.utc) - timedelta(minutes=time_window)).isoformat()
    
    res = supabase.table('item_updates').select('item_id').gt('created_at', since).execute()
    if not res.data:
        return
        
    item_ids = set(row['item_id'] for row in res.data)
    
    for item_id in item_ids:
        await algo.run(item_id)
