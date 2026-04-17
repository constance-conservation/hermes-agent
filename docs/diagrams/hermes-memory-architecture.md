# Hermes memory architecture

Conceptual view of how Hermes assembles context and tools around the LLM call path: **model routing** (for example OpenRouter) is the inference API path; **memory** is what feeds the prompt or is invoked as tools—local Cortical Lattice markdown, built-in `MEMORY.md` / `USER.md`, optional **Mem0** as the single pluggable memory provider, and **Zep / Letta / LangMem / LangSmith** as explicit tools in `tools/cloud_memory_tool.py`. Routing intent for backends is also described in workspace `constitution/memory-routing.md` (when present).

**Pre-rendered images** (committed in this folder): PNG for quick viewing; SVG for lossless zoom. See [README.md](README.md) to regenerate.

| Diagram | PNG | SVG |
|---------|-----|-----|
| A — Full turn | [hermes-memory-turn-flow.png](hermes-memory-turn-flow.png) | [hermes-memory-turn-flow.svg](hermes-memory-turn-flow.svg) |
| B — Cortical lattice | [hermes-memory-cortical-lattice.png](hermes-memory-cortical-lattice.png) | [hermes-memory-cortical-lattice.svg](hermes-memory-cortical-lattice.svg) |
| C — External products | [hermes-memory-external-products.png](hermes-memory-external-products.png) | [hermes-memory-external-products.svg](hermes-memory-external-products.svg) |

---

## Diagram A — One full turn (from message to memory side effects)

![Diagram A — one full turn from message to memory side effects](hermes-memory-turn-flow.png)

*Vector:* [hermes-memory-turn-flow.svg](hermes-memory-turn-flow.svg)

```mermaid
flowchart TB
  subgraph startTurn [Start of turn]
    UserMsg[User message]
    ChanCtx[Channel or chat context when applicable]
  end

  subgraph buildSystemPrompt [Building what the model sees as system context]
    HomeGov[Profile governance file hermes dot md]
    RootAnchors[Workspace memory root anchors AGENTS MEMORY USER ATTENTION INDEX]
    SoulFile[Persona and values SOUL]
    Extras[Optional extras from env STATE TOOLS SKILLS BOOTSTRAP]
    CorticalPack[Per turn lattice pack working pages plus memory routing hint]
    BuiltinProv[Always on builtin memory MEMORY dot md and USER dot md]
    Mem0Prefetch[Optional Mem0 prefetch from last query]
    Mem0Instructions[Optional Mem0 static instructions in system prompt]
    MergeSys[Assembled system prompt string]
    HomeGov --> MergeSys
    RootAnchors --> MergeSys
    SoulFile --> MergeSys
    Extras --> MergeSys
    CorticalPack --> MergeSys
    BuiltinProv --> MergeSys
    Mem0Prefetch --> MergeSys
    Mem0Instructions --> MergeSys
  end

  subgraph modelConfig [Model choice separate from memory]
    DefaultModel[Configured default such as OpenRouter free router]
    FallbackChain[Provider fallbacks and budget rules when a call fails]
    UpstreamApis[Upstream APIs OpenRouter OpenAI Anthropic Google etc]
  end

  subgraph inference [Inference call]
    ApiCall[Chat completion request]
    AssistantOut[Assistant text and tool calls]
  end

  subgraph toolSurface [Tools available during the turn]
    BuiltinTools[Builtin memory read and write tools]
    Mem0Tools[Mem0 search and profile tools when Mem0 is active]
    CloudSuite[Cloud memory tools Zep Letta LangMem LangSmith]
    OtherTools[All other Hermes tools filesystem web code etc]
  end

  subgraph afterTurn [After the assistant responds]
    SyncBuiltin[Sync turn into builtin store]
    SyncMem0[Sync turn into Mem0 when configured]
    QueuePrefetch[Queue prefetch text for next turn]
    WritebackLattice[Optional writeback into lattice layers and promotion]
  end

  MergeSys --> ApiCall
  UserMsg --> ApiCall
  ChanCtx --> ApiCall
  DefaultModel --> ApiCall
  FallbackChain --> ApiCall
  ApiCall --> UpstreamApis
  UpstreamApis --> AssistantOut
  AssistantOut --> SyncBuiltin
  AssistantOut --> SyncMem0
  AssistantOut --> QueuePrefetch
  AssistantOut --> WritebackLattice
  ApiCall -. exposes tool list .-> toolSurface
  AssistantOut -. may invoke .-> toolSurface
```

Standalone Mermaid source: [hermes-memory-turn-flow.mmd](hermes-memory-turn-flow.mmd)

---

## Diagram B — Cortical lattice local layers and how they relate

Folders of markdown under workspace memory, not separate servers.

![Diagram B — cortical lattice layers](hermes-memory-cortical-lattice.png)

*Vector:* [hermes-memory-cortical-lattice.svg](hermes-memory-cortical-lattice.svg)

```mermaid
flowchart LR
  subgraph pinned [Pinned rules and routing]
    Constitution[Constitution pinned rules and contracts]
    RoutingHints[Routing and activation hints]
  end

  subgraph liveState [Live and near term]
    WorkingMem[Working memory current focus blockers next steps]
    Prospective[Prospective memory commitments and open loops]
  end

  subgraph durableKnowledge [Durable knowledge]
    Semantic[Semantic graph facts domains references]
    Doctrine[Reflective doctrine policies and lessons]
    Social[Social and role memory persona org registers]
  end

  subgraph timeAndCases [History and reuse]
    Episodic[Episodic ledger what happened over time]
    Cases[Case memory reusable problem solution patterns]
    Skills[Skill atlas procedures and promoted skills]
  end

  subgraph riskAndOps [Risk and visibility]
    Hazard[Hazard memory failures and do not repeat]
    Observability[Observability audits traces registers]
    Bootstrap[Bootstrap init scripts and templates]
  end

  Constitution --> RoutingHints
  RoutingHints --> Semantic
  WorkingMem --> Episodic
  Episodic --> Cases
  Cases --> Skills
  Doctrine --> Semantic
  Hazard --> Cases
  Observability --> Episodic
```

Standalone Mermaid source: [hermes-memory-cortical-lattice.mmd](hermes-memory-cortical-lattice.mmd)

---

## Diagram C — External memory products versus local files

Who is a plugin, who is tools-only, and where routing intent is written.

![Diagram C — external memory products vs local files](hermes-memory-external-products.png)

*Vector:* [hermes-memory-external-products.svg](hermes-memory-external-products.svg)

```mermaid
flowchart TB
  subgraph localDisk [On disk under the profile]
    LatticeTree[Cortical lattice markdown tree]
    BuiltinFiles[Builtin MEMORY dot md and USER dot md]
  end

  subgraph singlePluginSlot [At most one optional external memory plugin]
    Mem0Plugin[Mem0 MemoryProvider prefetch sync Mem0 tools]
  end

  subgraph explicitTools [Separate tools not another plugin slot]
    ZepTool[Zep temporal graph memory]
    LettaTool[Letta pinned blocks]
    LangMemTool[LangMem extract and consolidate]
    LangSmithTool[LangSmith runs and traces]
  end

  subgraph routingDoc [Operator guidance inside the repo]
    MemoryRoutingDoc[constitution memory routing dot md who is for what]
  end

  LatticeTree --> MemoryRoutingDoc
  Mem0Plugin -. may overlap in purpose .- ZepTool
  MemoryRoutingDoc -. informs human and agent choices .- explicitTools
```

Standalone Mermaid source: [hermes-memory-external-products.mmd](hermes-memory-external-products.mmd)
