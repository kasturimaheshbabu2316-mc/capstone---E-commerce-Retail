"""
app/memory.py - Multi-Turn Conversational Session Memory
Track: E-Commerce & Retail (Nykaa)
"""

from typing import Dict, List, Any, Optional
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.memory import (
    InMemoryChatMessageHistory,
    SessionMemoryManager,
    get_session_memory,
    SESSION_MEMORY,
)

__all__ = [
    "InMemoryChatMessageHistory",
    "SessionMemoryManager",
    "get_session_memory",
    "SESSION_MEMORY",
]

if __name__ == "__main__":
    mem = get_session_memory()
    mem.record_turn("app-test", "Where is my lipstick order?", "Your lipstick order NYK-1001 is Placed.")
    print("Session history:", mem.get_history_summary("app-test"))
