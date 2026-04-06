# Mem0 Cloud Memory Policy

## Purpose

Define Mem0-first memory storage, retrieval, and safety controls for this runtime.

## Hard Disclosure

Mem0 is the final durable memory record. Deleting memory from Mem0 is irreversible loss.

The agent is never permitted to delete memory from Mem0.

## Prohibited Commands

- `delete_memory`
- `delete_all_memories`
- `delete_entities`
- `mem0_delete_memory`
- `mem0_delete_all_memories`
- `mem0_delete_entities`
- `mem0_batch_delete_memories`
- `mem0_reset_account`

## Available Mem0 Command Surface (Documented for this runtime)

### Official MCP

- `add_memory`
- `search_memories`
- `get_memories`
- `get_memory`
- `update_memory`
- `delete_memory` (prohibited by this policy)
- `delete_all_memories` (prohibited by this policy)
- `delete_entities` (prohibited by this policy)
- `list_entities`

### Local Hermes Mem0 Tools

- `mem0_profile`
- `mem0_search`
- `mem0_conclude`
- `mem0_add_memory`
- `mem0_get_memories`
- `mem0_get_memory`
- `mem0_update_memory`
- `mem0_delete_memory` (prohibited by this policy)
- `mem0_delete_all_memories` (prohibited by this policy)
- `mem0_list_entities`
- `mem0_delete_entities` (prohibited by this policy)
- `mem0_memory_history`
- `mem0_feedback`
- `mem0_batch_update_memories`
- `mem0_batch_delete_memories` (prohibited by this policy)
- `mem0_reset_account` (prohibited by this policy)
- `mem0_create_memory_export`
- `mem0_get_memory_export`
- `mem0_get_memory_export_summary`
- `mem0_get_webhooks`
- `mem0_create_webhook`
- `mem0_update_webhook`
- `mem0_delete_webhook`
- `mem0_project_get`
- `mem0_project_update`
- `mem0_project_create`
- `mem0_project_delete`
- `mem0_project_members`
- `mem0_project_member_add`
- `mem0_project_member_update`
- `mem0_project_member_remove`
- `mem0_legacy_project_get`
- `mem0_legacy_project_update`
- `mem0_chat` (stub)
- `mem0_async_invoke`

## Required Metadata For Every Memory Write

- `memory_title`
- `category`
- `keywords`
- `entity_type`
- `entity_id`
- `profile_or_role`
- `source_layer`
- `source_path` (for local mirrors)
- `created_at_utc`
- `updated_at_utc`
- `concept_refs`

## Upload-First Local Reorganization Rule

Before local memory consolidation, rewrite, or pruning:

1. Upload full extract of target memory items to Mem0.
2. Verify successful persistence and metadata completeness.
3. Only then reorganize local files.
4. If upload fails, abort local mutation and retry sync.

## Retrieval Strategy

1. Read local `working` context.
2. Query Mem0 index concepts.
3. Load relevant Mem0 semantic memories.
4. Enrich with Mem0 episodic context only when needed.
5. Rank relevance and minimize loaded context.

## Source Canon

- `../../state/memory-integration-override.md`
- `../templates/memory-append-snippet-template.md`
- Mem0 docs and tool surface listed in plan

## Read Next

- `../../../knowledge/references/index/concept-index.md`
- `../../../knowledge/concepts/foundation-memory-contract.md`

## Memory Network

- `../../../knowledge/references/index/memory-network.md`
