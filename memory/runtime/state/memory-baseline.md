# Memory Baseline

- Mem0 usage and governance: see Mem0 entry `MEM0_EXTENDED_GUIDE` (critical: no deletion without approval).
- Runtime context: see Mem0 entry `PROJECT_RUNTIME_CONTEXT`.

Primary memory strategy: use Mem0 as the primary source of truth for user preferences and agent knowledge. Check `mem0_search` and `mem0_profile` first. Keep local memory only for critical, bite-sized, prompt-essential anchors.

Operational core: phased activation session data (1-20) is stored on Mem0 and constitutes the binding operational policy for the `agentic-company` runtime.

## Related

- `memory-integration-override.md`
- `../tasks/procedures/mem0-cloud-memory-policy.md`
- `../../runtime/logs/mem0-integration.md`

## Canonical Local Memory Source
The directory /home/hermesuser/.hermes/profiles/chief-orchestrator/workspace/memory/ is the authoritative local memory system. It contains structured memory domains (core, governance, actors, knowledge, runtime) and should be consulted as the primary source of truth for chief-orchestrator operations. Do not treat root workspace files or other directories as authoritative memory sources.

## Archival memory (mandatory)
Project-level detail, evidence trails, and recall-oriented logs live under each project AGENT_HOME/workspace/memory/knowledge/projects tree, not in this file.
Minimum cadence for writing archival files (in addition to role prompts):
- after substantive decisions or governance-relevant actions
- after evidence-producing steps
- before handoff, long idle, or context compaction
Keep this file to summaries and pointers (paths, dates, topics); duplicate long-form content only when the canonical pack requires it for upward summary.
