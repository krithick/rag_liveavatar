"""
Tests for cost tracking
"""
import pytest
from cost_tracker import CostTracker

def test_cost_tracker_initialization():
    """Test cost tracker initialization"""
    tracker = CostTracker("test-session-123")
    assert tracker.session_id == "test-session-123"
    assert tracker.tokens["text_input"] == 0
    assert tracker.tokens["audio_output"] == 0

def test_add_usage_text_tokens():
    """Test adding text token usage"""
    tracker = CostTracker("test-session")
    
    usage = {
        "input_tokens": 100,
        "output_tokens": 50,
        "input_token_details": {"text_tokens": 100},
        "output_token_details": {"text_tokens": 50}
    }
    
    tracker.add_usage(usage)
    
    assert tracker.tokens["text_input"] == 100
    assert tracker.tokens["text_output"] == 50

def test_add_usage_audio_tokens():
    """Test adding audio token usage"""
    tracker = CostTracker("test-session")
    
    usage = {
        "input_tokens": 1000,
        "output_tokens": 2000,
        "input_token_details": {"audio_tokens": 1000},
        "output_token_details": {"audio_tokens": 2000}
    }
    
    tracker.add_usage(usage)
    
    assert tracker.tokens["audio_input"] == 1000
    assert tracker.tokens["audio_output"] == 2000

def test_calculate_cost_text_only():
    """Test cost calculation for text tokens"""
    tracker = CostTracker("test-session")
    tracker.tokens["text_input"] = 1_000_000  # 1M tokens
    tracker.tokens["text_output"] = 1_000_000  # 1M tokens
    
    cost = tracker.calculate_cost()
    
    # $5 for input + $20 for output = $25
    assert cost["total"] == 25.0
    assert cost["breakdown"]["text_input"] == 5.0
    assert cost["breakdown"]["text_output"] == 20.0

def test_calculate_cost_audio_only():
    """Test cost calculation for audio tokens"""
    tracker = CostTracker("test-session")
    tracker.tokens["audio_input"] = 1_000_000  # 1M tokens
    tracker.tokens["audio_output"] = 1_000_000  # 1M tokens
    
    cost = tracker.calculate_cost()
    
    # $100 for input + $200 for output = $300
    assert cost["total"] == 300.0
    assert cost["breakdown"]["audio_input"] == 100.0
    assert cost["breakdown"]["audio_output"] == 200.0

def test_calculate_cost_mixed():
    """Test cost calculation for mixed tokens"""
    tracker = CostTracker("test-session")
    tracker.tokens["text_input"] = 500_000  # 0.5M tokens
    tracker.tokens["text_output"] = 250_000  # 0.25M tokens
    tracker.tokens["audio_input"] = 100_000  # 0.1M tokens
    tracker.tokens["audio_output"] = 50_000   # 0.05M tokens
    
    cost = tracker.calculate_cost()
    
    # Text: $2.5 + $5 = $7.5
    # Audio: $10 + $10 = $20
    # Total: $27.5
    assert cost["total"] == 27.5

def test_get_summary():
    """Test getting cost summary"""
    tracker = CostTracker("test-session")
    tracker.tokens["text_input"] = 1000
    tracker.tokens["text_output"] = 500
    
    summary = tracker.get_summary()
    
    assert summary["session_id"] == "test-session"
    assert "start_time" in summary
    assert "duration_seconds" in summary
    assert summary["tokens"]["text_input"] == 1000
    assert summary["tokens"]["text_output"] == 500
    assert "cost_usd" in summary
