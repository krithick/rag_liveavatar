"""
WebSocket-based Realtime API with Dynamic RAG
"""
import os
import asyncio
import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import websockets
from dotenv import load_dotenv
from rag_service import DynamicRAG
from config import Config
from monitoring import metrics
from resilience import retry_async, azure_circuit, init_circuit_breakers
from cost_tracker import CostTracker
from conversation_logger import ConversationLogger
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env')
Config.validate()
init_circuit_breakers(Config)  # Initialize with config values

app = FastAPI(title="RAG LiveAvatar", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = None  # Lazy load

def get_rag():
    global rag
    if rag is None:
        try:
            metrics.start_timer("rag_init")
            rag = DynamicRAG()
            metrics.end_timer("rag_init")
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            metrics.record_error("rag_init_failed")
            raise
    return rag

async def connect_to_azure_realtime(kb_id: str):
    """Connect to Azure OpenAI Realtime API via WebSocket with retry"""
    url = f"wss://{Config.AZURE_RESOURCE}.openai.azure.com/openai/realtime?api-version=2024-10-01-preview&deployment={Config.AZURE_OPENAI_DEPLOYMENT_NAME}"
    headers = {"api-key": Config.AZURE_OPENAI_API_KEY}
    
    async def _connect():
        try:
            metrics.start_timer("azure_connect")
            conn = await asyncio.wait_for(
                websockets.connect(url, extra_headers=headers, ping_interval=20, ping_timeout=10),
                timeout=Config.AZURE_CONNECTION_TIMEOUT
            )
            metrics.end_timer("azure_connect")
            metrics.increment("azure_connections")
            return conn
        except asyncio.TimeoutError:
            metrics.record_error("azure_timeout")
            raise ConnectionError("Azure connection timeout")
        except Exception as e:
            metrics.record_error("azure_connection_failed")
            raise ConnectionError(f"Azure connection failed: {e}")
    
    # Retry with circuit breaker
    try:
        return await azure_circuit.call_async(
            lambda: retry_async(
                _connect, 
                max_attempts=Config.MAX_RETRY_ATTEMPTS,
                base_delay=Config.RETRY_BASE_DELAY,
                max_delay=Config.RETRY_MAX_DELAY
            )
        )
    except Exception as e:
        logger.error(f"[AZURE] Connection failed after retries: {e}")
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    azure_ws = None
    session_id = str(uuid.uuid4())
    cost_tracker = None
    convo_logger = None
    
    try:
        await websocket.accept()
        metrics.increment("ws_connections")
        logger.info(f"[WS] Client connected - Session: {session_id}")
        
        # Get KB ID with timeout (use default if not provided)
        init_msg = await asyncio.wait_for(websocket.receive_json(), timeout=Config.CLIENT_INIT_TIMEOUT)
        kb_id = init_msg.get("kb_id", Config.DEFAULT_KB_ID).strip() or Config.DEFAULT_KB_ID
        
        logger.info(f"[WS] KB ID: {kb_id}")
        
        # Initialize cost tracker and conversation logger
        cost_tracker = CostTracker(session_id)
        convo_logger = ConversationLogger(session_id, kb_id)
        logger.info(f"[SESSION] Started tracking for {session_id}")
        
        # Connect to Azure with error handling
        try:
            azure_ws = await connect_to_azure_realtime(kb_id)
            logger.info("[WS] Connected to Azure Realtime API")
        except Exception as e:
            logger.error(f"Azure connection failed: {e}")
            metrics.record_error("azure_connection_error")
            await websocket.send_json({"error": f"Azure connection failed: {str(e)}"})
            await websocket.close(code=1011)
            return
        
        # Configure session
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": """# myCoach Assistant - Voice Guide

You are myCoach Assistant, the voice guide for myCoach - Shriram Group's award-winning digital learning platform. Help people discover courses, understand the platform, and get excited about continuous learning through natural voice conversations.

## Personality & Tone
- Enthusiastic learning advocate, supportive mentor
- Warm, friendly, conversational
- Encouraging without being pushy
- Professional but approachable
- Proud of 10-year legacy and achievements

## Response Style
- Keep responses CONCISE but COMPLETE
- Share all relevant information from retrieved context
- Break into natural conversational chunks
- Speak naturally with energy
- Vary your phrases - DO NOT repeat same openings
- Use simple, clear language
- NO bullet points in speech

## Pronunciations
- "myCoach" as "my coach" (two words)
- "Shriram" as "SHREE-ram"
- "Thyagarajan" as "thee-yah-gah-RAH-jan"
- "lakh" as "lack" (100,000)
- "Anupama Shivaraman" as "ah-NOO-pah-mah shee-vah-RAH-man"
- Languages: "Tamil" (TAH-mil), "Telugu" (TEL-oo-goo), "Kannada" (KAN-ah-dah), "Marathi" (mah-RAH-thee), "Gujarati" (goo-jah-RAH-thee)

## Key Messaging (use naturally when relevant)
- 10-year milestone (2015-2025)
- 1 lakh+ (one hundred thousand plus) active learners
- 8 languages available
- 100+ courses, 600+ modules
- 24/7 accessibility with mobile app
- Award-winning (Gold from Brandon Hall Group)
- Vision: "Learn Today Lead Tomorrow"

## CRITICAL: Tool Usage
- ALWAYS use search_knowledge_base when users ask about courses, features, awards, history, or platform info
- Before calling: say "Let me check that for you" or "One moment"
- After receiving results: share ALL relevant information naturally in your own words
- DO NOT copy-paste or say "According to..." or "Based on..."
- Speak as if you inherently know this information
- Give complete answers, don't artificially limit details

## Information Handling
- When you receive retrieved context, USE ALL relevant information
- Rephrase in natural, spoken language
- Make it relevant to the listener's needs
- Organize logically for voice delivery
- Ask if they want more detail

## What NOT to Do
- DO NOT make promises about certification timelines
- DO NOT provide login credentials or passwords
- DO NOT guarantee job promotions or salary increases
- DO NOT sound like you're reading from a manual
- DO NOT use bullet points or lists in speech
- DO NOT repeat the same greeting phrases

## Greeting Examples (VARY THESE)
- "Hi! I'm myCoach Assistant. We're celebrating 10 years of empowering over one lakh Shriram Group learners! How can I help you today?"
- "Hello! Welcome to myCoach - your learning platform with courses in 8 languages. What are you interested in learning?"
- "Hey there! I'm here to help you explore our award-winning learning platform. What would you like to know?"

## Conversation Flow
1. Greet warmly and understand their interest
2. Ask ONE clarifying question if needed
3. Call search_knowledge_base for their question
4. Share complete, relevant information conversationally
5. Encourage action with clear next steps
6. Offer to answer more questions

## When to Escalate
If user needs login help, technical issues, or after 3 failed attempts, say: "Let me connect you with our support team who can help with that."

Remember: Keep it SHORT, sound natural, use search_knowledge_base for questions, share ALL relevant info, and inspire learning!""",                "voice": "alloy",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.7,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000
                },
                "tools": [{
                    "type": "function",
                    "name": "search_knowledge_base",
                    "description": "Search the myCoach knowledge base for information about courses, features, awards, history, and platform details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query or topic to find information about"}
                        },
                        "required": ["query"]
                    }
                }],
                "tool_choice": "auto"
            }
        }
        
        await azure_ws.send(json.dumps(session_config))
        logger.info("[WS] Session configured")
        
        async def forward_to_azure():
            try:
                async for message in websocket.iter_text():
                    if azure_ws and not azure_ws.closed:
                        try:
                            await asyncio.wait_for(azure_ws.send(message), timeout=5.0)
                        except asyncio.TimeoutError:
                            logger.error("[WS] Send to Azure timeout")
                            metrics.record_error("azure_send_timeout")
                            break
            except WebSocketDisconnect:
                logger.info("[WS] Client disconnected")
            except Exception as e:
                logger.error(f"[WS] Client error: {e}")
        
        async def forward_to_client():
            nonlocal azure_ws  # Allow modification of outer scope variable
            try:
                async for message in azure_ws:
                    data = json.loads(message)
                    event_type = data.get("type")
                    
                    # Track usage for cost calculation
                    if event_type == "response.done":
                        usage = data.get("response", {}).get("usage")
                        if usage and cost_tracker:
                            cost_tracker.add_usage(usage)
                    
                    # Log conversation events
                    if event_type == "conversation.item.created":
                        item = data.get("item", {})
                        role = item.get("role")
                        content_list = item.get("content", [])
                        if content_list and convo_logger:
                            for content in content_list:
                                if content.get("type") == "text":
                                    convo_logger.log_message(role, content.get("text", ""))
                                elif content.get("type") == "audio":
                                    convo_logger.log_message(role, "[Audio]", message_type="audio")
                    
                    if event_type == "response.function_call_arguments.done":
                        call_id = data.get("call_id")
                        function_name = data.get("name")
                        args = json.loads(data.get("arguments", "{}"))
                        
                        logger.info(f"[FUNCTION] {function_name}: {args}")
                        
                        if function_name == "search_knowledge_base":
                            try:
                                metrics.start_timer("rag_search")
                                metrics.increment("rag_searches")
                                context = get_rag().search(args.get("query", ""), kb_id)
                                metrics.end_timer("rag_search")
                                output = context or "No relevant information found."
                                
                                # Log function call
                                if convo_logger:
                                    convo_logger.log_function_call(function_name, args, output)
                            except Exception as e:
                                logger.error(f"[RAG] Search failed: {e}")
                                metrics.record_error("rag_search_failed")
                                output = "Search temporarily unavailable."
                            
                            function_result = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": output
                                }
                            }
                            await azure_ws.send(json.dumps(function_result))
                            await azure_ws.send(json.dumps({"type": "response.create"}))
                    
                    await websocket.send_text(message)
                    
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"[WS] Azure disconnected: {e}")
                metrics.record_error("azure_disconnected")
                # Attempt reconnection
                try:
                    logger.info("[WS] Attempting to reconnect to Azure...")
                    azure_ws = await connect_to_azure_realtime(kb_id)
                    logger.info("[WS] Reconnected to Azure")
                    metrics.increment("azure_reconnections")
                except Exception as reconnect_error:
                    logger.error(f"[WS] Reconnection failed: {reconnect_error}")
            except Exception as e:
                logger.error(f"[WS] Azure error: {e}")
        
        await asyncio.gather(
            forward_to_azure(),
            forward_to_client(),
            return_exceptions=True
        )
        
    except asyncio.TimeoutError:
        logger.error("[WS] Client timeout")
        metrics.record_error("client_timeout")
        await websocket.send_json({"error": "Connection timeout"})
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected")
        metrics.increment("ws_disconnects")
    except Exception as e:
        logger.error(f"[WS] Unexpected error: {e}")
        metrics.record_error("ws_unexpected_error")
        try:
            await websocket.send_json({"error": "Internal server error"})
        except:
            pass
    finally:
        # Save conversation and cost summary
        if cost_tracker and convo_logger:
            try:
                cost_summary = cost_tracker.get_summary()
                logger.info(f"[COST] Session {session_id}: ${cost_summary['cost_usd']:.6f}")
                logger.info(f"[COST] Tokens: {cost_summary['tokens']}")
                
                filepath = convo_logger.save(cost_summary)
                if filepath:
                    logger.info(f"[SESSION] Saved to {filepath}")
            except Exception as e:
                logger.error(f"[SESSION] Failed to save: {e}")
        
        if azure_ws and not azure_ws.closed:
            await azure_ws.close()
            logger.info("[WS] Azure connection closed")
        try:
            await websocket.close()
        except:
            pass

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from resilience import azure_circuit, rag_circuit
        
        rag_status = "healthy" if rag else "not_initialized"
        
        return JSONResponse({
            "status": "healthy",
            "environment": Config.ENV,
            "rag_service": rag_status,
            "circuit_breakers": {
                "azure": azure_circuit.state.value,
                "rag": rag_circuit.state.value
            },
            "metrics": metrics.get_stats()
        })
    except Exception as e:
        return JSONResponse(
            {"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@app.get("/sessions")
async def list_sessions():
    """List all saved conversation sessions"""
    try:
        log_dir = "conversations"
        if not os.path.exists(log_dir):
            return JSONResponse({"sessions": []})
        
        sessions = []
        for filename in os.listdir(log_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(log_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        sessions.append({
                            "session_id": data.get("session_id"),
                            "kb_id": data.get("kb_id"),
                            "start_time": data.get("start_time"),
                            "duration_seconds": data.get("duration_seconds"),
                            "message_count": data.get("message_count"),
                            "cost_usd": data.get("cost", {}).get("cost_usd", 0),
                            "filename": filename
                        })
                except Exception as e:
                    logger.error(f"Failed to read {filename}: {e}")
        
        # Sort by start time (newest first)
        sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return JSONResponse({"sessions": sessions, "total": len(sessions)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full conversation details for a session"""
    try:
        log_dir = "conversations"
        for filename in os.listdir(log_dir):
            if filename.startswith(session_id) and filename.endswith(".json"):
                filepath = os.path.join(log_dir, filename)
                with open(filepath, 'r') as f:
                    return JSONResponse(json.load(f))
        
        return JSONResponse({"error": "Session not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/cost-summary")
async def get_cost_summary():
    """Get cost summary for all sessions"""
    try:
        log_dir = "conversations"
        if not os.path.exists(log_dir):
            return JSONResponse({"total_cost": 0, "sessions": 0})
        
        total_cost = 0
        total_tokens = {"text_input": 0, "text_output": 0, "audio_input": 0, "audio_output": 0}
        session_count = 0
        
        for filename in os.listdir(log_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(log_dir, filename), 'r') as f:
                        data = json.load(f)
                        cost = data.get("cost", {})
                        total_cost += cost.get("cost_usd", 0)
                        tokens = cost.get("tokens", {})
                        for key in total_tokens:
                            total_tokens[key] += tokens.get(key, 0)
                        session_count += 1
                except:
                    pass
        
        return JSONResponse({
            "total_cost_usd": round(total_cost, 6),
            "total_sessions": session_count,
            "total_tokens": total_tokens,
            "average_cost_per_session": round(total_cost / session_count, 6) if session_count > 0 else 0
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/sessions-ui")
async def sessions_ui():
    """Sessions dashboard UI"""
    try:
        with open("sessions.html", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>sessions.html not found</h1>", status_code=500)

@app.get("/metrics")
async def get_metrics():
    """Metrics endpoint"""
    return JSONResponse(metrics.get_stats())

@app.get("/")
async def get():
    try:
        with open("index.html", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>index.html not found</h1>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server in {Config.ENV} environment")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
