"""
Scenario management service
"""
import logging
from database import get_database

logger = logging.getLogger(__name__)

async def get_scenario(scenario_id: str):
    """Get scenario configuration from MongoDB"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        scenario = await scenarios.find_one({"scenario_id": scenario_id})
        
        if not scenario:
            logger.warning(f"[SCENARIO] Not found: {scenario_id}")
            return None
            
        logger.info(f"[SCENARIO] Loaded: {scenario_id}")
        return scenario
    except Exception as e:
        logger.error(f"[SCENARIO] Failed to load {scenario_id}: {e}")
        return None

async def list_scenarios():
    """List all available scenarios"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        cursor = scenarios.find({}, {"scenario_id": 1, "name": 1, "enable_rag": 1})
        result = await cursor.to_list(length=100)
        # Convert ObjectId to string
        for item in result:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        return result
    except Exception as e:
        logger.error(f"[SCENARIO] Failed to list: {e}")
        return []
