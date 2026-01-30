"""
Scenario management REST API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

class ScenarioCreate(BaseModel):
    scenario_id: str
    name: str
    system_prompt: str
    kb_id: Optional[str] = None
    enable_rag: bool = True
    voice: str = "alloy"

class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    kb_id: Optional[str] = None
    enable_rag: Optional[bool] = None
    voice: Optional[str] = None

@router.get("")
async def list_scenarios():
    """List all scenarios"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        cursor = scenarios.find({})
        result = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for item in result:
            item["_id"] = str(item["_id"])
        
        return JSONResponse({"scenarios": result, "total": len(result)})
    except Exception as e:
        logger.error(f"[API] List scenarios failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get scenario by ID"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        scenario = await scenarios.find_one({"scenario_id": scenario_id})
        
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        scenario["_id"] = str(scenario["_id"])
        return JSONResponse(scenario)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Get scenario failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_scenario(scenario: ScenarioCreate):
    """Create new scenario"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        
        # Check if scenario_id already exists
        existing = await scenarios.find_one({"scenario_id": scenario.scenario_id})
        if existing:
            raise HTTPException(status_code=400, detail="Scenario ID already exists")
        
        # Insert scenario
        result = await scenarios.insert_one(scenario.dict())
        
        logger.info(f"[API] Created scenario: {scenario.scenario_id}")
        return JSONResponse({
            "message": "Scenario created",
            "scenario_id": scenario.scenario_id,
            "_id": str(result.inserted_id)
        }, status_code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Create scenario failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{scenario_id}")
async def update_scenario(scenario_id: str, updates: ScenarioUpdate):
    """Update scenario"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        
        # Build update dict (include None values for kb_id to allow clearing it)
        update_data = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.system_prompt is not None:
            update_data["system_prompt"] = updates.system_prompt
        if updates.enable_rag is not None:
            update_data["enable_rag"] = updates.enable_rag
        if updates.voice is not None:
            update_data["voice"] = updates.voice
        # Always include kb_id even if None (to allow clearing)
        if "kb_id" in updates.__fields_set__:
            update_data["kb_id"] = updates.kb_id
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update scenario
        result = await scenarios.update_one(
            {"scenario_id": scenario_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        logger.info(f"[API] Updated scenario: {scenario_id}")
        return JSONResponse({
            "message": "Scenario updated",
            "scenario_id": scenario_id,
            "modified": result.modified_count
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Update scenario failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """Delete scenario"""
    try:
        db = get_database()
        scenarios = db["scenarios"]
        
        result = await scenarios.delete_one({"scenario_id": scenario_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        logger.info(f"[API] Deleted scenario: {scenario_id}")
        return JSONResponse({
            "message": "Scenario deleted",
            "scenario_id": scenario_id
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Delete scenario failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
