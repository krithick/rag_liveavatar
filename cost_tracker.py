"""
Cost tracking for Azure OpenAI Realtime API
Pricing: https://platform.openai.com/docs/models/gpt-realtime
"""
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class CostTracker:
    # GPT-4o Realtime API Pricing (as of Jan 2025)
    # Source: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
    PRICES = {
        "text_input": 4.00,      # $4.00 per 1M input tokens
        "text_output": 16.00,    # $16.00 per 1M output tokens
        "audio_input": 32.00,    # $32.00 per 1M audio input tokens
        "audio_output": 64.00    # $64.00 per 1M audio output tokens
    }
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.utcnow()
        self.tokens = {
            "text_input": 0,
            "text_output": 0,
            "audio_input": 0,
            "audio_output": 0
        }
    
    def add_usage(self, usage_data: dict):
        """Add token usage from Azure response"""
        if not usage_data:
            return
        
        # Azure returns usage in different formats
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        input_token_details = usage_data.get("input_token_details", {})
        output_token_details = usage_data.get("output_token_details", {})
        
        # Text tokens
        self.tokens["text_input"] += input_token_details.get("text_tokens", input_tokens)
        self.tokens["text_output"] += output_token_details.get("text_tokens", output_tokens)
        
        # Audio tokens
        self.tokens["audio_input"] += input_token_details.get("audio_tokens", 0)
        self.tokens["audio_output"] += output_token_details.get("audio_tokens", 0)
        
        logger.info(f"[COST] Session {self.session_id}: +{input_tokens} in, +{output_tokens} out")
    
    def calculate_cost(self) -> Dict[str, float]:
        """Calculate total cost"""
        costs = {}
        total = 0.0
        
        for token_type, count in self.tokens.items():
            cost = (count / 1_000_000) * self.PRICES[token_type]
            costs[token_type] = round(cost, 6)
            total += cost
        
        return {
            "breakdown": costs,
            "total": round(total, 6),
            "tokens": self.tokens,
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    def get_summary(self) -> dict:
        """Get cost summary"""
        cost_data = self.calculate_cost()
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": cost_data["duration_seconds"],
            "tokens": cost_data["tokens"],
            "cost_usd": cost_data["total"],
            "cost_breakdown": cost_data["breakdown"]
        }
