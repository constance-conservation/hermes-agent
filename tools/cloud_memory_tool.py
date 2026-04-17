#!/usr/bin/env python3
"""
Cloud memory integrations — LangSmith observability, LangMem semantic memory (LangGraph store),
Zep Cloud temporal graph memory, and Letta pinned/archival memory.

These are **tools** (not memory.provider plugins). Mem0 remains the single optional external
MemoryManager provider; use Mem0 for extract/search/rerank and these tools for Zep graph,
Letta blocks, LangMem lifecycle notes, and LangSmith workspace checks.

Host-scoped keys: set HERMES_MEMORY_KEY_SUFFIX=OPERATOR or DROPLET and matching
LANGSMITH_API_KEY_OPERATOR|_DROPLET, ZEP_API_KEY_*, LETTA_API_KEY_* in profile .env.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from hermes_constants import get_hermes_home

from tools.registry import registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key resolution (never cross-operator/droplet)
# ---------------------------------------------------------------------------


def _memory_suffix() -> Optional[str]:
    raw = (os.environ.get("HERMES_MEMORY_KEY_SUFFIX") or "").strip().upper()
    if raw in ("OPERATOR", "DROPLET"):
        return raw
    # Infer: exactly one suffixed LangSmith key set
    op = bool((os.environ.get("LANGSMITH_API_KEY_OPERATOR") or "").strip())
    dr = bool((os.environ.get("LANGSMITH_API_KEY_DROPLET") or "").strip())
    if op and not dr:
        return "OPERATOR"
    if dr and not op:
        return "DROPLET"
    return None


def _scoped_api_key(base: str) -> str:
    """Resolve LANGSMITH_API_KEY / ZEP_API_KEY / LETTA_API_KEY for this host."""
    suf = _memory_suffix()
    if suf:
        v = (os.environ.get(f"{base}_{suf}") or "").strip()
        if v:
            return v
    # Non-suffixed fallback (local dev only)
    return (os.environ.get(base) or "").strip()


def _langsmith_key() -> str:
    return _scoped_api_key("LANGSMITH_API_KEY")


def _zep_key() -> str:
    return _scoped_api_key("ZEP_API_KEY")


def _letta_key() -> str:
    return _scoped_api_key("LETTA_API_KEY")


# ---------------------------------------------------------------------------
# LangMem — durable BaseStore backed by SQLite (singleton)
# ---------------------------------------------------------------------------

_LANGMEM_STORE = None
_LANGMEM_MANAGE = None
_LANGMEM_SEARCH = None


class HermesLangMemSQLiteStore:
    """Minimal LangGraph BaseStore-compatible adapter with on-disk durability.

    LangMem's tools require a LangGraph BaseStore. We implement a pragmatic subset:
    - put/get/delete: store memory documents by uuid
    - search: simple FTS5 if available, else LIKE fallback

    This is not embedding-based semantic search; Mem0 remains the primary semantic+rerank store.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS langmem_items (
                  id TEXT PRIMARY KEY,
                  namespace TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at REAL NOT NULL
                );
                """
            )
            # Best-effort FTS index (optional)
            try:
                con.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS langmem_items_fts
                    USING fts5(id, namespace, content, content='langmem_items', content_rowid='rowid');
                    """
                )
                con.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS langmem_items_ai AFTER INSERT ON langmem_items BEGIN
                      INSERT INTO langmem_items_fts(rowid, id, namespace, content) VALUES (new.rowid, new.id, new.namespace, new.content);
                    END;
                    """
                )
                con.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS langmem_items_ad AFTER DELETE ON langmem_items BEGIN
                      INSERT INTO langmem_items_fts(langmem_items_fts, rowid, id, namespace, content) VALUES('delete', old.rowid, old.id, old.namespace, old.content);
                    END;
                    """
                )
                con.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS langmem_items_au AFTER UPDATE ON langmem_items BEGIN
                      INSERT INTO langmem_items_fts(langmem_items_fts, rowid, id, namespace, content) VALUES('delete', old.rowid, old.id, old.namespace, old.content);
                      INSERT INTO langmem_items_fts(rowid, id, namespace, content) VALUES (new.rowid, new.id, new.namespace, new.content);
                    END;
                    """
                )
            except Exception:
                pass
            con.commit()
        finally:
            con.close()

    # --- BaseStore-ish API used by LangMem tools --------------------------
    # langgraph.store.base.BaseStore defines: put/get/delete/search + batch variants.
    # LangMem tools call the sync methods directly.

    def put(self, namespace: Tuple[str, ...], key: str, value: dict) -> None:
        content = (value or {}).get("content") or ""
        ns = "/".join(namespace)
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO langmem_items(id, namespace, content, created_at) VALUES(?,?,?,?)",
                (key, ns, str(content), time.time()),
            )
            con.commit()
        finally:
            con.close()

    def get(self, namespace: Tuple[str, ...], key: str):
        ns = "/".join(namespace)
        con = self._connect()
        try:
            row = con.execute(
                "SELECT id, namespace, content, created_at FROM langmem_items WHERE id=? AND namespace=?",
                (key, ns),
            ).fetchone()
            if not row:
                return None
            from langgraph.store.base import Item

            dt = datetime.fromtimestamp(float(row["created_at"]), tz=timezone.utc)
            return Item(
                key=row["id"],
                namespace=tuple(str(row["namespace"]).split("/")) if row["namespace"] else tuple(),
                value={"content": row["content"]},
                created_at=dt,
                updated_at=dt,
            )
        finally:
            con.close()

    def delete(self, namespace: Tuple[str, ...], key: str) -> None:
        ns = "/".join(namespace)
        con = self._connect()
        try:
            con.execute("DELETE FROM langmem_items WHERE id=? AND namespace=?", (key, ns))
            con.commit()
        finally:
            con.close()

    def search(
        self,
        namespace_prefix: Tuple[str, ...],
        query: str,
        limit: int = 10,
        offset: int = 0,
        filter: dict | None = None,
    ):
        ns_prefix = "/".join(namespace_prefix)
        q = (query or "").strip()
        con = self._connect()
        try:
            # Prefer FTS if present
            try:
                rows = con.execute(
                    """
                    SELECT i.id, i.namespace, i.content, i.created_at
                    FROM langmem_items_fts f
                    JOIN langmem_items i ON i.rowid = f.rowid
                    WHERE f.content MATCH ? AND i.namespace LIKE ?
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                    """,
                    (q, ns_prefix + "%", int(limit), int(offset)),
                ).fetchall()
            except Exception:
                rows = con.execute(
                    """
                    SELECT id, namespace, content, created_at
                    FROM langmem_items
                    WHERE namespace LIKE ? AND content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (ns_prefix + "%", f"%{q}%", int(limit), int(offset)),
                ).fetchall()
            from langgraph.store.base import Item

            out: List[Item] = []
            for r in rows:
                dt = datetime.fromtimestamp(float(r["created_at"]), tz=timezone.utc)
                out.append(
                    Item(
                        key=r["id"],
                        namespace=tuple(str(r["namespace"]).split("/")) if r["namespace"] else tuple(),
                        value={"content": r["content"]},
                        created_at=dt,
                        updated_at=dt,
                    )
                )
            return out
        finally:
            con.close()


