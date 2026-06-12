import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from ..database import supabase

class ConsensusAlgorithm:
    def __init__(self, db_client=None):
        self.supabase = db_client or supabase
        self.config = {}

    async def load_config(self):
        try:
            res = self.supabase.table("config").select("*").execute()
            for row in res.data:
                key = row['key']
                val = row['value']
                if key.startswith("algo."):
                    try:
                        if "." in val:
                            self.config[key] = float(val)
                        else:
                            self.config[key] = int(val)
                    except ValueError:
                        self.config[key] = val
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Set defaults if missing
        defaults = {
            "algo.time_window_minutes": 30,
            "algo.decay_lambda": 0.1,
            "algo.confidence_threshold": 0.60,
            "algo.min_votes": 1,
            "algo.rep_correct_delta": 0.05,
            "algo.rep_incorrect_delta": 0.02,
            "algo.rep_min": 0.10,
            "algo.rep_max": 5.00,
            "algo.coming_soon_window_min": 1,
            "algo.coming_soon_window_max": 120
        }
        for k, v in defaults.items():
            if k not in self.config:
                self.config[k] = v

    def calculate_weight(self, rep_snapshot: float, created_at: str) -> float:
        now = datetime.now(timezone.utc)
        # Handle various ISO formats
        try:
            created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            # Fallback for other formats if necessary
            created_at_dt = datetime.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            
        age_minutes = (now - created_at_dt).total_seconds() / 60.0
        # t is in minutes as per algorithm
        decay = math.exp(-self.config["algo.decay_lambda"] * age_minutes)
        return rep_snapshot * decay

    async def run(self, item_id: str):
        await self.load_config()
        
        time_window = self.config["algo.time_window_minutes"]
        since = (datetime.now(timezone.utc) - timedelta(minutes=time_window)).isoformat()
        
        # Step 1: Collect Votes
        res = self.supabase.table("item_updates")\
            .select("*")\
            .eq("item_id", item_id)\
            .gt("created_at", since)\
            .order("created_at", desc=True)\
            .execute()
        
        votes = res.data
        if not votes or len(votes) < self.config["algo.min_votes"]:
            return None

        # Step 2 & 3: Compute Weights and Tally
        weights = {"available": 0.0, "unavailable": 0.0, "coming_soon": 0.0}
        total_weight = 0.0
        
        for vote in votes:
            w = self.calculate_weight(vote['rep_snapshot'], vote['created_at'])
            status = vote['reported_status']
            if status in weights:
                weights[status] += w
                total_weight += w

        if total_weight == 0:
            return None

        # Step 4: Determine Consensus
        winning_status = max(weights, key=weights.get)
        confidence = weights[winning_status] / total_weight
        
        # Get current status to compare
        item_res = self.supabase.table("menu_items").select("current_status").eq("id", item_id).single().execute()
        current_status = item_res.data.get('current_status') if item_res.data else "available"
        
        new_status = current_status
        if confidence >= self.config["algo.confidence_threshold"]:
            new_status = winning_status

        # Step 5: Handling coming_soon
        ready_in_minutes = None
        if new_status == "coming_soon":
            cs_votes = [(v['ready_in_minutes'], self.calculate_weight(v['rep_snapshot'], v['created_at'])) 
                        for v in votes if v['reported_status'] == "coming_soon" and v.get('ready_in_minutes') is not None]
            
            if cs_votes:
                # Sort by minutes
                cs_votes.sort(key=lambda x: x[0])
                total_cs_weight = sum(w for m, w in cs_votes)
                cumulative_w = 0.0
                for m, w in cs_votes:
                    cumulative_w += w
                    if cumulative_w >= total_cs_weight / 2:
                        ready_in_minutes = m
                        break

        # Step 6: Update menu_items
        self.supabase.table("menu_items").update({
            "current_status": new_status,
            "ready_in_minutes": ready_in_minutes,
            "consensus_updated_at": datetime.now(timezone.utc).isoformat(),
            "consensus_confidence": confidence
        }).eq("id", item_id).execute()

        # Step 7: Retrospective Reputation Update
        for vote in votes:
            is_correct = vote['reported_status'] == new_status
            
            # Update vote status
            self.supabase.table("item_updates").update({"was_correct": is_correct}).eq("id", vote['id']).execute()
            
            # Fetch current profile to update reputation
            prof_res = self.supabase.table("profiles").select("reputation, total_updates, correct_updates").eq("id", vote['user_id']).single().execute()
            if prof_res.data:
                p = prof_res.data
                old_rep = p['reputation']
                if is_correct:
                    new_rep = min(old_rep + self.config["algo.rep_correct_delta"], self.config["algo.rep_max"])
                else:
                    new_rep = max(old_rep - self.config["algo.rep_incorrect_delta"], self.config["algo.rep_min"])
                
                self.supabase.table("profiles").update({
                    "reputation": new_rep,
                    "total_updates": (p.get('total_updates') or 0) + 1,
                    "correct_updates": (p.get('correct_updates') or 0) + (1 if is_correct else 0),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", vote['user_id']).execute()

        return {
            "item_id": item_id,
            "status": new_status,
            "confidence": confidence,
            "ready_in_minutes": ready_in_minutes
        }
