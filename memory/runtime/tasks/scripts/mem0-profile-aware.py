#!/usr/bin/env python3
"""
Mem0 Profile-Aware Helper — Memory isolation per Hermes profile.

CRITICAL RULES:
1. Each Hermes profile uses profile name as mem0 user_id
2. NEVER mix memories between profiles - strict namespace isolation  
3. Local memories already profile-isolated by HERMES_HOME
4. Mem0 mirrors this: user_id = profile_name

Profile → Mem0 user_id:
- chief-orchestrator → user_id="chief-orchestrator"
- project-lead-alpha → user_id="project-lead-alpha"

Usage:
    from workspace.memories.mem0_profile_aware import store_memory, search_memory
    
    # Automatically scoped to current profile
    store_memory("Session 4 summary...", {"session": "4"})
    results = search_memory("security audit")
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False


def _load_env():
    """Load .env from current profile."""
    hermes_home = os.getenv("HERMES_HOME", "/home/hermesuser/.hermes/profiles/chief-orchestrator")
    env_file = Path(hermes_home) / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def get_current_profile_name() -> str:
    """Extract profile name from HERMES_HOME."""
    hermes_home = os.getenv("HERMES_HOME")
    if not hermes_home:
        raise ValueError("HERMES_HOME not set")
    
    path_parts = Path(hermes_home).parts
    if "profiles" in path_parts:
        profile_idx = path_parts.index("profiles")
        if len(path_parts) > profile_idx + 1:
            return path_parts[profile_idx + 1]
    
    return Path(hermes_home).name


def get_client() -> MemoryClient:
    """Get Mem0 client (user_id passed per-operation)."""
    if not MEM0_AVAILABLE:
        raise ImportError("mem0ai not available")
    
    _load_env()
    api_key = os.getenv("MEM0_API_KEY")
    if not api_key:
        raise ValueError("MEM0_API_KEY not found")
    
    return MemoryClient(api_key=api_key)


def store_memory(
    content: str,
    metadata: Optional[Dict] = None,
    profile_name: Optional[str] = None
) -> Dict:
    """
    Store memory scoped to profile.
    
    Args:
        content: Memory content
        metadata: Optional metadata
        profile_name: Override profile (auto-detected if None)
    
    Returns:
        API response
    """
    client = get_client()
    profile = profile_name or get_current_profile_name()
    
    final_metadata = metadata or {}
    final_metadata["profile"] = profile
    
    result = client.add(
        messages=[{"role": "assistant", "content": content}],
        user_id=profile,  # CRITICAL: profile name as user_id
        metadata=final_metadata
    )
    
    return result


def search_memory(
    query: str,
    metadata_filters: Optional[Dict] = None,
    profile_name: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """
    Search memories within profile only.
    
    Args:
        query: Search query
        metadata_filters: Optional metadata filters
        profile_name: Override profile
        limit: Max results
    
    Returns:
        Search results scoped to profile
    """
    client = get_client()
    profile = profile_name or get_current_profile_name()
    
    # CRITICAL: user_id in filters enforces profile isolation
    filters = {"user_id": profile}
    
    if metadata_filters:
        filters["AND"] = [metadata_filters]
    
    result = client.search(
        query=query,
        filters=filters,
        limit=limit
    )
    
    return result


def get_profile_stats(profile_name: Optional[str] = None) -> Dict:
    """Get memory stats for profile."""
    profile = profile_name or get_current_profile_name()
    results = search_memory("", profile_name=profile, limit=1000)
    memories = results.get("results", [])
    
    return {
        "profile": profile,
        "total": len(memories),
        "memories": memories
    }


if __name__ == "__main__":
    print("Testing profile-aware mem0...")
    try:
        profile = get_current_profile_name()
        print(f"✓ Profile: {profile}")
        
        client = get_client()
        print(f"✓ Client ready")
        
        results = search_memory("session")
        print(f"✓ Search: {len(results.get('results', []))} memories")
        
        print(f"\n✓✓ Profile-aware mem0 operational (user_id={profile})")
    except Exception as e:
        print(f"✗ Error: {e}")