def _langmem_store_path() -> Path:
    return get_hermes_home() / "runtime" / "langmem.sqlite3"


def _get_langmem_tools():
    global _LANGMEM_STORE, _LANGMEM_MANAGE, _LANGMEM_SEARCH
    if _LANGMEM_STORE is None:
        from langmem import create_manage_memory_tool, create_search_memory_tool

        # Durable store per profile
        _LANGMEM_STORE = HermesLangMemSQLiteStore(_langmem_store_path())
        ns = ("hermes", "langmem", str(get_hermes_home()))
        _LANGMEM_MANAGE = create_manage_memory_tool(
            ns,
            store=_LANGMEM_STORE,
            name="langmem_manage_inner",
        )
        _LANGMEM_SEARCH = create_search_memory_tool(
            ns,
            store=_LANGMEM_STORE,
            name="langmem_search_inner",
        )
    return _LANGMEM_MANAGE, _LANGMEM_SEARCH


def _letta_agent_id_path() -> Path:
    return get_hermes_home() / "runtime" / "letta_default_agent_id.txt"


def _read_or_create_letta_agent(client: Any) -> str:
    p = _letta_agent_id_path()
    if p.exists():
        aid = p.read_text(encoding="utf-8").strip()
        if aid:
            try:
                client.agents.retrieve(aid)
                return aid
            except Exception:
                logger.warning("letta: stale agent id, recreating")

    p.parent.mkdir(parents=True, exist_ok=True)
    profile = Path(get_hermes_home()).name
    name = f"hermes-{profile}-memory"
    state = client.agents.create(
        name=name,
        memory_blocks=[
            {"label": "human", "value": "Hermes user — preferences and facts go here."},
            {
                "label": "persona",
                "value": "Hermes orchestrator — use archival search for long history.",
            },
        ],
    )
    aid = str(state.id)
    p.write_text(aid, encoding="utf-8")
    return aid


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _langsmith_workspace_info(_: str, **kw: Any) -> str:
    key = _langsmith_key()
    if not key:
        return json.dumps(
            {
                "success": False,
                "error": "Missing LANGSMITH_API_KEY_OPERATOR or LANGSMITH_API_KEY_DROPLET (or HERMES_MEMORY_KEY_SUFFIX).",
            }
        )
    try:
        from langsmith import Client

        c = Client(api_key=key)
        # Use Client.info (does not require sessions/projects permissions).
        info = getattr(c, "info", None)
        payload = info if isinstance(info, dict) else (info() if callable(info) else {})
        return json.dumps(
            {
                "success": True,
                "info": payload,
                "tracing_hint": "Set LANGCHAIN_TRACING_V2=true and LANGSMITH_TRACING=true for traces.",
            }
        )
    except Exception as e:
        logger.exception("langsmith_workspace_info")
        return json.dumps({"success": False, "error": str(e)})


