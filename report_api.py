"""
Session report generation API
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from database import get_database
from datetime import datetime
from openai import AsyncAzureOpenAI
from config import Config
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/session/{session_id}")
async def get_session_report(session_id: str, use_llm: bool = Query(False)):
    """Generate report for a session (optionally with LLM summary)"""
    try:
        db = get_database()
        conversations = db["conversations"]
        
        # Get session document
        session = await conversations.find_one({"session_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"[REPORT] Session found: {session_id}")
        logger.info(f"[REPORT] Session keys: {session.keys()}")
        
        # Extract messages from session document
        messages = session.get("messages", [])
        logger.info(f"[REPORT] Messages count: {len(messages)}")
        
        if not messages:
            raise HTTPException(status_code=404, detail="No messages in session")
        
        # Build minimal report
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        conversation = [
            {
                "role": m.get("role"),
                "content": m.get("content", ""),
                "timestamp": m.get("timestamp")
            }
            for m in messages
        ]
        
        report = {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "duration_seconds": session.get("duration_seconds"),
            "cost": session.get("cost"),
            "conversation": conversation
        }
        
        # Generate LLM summary if requested
        if use_llm:
            try:
                client = AsyncAzureOpenAI(
                    api_key=Config.EMBEDDING_API_KEY,
                    azure_endpoint=Config.EMBEDDING_ENDPOINT,
                    api_version="2024-05-01-preview"
                )
                
                conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "system",
                        "content": """You are an interview evaluator. Analyze the interview conversation and generate a performance report focusing on:
1. Candidate's responses and engagement level
2. Communication skills and professionalism
3. Relevant experience or qualifications mentioned
4. Areas of strength and areas for improvement
5. Overall interview performance rating

Provide a concise evaluation of how the candidate performed."""
                    }, {
                        "role": "user",
                        "content": conv_text
                    }],
                    temperature=0.7,
                    max_tokens=300
                )
                
                report["llm_summary"] = response.choices[0].message.content
            except Exception as e:
                logger.error(f"[REPORT] LLM summary failed: {e}")
                report["llm_summary"] = "Summary generation failed"
        
        return JSONResponse(report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REPORT] Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
