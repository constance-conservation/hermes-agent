# Memory Baseline

- Mem0 usage and governance: see Mem0 entry `MEM0_EXTENDED_GUIDE` (critical: no deletion without approval).
- Runtime context: see Mem0 entry `PROJECT_RUNTIME_CONTEXT`.

Primary memory strategy: use Mem0 as the primary source of truth for user preferences and agent knowledge. Check `mem0_search` and `mem0_profile` first. Keep local memory only for critical, bite-sized, prompt-essential anchors.

Operational core: phased activation session data (1-20) is stored on Mem0 and constitutes the binding operational policy for the `agentic-company` runtime.

## Related

- `memory-integration-override.md`
- `../tasks/procedures/mem0-cloud-memory-policy.md`
- `../../runtime/logs/mem0-integration.md`