def _langmem_semantic_memory(
    action: str,
    content: str = "",
    memory_id: str = "",
    query: str = "",
    limit: int = 10,
    mem_action: str = "",
    **kw: Any,
) -> str:
    try:
        manage, search = _get_langmem_tools()
    except ImportError as e:
        return json.dumps(
            {
                "success": False,
                "error": f"langmem/langgraph not installed: {e}. pip install 'hermes-agent[memory_services]'",
            }
        )
    action = (action or "search").strip().lower()
    try:
        if action == "search":
            if not (query or "").strip():
                return json.dumps({"success": False, "error": "query required for search"})
            out = search.invoke({"query": query.strip(), "limit": int(limit)})
            return json.dumps({"success": True, "result": str(out)})
        if action in ("create", "update", "delete"):
            payload: Dict[str, Any] = {"action": action, "content": content or None, "id": memory_id or None}
            out = manage.invoke(payload)
            return json.dumps({"success": True, "result": str(out)})
        if action == "manage":
            ma = (mem_action or "create").strip().lower()
            if ma not in ("create", "update", "delete"):
                ma = "create"
            payload = {"action": ma, "content": content or None, "id": memory_id or None}
            out = manage.invoke(payload)
            return json.dumps({"success": True, "result": str(out)})
        return json.dumps({"success": False, "error": f"unknown action {action!r}"})
    except Exception as e:
        logger.exception("langmem_semantic_memory")
        return json.dumps({"success": False, "error": str(e)})


def _zep_knowledge_search(query: str, user_id: str = "", limit: int = 8, **kw: Any) -> str:
    key = _zep_key()
    if not key:
        return json.dumps({"success": False, "error": "Missing ZEP_API_KEY_OPERATOR or ZEP_API_KEY_DROPLET."})
    uid = (user_id or os.environ.get("ZEP_DEFAULT_USER_ID") or "hermes-default").strip()
    try:
        from zep_cloud.client import Zep

        z = Zep(api_key=key)
        res = z.graph.search(query=query, user_id=uid, limit=int(limit))
        edges = getattr(res, "edges", None) or []
        facts = []
        for e in edges[: int(limit)]:
            facts.append(
                {
                    "fact": getattr(e, "fact", str(e)),
                    "uuid": getattr(e, "uuid_", getattr(e, "uuid", None)),
                }
            )
        return json.dumps({"success": True, "user_id": uid, "facts": facts})
    except Exception as e:
        logger.exception("zep_knowledge_search")
        return json.dumps({"success": False, "error": str(e)})


