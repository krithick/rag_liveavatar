# Dynamic RAG with Realtime API

WebSocket-based implementation with **per-question** knowledge base searches.

## Key Difference from WebRTC Version

### WebRTC (Old - Static RAG)
- ❌ KB context loaded ONCE at connection
- ❌ Can't search for new topics
- ❌ Stops working after 2-4 questions

### WebSocket (New - Dynamic RAG)
- ✅ KB search happens PER QUESTION
- ✅ Can handle any topic dynamically
- ✅ Works for unlimited questions
- ✅ Uses function calling

## How It Works

```
You: "What is Shriram Finance?"
  → AI calls search_knowledge_base("Shriram Finance")
  → Gets relevant chunks
  → Responds with context

You: "What about HDFC Bank?"
  → AI calls search_knowledge_base("HDFC Bank")
  → Gets NEW chunks
  → Responds with NEW context
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` with your credentials

3. Run server:
```bash
python app.py
```

4. Open http://localhost:8002

5. Enter your KB ID and click Connect

6. Start speaking!

## Architecture

```
Browser (Mic) 
    ↓ WebSocket
FastAPI Server
    ↓ WebSocket
Azure Realtime API
    ↓ Function Call
RAG Service → Azure AI Search
    ↓ Context
Azure Realtime API
    ↓ Voice Response
Browser (Speaker)
```

## Advantages

- **Dynamic**: Searches KB per question
- **Scalable**: No context size limits
- **Flexible**: Can search multiple KBs
- **Real-time**: Still voice-to-voice

## Limitations

- More complex than WebRTC
- Requires WebSocket handling
- Slightly higher latency (RAG search time)

## Debugging

Check terminal for:
- `[RAG] Searching: ...` - KB searches
- `[FUNCTION] search_knowledge_base called` - Function calls
- `[WS] Client connected` - Connection status
