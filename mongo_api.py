"""
MongoDB API endpoints for sessions
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database import get_sessions_collection, get_messages_collection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sessions")
async def list_sessions():
    """List all sessions from MongoDB"""
    try:
        sessions = get_sessions_collection()
        cursor = sessions.find().sort("created_at", -1).limit(100)
        
        sessions_list = []
        async for doc in cursor:
            sessions_list.append({
                "session_id": doc.get("session_id"),
                "kb_id": doc.get("kb_id"),
                "start_time": doc.get("start_time").isoformat() if doc.get("start_time") else None,
                "duration_seconds": doc.get("duration_seconds", 0),
                "message_count": doc.get("message_count", 0),
                "cost_usd": doc.get("cost_usd", 0.0)
            })
        
        return JSONResponse({"sessions": sessions_list, "total": len(sessions_list)})
    except Exception as e:
        logger.error(f"[MONGO] Failed to list sessions: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details from MongoDB"""
    try:
        sessions = get_sessions_collection()
        messages = get_messages_collection()
        
        # Get session
        session = await sessions.find_one({"session_id": session_id})
        if not session:
            return JSONResponse({"error": "Session not found"}, status_code=404)
        
        # Get messages
        cursor = messages.find({"session_id": session_id}).sort("timestamp", 1)
        messages_list = []
        async for msg in cursor:
            messages_list.append({
                "timestamp": msg.get("timestamp").isoformat() if msg.get("timestamp") else None,
                "role": msg.get("role"),
                "type": msg.get("message_type"),
                "content": msg.get("content"),
                "metadata": msg.get("metadata", {})
            })
        
        # Format response
        response = {
            "session_id": session.get("session_id"),
            "kb_id": session.get("kb_id"),
            "start_time": session.get("start_time").isoformat() if session.get("start_time") else None,
            "end_time": session.get("end_time").isoformat() if session.get("end_time") else None,
            "duration_seconds": session.get("duration_seconds", 0),
            "message_count": session.get("message_count", 0),
            "messages": messages_list,
            "cost": {
                "session_id": session.get("session_id"),
                "tokens": {
                    "text_input": session.get("text_input_tokens", 0),
                    "text_output": session.get("text_output_tokens", 0),
                    "audio_input": session.get("audio_input_tokens", 0),
                    "audio_output": session.get("audio_output_tokens", 0)
                },
                "cost_usd": session.get("cost_usd", 0.0),
                "cost_breakdown": session.get("cost_breakdown", {})
            }
        }
        
        return JSONResponse(response)
    except Exception as e:
        logger.error(f"[MONGO] Failed to get session: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/cost-summary")
async def get_cost_summary():
    """Get cost summary from MongoDB"""
    try:
        sessions = get_sessions_collection()
        
        # Aggregate costs
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$cost_usd"},
                    "total_sessions": {"$sum": 1},
                    "total_text_input": {"$sum": "$text_input_tokens"},
                    "total_text_output": {"$sum": "$text_output_tokens"},
                    "total_audio_input": {"$sum": "$audio_input_tokens"},
                    "total_audio_output": {"$sum": "$audio_output_tokens"}
                }
            }
        ]
        
        result = await sessions.aggregate(pipeline).to_list(1)
        
        if result:
            data = result[0]
            total_sessions = data.get("total_sessions", 0)
            total_cost = data.get("total_cost", 0.0)
            
            return JSONResponse({
                "total_cost_usd": round(total_cost, 6),
                "total_sessions": total_sessions,
                "total_tokens": {
                    "text_input": data.get("total_text_input", 0),
                    "text_output": data.get("total_text_output", 0),
                    "audio_input": data.get("total_audio_input", 0),
                    "audio_output": data.get("total_audio_output", 0)
                },
                "average_cost_per_session": round(total_cost / total_sessions, 6) if total_sessions > 0 else 0
            })
        else:
            return JSONResponse({
                "total_cost_usd": 0,
                "total_sessions": 0,
                "total_tokens": {"text_input": 0, "text_output": 0, "audio_input": 0, "audio_output": 0},
                "average_cost_per_session": 0
            })
    except Exception as e:
        logger.error(f"[MONGO] Failed to get cost summary: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