def _zep_user_ensure(user_id: str = "", **kw: Any) -> str:
    key = _zep_key()
    if not key:
        return json.dumps({"success": False, "error": "Missing ZEP_API_KEY_* for this host."})
    uid = (user_id or os.environ.get("ZEP_DEFAULT_USER_ID") or "hermes-default").strip()
    try:
        from zep_cloud.client import Zep

        z = Zep(api_key=key)
        u = z.user.add(user_id=uid, metadata={"source": "hermes", "profile": Path(get_hermes_home()).name})
        return json.dumps({"success": True, "user_id": getattr(u, "user_id", uid)})
    except Exception as e:
        logger.exception("zep_user_ensure")
        return json.dumps({"success": False, "error": str(e)})


def _letta_memory_turn(message: str, agent_id: str = "", **kw: Any) -> str:
    key = _letta_key()
    if not key:
        return json.dumps({"success": False, "error": "Missing LETTA_API_KEY_OPERATOR or LETTA_API_KEY_DROPLET."})
    if not (message or "").strip():
        return json.dumps({"success": False, "error": "message required"})
    try:
        from letta_client import Letta
    except ImportError as e:
        return json.dumps({"success": False, "error": f"letta-client not installed: {e}"})

    try:
        client = Letta(api_key=key)
        aid = (agent_id or "").strip() or _read_or_create_letta_agent(client)
        resp = client.agents.messages.create(
            agent_id=aid,
            messages=[{"role": "user", "content": message.strip()}],
        )
        text = str(resp)
        return json.dumps({"success": True, "agent_id": aid, "response_excerpt": text[:12000]})
    except Exception as e:
        logger.exception("letta_memory_turn")
        return json.dumps({"success": False, "error": str(e)})


def _letta_memory_blocks(agent_id: str = "", **kw: Any) -> str:
    key = _letta_key()
    if not key:
        return json.dumps({"success": False, "error": "Missing LETTA_API_KEY_* for this host."})
    try:
        from letta_client import Letta
    except ImportError as e:
        return json.dumps({"success": False, "error": str(e)})
    try:
        client = Letta(api_key=key)
        aid = (agent_id or "").strip() or _read_or_create_letta_agent(client)
        st = client.agents.retrieve(agent_id=aid, include=["agent.blocks"])
        blocks = getattr(st, "memory_blocks", None) or getattr(st, "blocks", []) or []
        out = []
        for b in blocks:
            out.append(
                {
                    "label": getattr(b, "label", None),
                    "value": (getattr(b, "value", None) or "")[:4000],
                }
            )
        return json.dumps({"success": True, "agent_id": aid, "blocks": out})
    except Exception as e:
        logger.exception("letta_memory_blocks")
        return json.dumps({"success": False, "error": str(e)})


def _check_langsmith() -> bool:
    return bool(_langsmith_key())


def _check_zep() -> bool:
    return bool(_zep_key())


def _check_letta() -> bool:
    return bool(_letta_key())


def _check_langmem() -> bool:
    try:
        import langmem  # noqa: F401
        import langgraph  # noqa: F401
        return True
    except ImportError:
        return False


registry.register(
    name="langsmith_workspace_info",
    toolset="memory_cloud",
    schema={
        "name": "langsmith_workspace_info",
        "description": (
            "List LangSmith projects for observability (uses host-scoped LANGSMITH_API_KEY_*). "
            "Does not replace Mem0 — use for traces/debugging when LANGCHAIN_TRACING_V2 is enabled."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "_unused": {
                    "type": "string",
                    "description": "Optional no-op for older callers.",
                },
            },
        },
    },
    handler=lambda args, **kw: _langsmith_workspace_info(args.get("_unused", ""), **kw),
    check_fn=_check_langsmith,
    requires_env=[],
    description="LangSmith project list (host-scoped API key).",
    emoji="🔭",
)

