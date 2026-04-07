# Memory Governance

## Purpose

This file is the concise foundation for the runtime memory architecture and execution plan.

## Core Principles

- Use a layered memory architecture through domains: `governance`, `actors`, `knowledge`, `runtime`.
- Keep root anchors concise and delegate detail to linked leaf files.
- Prefer linking over duplication.
- Preserve auditability: record material decisions and verification outcomes.
- Keep context lean: load only relevant shards.

## CLAW Verbatim Operating Doctrine

CLAW doctrine excerpt (integrated):

> Use this file as the top-level operating doctrine for a multi-agent coding runtime.  
> Primary principle: code is an artifact; orchestration quality is the product.

> Every work item must move through these states:  
> `new -> clarified -> planned -> executing -> verifying -> review -> done | blocked | failed`

CLAW doctrine excerpt (integrated):

> Treat generated code as an artifact.  
> Treat orchestration quality as the core product.

> Implement and enforce this loop:  
> `Analysis -> Planning -> Coding/Tools -> Verification -> Review -> (repeat until done)`

## Plan Summary Embedded In-Structure

The active consolidation and memory integration plan is implemented through this contract:

1. Read and classify all source directives.
2. Merge overlapping directives into domain-layer docs without losing unique policy meaning.
3. Keep multiple root anchors for startup, governance, memory navigation, and orchestration.
4. Use Mem0 as primary durable memory backend.
5. Keep local files as deterministic anchors and low-latency cache only.
6. Require metadata-rich memory records for high-quality retrieval.
7. Never delete memories from Mem0.
8. Archive superseded files and templates for traceability.

## Read Next

- `security-and-authority.md`
- `../../runtime/tasks/procedures/mem0-cloud-memory-policy.md`
- `../references/index/root-anchors.md`

## Memory Network

- `../references/index/memory-network.md`


## Canonical Local Memory Source
The directory /home/hermesuser/.hermes/profiles/chief-orchestrator/workspace/memory/ is the authoritative local memory system. It contains structured memory domains (core, governance, actors, knowledge, runtime) and should be consulted as the primary source of truth for chief-orchestrator operations. Do not treat root workspace files or other directories as authoritative memory sources.

## Archival memory (mandatory)
Project-level detail, evidence trails, and recall-oriented logs live under each project AGENT_HOME/workspace/memory/knowledge/projects tree, not in this file.
Minimum cadence for writing archival files (in addition to role prompts):
- after substantive decisions or governance-relevant actions
- after evidence-producing steps
- before handoff, long idle, or context compaction
Keep this file to summaries and pointers (paths, dates, topics); duplicate long-form content only when the canonical pack requires it for upward summary.

## Related

- `../../../runtime/tasks/procedures/mem0-cloud-memory-policy.md`
