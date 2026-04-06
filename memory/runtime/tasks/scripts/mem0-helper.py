#!/usr/bin/env python3
"""
Mem0 Helper — Simplified memory storage and retrieval for Hermes Agent sessions.

Usage:
    from workspace.memories.mem0_helper import store_session, search_memory, get_client

Example:
    # Store a session
    store_session(
        session_num=4,
        content="Session 4 summary...",
        focus="orchestrator_instantiation",
        agents_created=2
    )
    
    # Search memories
    results = search_memory("security audit")
    
    # Advanced search with metadata
    results = search_memory(
        "agent instantiation",
        metadata_filters={"focus": "orchestrator_instantiation"}
    )
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    print("WARNING: mem0ai package not installed. Run: pip install mem0ai")


def _load_env():
    """Load .env file from profile directory."""
    env_file = Path("/home/hermesuser/.hermes/profiles/chief-orchestrator/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def get_client() -> MemoryClient:
    """Get initialized Mem0 client."""
    if not MEM0_AVAILABLE:
        raise ImportError("mem0ai package not available")
    
    _load_env()
    api_key = os.getenv("MEM0_API_KEY")
    
    if not api_key:
        raise ValueError("MEM0_API_KEY not found in environment")
    
    return MemoryClient(api_key=api_key)


def store_session(
    session_num: int,
    content: str,
    focus: str,
    agents_created: int = 0,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Store a session memory in Mem0.
    
    Args:
        session_num: Session number (1, 2, 3, ...)
        content: Full session summary/description
        focus: Short focus keyword (e.g., "security_audit", "constitution")
        agents_created: Number of agents instantiated this session
        metadata: Additional metadata dict
    
    Returns:
        API response dict with status and event_id
    """
    client = get_client()
    
    # Build metadata
    session_metadata = {
        "session": str(session_num),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "focus": focus,
        "agents_created": str(agents_created)
    }
    
    if metadata:
        session_metadata.update(metadata)
    
    # Store as assistant message
    messages = [
        {"role": "assistant", "content": content}
    ]
    
    result = client.add(
        messages=messages,
        user_id="chief_orchestrator_profile",
        metadata=session_metadata
    )
    
    return result


def search_memory(
    query: str,
    metadata_filters: Optional[Dict] = None,
    limit: int = 10
) -> Dict:
    """
    Search memories with semantic query.
    
    Args:
        query: Search query string
        metadata_filters: Optional metadata filters (e.g., {"focus": "security_audit"})
        limit: Max results to return
    
    Returns:
        Search results dict with 'results' array
    """
    client = get_client()
    
    # Build filters (user_id required by API)
    filters = {"user_id": "chief_orchestrator_profile"}
    
    if metadata_filters:
        filters["AND"] = [metadata_filters]
    
    result = client.search(
        query=query,
        filters=filters,
        limit=limit
    )
    
    return result


def get_session_memory(session_num: int) -> Dict:
    """
    Retrieve specific session memory by number.
    
    Args:
        session_num: Session number
    
    Returns:
        Search results for that session
    """
    return search_memory(
        query=f"session {session_num}",
        metadata_filters={"session": str(session_num)}
    )


def list_all_sessions() -> List[Dict]:
    """
    List all stored session memories.
    
    Returns:
        List of all session memories sorted by session number
    """
    # Search broadly and filter by session metadata
    result = search_memory(query="session", limit=100)
    
    memories = result.get("results", [])
    
    # Sort by session number if available
    def get_session_num(mem):
        metadata = mem.get("metadata", {})
        try:
            return int(metadata.get("session", 999))
        except (ValueError, TypeError):
            return 999
    
    return sorted(memories, key=get_session_num)


# Example usage
if __name__ == "__main__":
    print("Mem0 Helper — Testing connection...")
    
    try:
        client = get_client()
        print("✓ Connection successful")
        
        # Test search
        results = search_memory("security audit")
        print(f"✓ Search test: found {len(results.get('results', []))} memories")
        
        print("\n✓✓ Mem0 helper is operational!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