registry.register(
    name="langmem_semantic_memory",
    toolset="memory_cloud",
    schema={
        "name": "langmem_semantic_memory",
        "description": (
            "LangMem-style semantic memory using an in-process LangGraph store (singleton per process). "
            "action=search|create|update|delete. For create/update/delete use content and optional memory_id. "
            "Complements Mem0 (cloud extract/search) with fast lifecycle notes; not persisted across process restarts unless you add external store."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "create", "update", "delete", "manage"],
                    "description": "search = query store; create/update/delete/manage = write",
                },
                "query": {"type": "string", "description": "Search query (required for search)."},
                "content": {"type": "string", "description": "Text for create/update."},
                "memory_id": {"type": "string", "description": "UUID for update/delete."},
                "limit": {"type": "integer", "description": "Max search hits (default 10)."},
                "mem_action": {
                    "type": "string",
                    "enum": ["create", "update", "delete"],
                    "description": "When action=manage, which write op.",
                },
            },
            "required": ["action"],
        },
    },
    handler=lambda args, **kw: _langmem_semantic_memory(
        str(args.get("action", "search")),
        content=str(args.get("content") or ""),
        memory_id=str(args.get("memory_id") or ""),
        query=str(args.get("query") or ""),
        limit=int(args.get("limit") or 10),
        mem_action=str(args.get("mem_action") or ""),
        **kw,
    ),
    check_fn=_check_langmem,
    requires_env=[],
    description="LangMem semantic memory (LangGraph InMemoryStore).",
    emoji="🧠",
)

registry.register(
    name="zep_knowledge_search",
    toolset="memory_cloud",
    schema={
        "name": "zep_knowledge_search",
        "description": (
            "Search Zep Cloud temporal knowledge graph for facts relevant to the query. "
            "Uses ZEP_API_KEY_* and optional user_id (default ZEP_DEFAULT_USER_ID or hermes-default)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search."},
                "user_id": {"type": "string", "description": "Zep user id namespace."},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    handler=lambda args, **kw: _zep_knowledge_search(
        args.get("query", ""),
        user_id=args.get("user_id") or "",
        limit=int(args.get("limit") or 8),
        **kw,
    ),
    check_fn=_check_zep,
    requires_env=[],
    description="Zep graph search (temporal semantics).",
    emoji="🕸️",
)

registry.register(
    name="zep_user_ensure",
    toolset="memory_cloud",
    schema={
        "name": "zep_user_ensure",
        "description": "Create or ensure a Zep Cloud user id for graph/memory scope.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Stable user id (default hermes-default)."},
            },
        },
    },
    handler=lambda args, **kw: _zep_user_ensure(user_id=args.get("user_id") or "", **kw),
    check_fn=_check_zep,
    requires_env=[],
    description="Zep user upsert.",
    emoji="👤",
)

registry.register(
    name="letta_memory_turn",
    toolset="memory_cloud",
    schema={
        "name": "letta_memory_turn",
        "description": (
            "Send a user message to the host-scoped Letta agent and return its reply. "
            "Pinned memory blocks + archival behavior follow Letta Cloud defaults; agent id is cached under HERMES_HOME/runtime/."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "User message to the Letta agent."},
                "agent_id": {"type": "string", "description": "Optional existing Letta agent id."},
            },
            "required": ["message"],
        },
    },
    handler=lambda args, **kw: _letta_memory_turn(
        args.get("message", ""),
        agent_id=args.get("agent_id") or "",
        **kw,
    ),
    check_fn=_check_letta,
    requires_env=[],
    description="Letta agent turn (memory-first).",
    emoji="💬",
)

registry.register(
    name="letta_memory_blocks",
    toolset="memory_cloud",
    schema={
        "name": "letta_memory_blocks",
        "description": "Read Letta memory blocks (pinned context) for the default or given agent.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
        },
    },
    handler=lambda args, **kw: _letta_memory_blocks(agent_id=args.get("agent_id") or "", **kw),
    check_fn=_check_letta,
    requires_env=[],
    description="Letta block snapshot.",
    emoji="📌",
)
