# Cost Tracking & Conversation Logging

## Features

### 1. Cost Tracking
Automatically tracks token usage and calculates costs per session based on OpenAI's GPT-4 Realtime pricing.

**Pricing (per 1M tokens):**
- Text Input: $5.00
- Text Output: $20.00
- Audio Input: $100.00
- Audio Output: $200.00

### 2. Conversation Logging
Saves complete conversation history including:
- User messages
- Assistant responses
- Function calls and results
- Audio interactions
- Session metadata
- Cost summary

## Usage

### Automatic Tracking
Every WebSocket session is automatically tracked. When the session ends:
- Cost summary is logged
- Conversation is saved to `conversations/` directory
- Filename format: `{session_id}_{timestamp}.json`

### View Sessions

**List all sessions:**
```bash
curl http://localhost:8003/sessions
```

Response:
```json
{
  "sessions": [
    {
      "session_id": "abc-123",
      "kb_id": "kb_finance",
      "start_time": "2024-01-15T10:30:00",
      "duration_seconds": 245.5,
      "message_count": 12,
      "cost_usd": 0.002345,
      "filename": "abc-123_20240115_103000.json"
    }
  ],
  "total": 1
}
```

**Get specific session:**
```bash
curl http://localhost:8003/sessions/{session_id}
```

Response includes full conversation:
```json
{
  "session_id": "abc-123",
  "kb_id": "kb_finance",
  "start_time": "2024-01-15T10:30:00",
  "end_time": "2024-01-15T10:34:05",
  "duration_seconds": 245.5,
  "message_count": 12,
  "messages": [
    {
      "timestamp": "2024-01-15T10:30:15",
      "role": "user",
      "type": "text",
      "content": "What is Shriram Finance?",
      "metadata": {}
    },
    {
      "timestamp": "2024-01-15T10:30:16",
      "role": "function",
      "type": "function_call",
      "content": "Shriram Finance is...",
      "metadata": {
        "function_name": "search_knowledge_base",
        "arguments": {"query": "Shriram Finance"}
      }
    },
    {
      "timestamp": "2024-01-15T10:30:18",
      "role": "assistant",
      "type": "text",
      "content": "Shriram Finance is a leading NBFC...",
      "metadata": {}
    }
  ],
  "cost": {
    "session_id": "abc-123",
    "start_time": "2024-01-15T10:30:00",
    "duration_seconds": 245.5,
    "tokens": {
      "text_input": 1250,
      "text_output": 3400,
      "audio_input": 0,
      "audio_output": 0
    },
    "cost_usd": 0.074250,
    "cost_breakdown": {
      "text_input": 0.006250,
      "text_output": 0.068000,
      "audio_input": 0.0,
      "audio_output": 0.0
    }
  }
}
```

## Cost Analysis

### Check Logs
After each session, check terminal for cost summary:
```
[COST] Session abc-123: $0.002345
[COST] Tokens: {'text_input': 500, 'text_output': 1200, 'audio_input': 0, 'audio_output': 0}
[SESSION] Saved to conversations/abc-123_20240115_103000.json
```

### Calculate Total Costs
```python
import json
import os

total_cost = 0
for filename in os.listdir("conversations"):
    with open(f"conversations/{filename}") as f:
        data = json.load(f)
        total_cost += data.get("cost", {}).get("cost_usd", 0)

print(f"Total cost: ${total_cost:.6f}")
```

## Cost Optimization Tips

1. **Use text mode when possible** - Audio tokens are 20-40x more expensive
2. **Keep responses concise** - Output tokens cost 4x more than input
3. **Limit RAG context** - Reduce tokens sent to the model
4. **Monitor per-session costs** - Set alerts for expensive sessions
5. **Cache common queries** - Avoid repeated searches

## Example Costs

**Text-only conversation (10 exchanges):**
- Input: ~2,000 tokens = $0.01
- Output: ~5,000 tokens = $0.10
- Total: ~$0.11

**Audio conversation (5 minutes):**
- Audio input: ~50,000 tokens = $5.00
- Audio output: ~100,000 tokens = $20.00
- Total: ~$25.00

**Mixed (text + audio):**
- Text input: 1,000 tokens = $0.005
- Text output: 2,000 tokens = $0.04
- Audio input: 10,000 tokens = $1.00
- Audio output: 20,000 tokens = $4.00
- Total: ~$5.05

## Conversation Analysis

### Export to CSV
```python
import json
import csv

sessions = []
for filename in os.listdir("conversations"):
    with open(f"conversations/{filename}") as f:
        data = json.load(f)
        sessions.append({
            "session_id": data["session_id"],
            "kb_id": data["kb_id"],
            "duration": data["duration_seconds"],
            "messages": data["message_count"],
            "cost": data["cost"]["cost_usd"]
        })

with open("sessions.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["session_id", "kb_id", "duration", "messages", "cost"])
    writer.writeheader()
    writer.writerows(sessions)
```

### Search Conversations
```python
import json
import os

def search_conversations(keyword):
    results = []
    for filename in os.listdir("conversations"):
        with open(f"conversations/{filename}") as f:
            data = json.load(f)
            for msg in data["messages"]:
                if keyword.lower() in msg["content"].lower():
                    results.append({
                        "session_id": data["session_id"],
                        "timestamp": msg["timestamp"],
                        "role": msg["role"],
                        "content": msg["content"]
                    })
    return results

# Find all mentions of "Shriram Finance"
results = search_conversations("Shriram Finance")
```

## Privacy & Compliance

**Data Stored:**
- User queries (text/audio markers)
- Assistant responses
- Function calls and results
- Timestamps and metadata
- Cost information

**Recommendations:**
1. **Encrypt conversations** - Use encryption at rest
2. **Set retention policy** - Auto-delete old conversations
3. **Anonymize data** - Remove PII before storage
4. **Access control** - Restrict who can view sessions
5. **Compliance** - Follow GDPR/CCPA requirements

## Troubleshooting

**Conversations not saving:**
- Check `conversations/` directory exists
- Verify write permissions
- Check logs for errors

**Cost seems incorrect:**
- Verify token counts in Azure response
- Check pricing is up to date
- Compare with Azure billing

**Missing usage data:**
- Azure may not send usage in all events
- Look for `response.done` events
- Check if model supports usage reporting
