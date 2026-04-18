# Autoresearch Scope Mapping for Hermes Agent

## Repository Mapping
- Target system: `/home/hermesuser/hermes-agent` (Hermes Agent codebase)
- Research harness: `/home/hermesuser/.hermes/profiles/chief-orchestrator/skills/external-repos/autoresearch` (autoresearch runner)

## In-Scope Files

### Core Agent Files
- `run_agent.py` - Primary agent loop and instruction processing
- `cli.py` - CLI orchestrator and entry point
- `model_tools.py` - Tool orchestration and function calling
- `toolsets.py` - Toolset definitions and management
- `hermes_cli/` - CLI subcommands and configuration

### Gateway and Runtime
- `gateway/run.py` - Gateway execution and messaging
- `gateway/status.py` - Gateway status and watchdog
- `agent/prompt_builder.py` - System prompt assembly
- `agent/context_compressor.py` - Context compression logic
- `agent/prompt_caching.py` - Prompt caching mechanisms

### Delegation and Subagents
- `tools/delegate_tool.py` - Delegation to subagents
- `model_tools.py` - Subagent model routing
- `agent/skill_commands.py` - Skill and command delegation

### Memory and Context
- `hermes_state.py` - Session state and memory
- `agent/auxiliary_client.py` - Auxiliary LLM clients
- `agent/trajectory.py` - Trajectory saving and analysis

### Configuration and Routing
- `hermes_cli/config.py` - Configuration management
- `hermes_cli/models.py` - Model catalog and selection
- `hermes_cli/model_switch.py` - Model switching logic

### Evaluation and Testing
- `tests/` - Test suite for validation
- `batch_runner.py` - Batch evaluation runner
- `batch_runner.py` - Parallel batch processing

### Benchmarks
- `benchmarks/` - Benchmark suites and data
- `environments/` - Evaluation environments

### Excluded Files
- External dependencies and vendored code
- Documentation and README files
- Development and build scripts
- Testing fixtures unrelated to core behavior