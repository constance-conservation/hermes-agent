# Hermes engineering standards (draft)

This page is the **high-level agreement** for how we work and what Hermes sits on. Details live in the main repo docs and in code—this is not a catalogue of settings.

---

**GitHub.** We work in the **hermes-agent** repository. New repos we add should use **short, lowercase, hyphenated** names. Branches follow **fix**, **feat**, **docs**, **test**, or **refactor**, then a **kebab-case** slug. Commits use **conventional** style: a type, an optional scope, and a clear message. Pull requests should do **one thing**, explain **why** and **how to verify**, and call out anything **security-related**. We **never** commit API keys or `.env` files; those belong under your **Hermes home** directory (per-profile when you use profiles). Bugs and tasks use **Issues**; broader design questions use **Discussions**.

**Runtime.** Hermes is a **Python 3.11+** project: a **virtualenv** in the checkout, install in editable mode, **pytest** for tests. At a glance: an **agent** and **tools**, a **terminal CLI**, and an optional **gateway** that connects to chat apps. State and config are **per profile**—treat the Hermes home as the source of truth, not paths baked into code. Optional pieces include **Node** for some tooling, extra Python packages for messaging, memory providers, sandboxes, and the like—install only what you need.

**Platforms.** We use **Vercel** in practice mainly through the **AI Gateway** pattern for routing models, and the wider ecosystem shows up in skills and docs. Day-to-day ops also distinguish an **operator** workstation and a **droplet** server; SSH and deployment are documented elsewhere. Looking ahead, we may standardize on **Supabase** for app data, **Sentry** for errors in long-running services, and **Doppler** (or similar) for **centralized secrets**—none of those are requirements inside Hermes core today.

**Integrations.** Hermes talks to **LLM providers**, **research and browser tools**, **memory services** (cloud and optional local pieces), **team chat platforms**, and **related repos** such as Paperclip and Autoresearch when you wire them in. All of that is configured **outside git**; the exhaustive list of names and meanings is maintained in the **environment-variable reference** in the docs tree—use that when you need specifics.

**Getting going.** Put Python and a venv in place, install the package for development, add at least one model key under your Hermes home, and run the test suite before you merge meaningful changes. If you run the **gateway**, use **one** live process per bot identity. If you use **SSH-heavy** operator and droplet setups, follow the dedicated deployment notes in the repo.

---

## Appendix — machine-readable reference (AI coding assistants)

The block below is **structured data** for tools and assistants. It duplicates policy and inventory detail from `CONTRIBUTING.md`, `AGENTS.md`, `pyproject.toml`, `hermes_cli/config.py`, and `website/docs/reference/environment-variables.md`. **Do not store secret values** in this file; use env key names only for discovery.

```yaml
hermes_engineering_standards:
  schema_version: "1.0"
  intended_audience:
    - ai_coding_assistant
    - ci_automation
  scope_note: >-
    Human-readable policy is the prose section above this fence.
    This YAML is the canonical structured complement for parsing.

  github:
    primary_repository: hermes-agent
    new_repository_naming: lowercase_hyphenated
    branch_prefixes: [fix, feat, docs, test, refactor]
    branch_slug_style: kebab-case
    commit_style: conventional_commits
    commit_types: [fix, feat, docs, test, refactor, chore]
    commit_scope_examples: [cli, gateway, tools, skills, agent, install, whatsapp, security]
    pull_request_rules:
      - one_logical_change_per_pr
      - describe_what_why_how_to_test
      - note_security_sensitive_changes
      - run_tests_before_merge
    secrets_policy:
      never_commit: [api_keys, tokens, dot_env_files]
      profile_secrets_path_pattern: "~/.hermes/profiles/<profile>/.env"
      root_env_path_pattern: "~/.hermes/.env"
    discussion_venues:
      bugs_and_tasks: github_issues
      design_and_architecture: github_discussions
    related_upstream_repos_examples:
      paperclip: cc-org-au/paperclip
      autoresearch: cc-org-au/autoresearch

  runtime:
    python_minimum: "3.11"
    install_mode: editable
    virtualenv: venv_in_repo
    test_runner: pytest
    optional_node_minimum: "18"
    hermes_home_rule: profile_scoped; use get_hermes_home() in code

  python_core_dependencies:
    # From pyproject.toml [project] dependencies — names only
    - openai
    - anthropic
    - python-dotenv
    - fire
    - httpx
    - rich
    - tenacity
    - pyyaml
    - requests
    - jinja2
    - pydantic
    - prompt_toolkit
    - exa-py
    - firecrawl-py
    - parallel-web
    - fal-client
    - edge-tts
    - PyJWT

  pip_optional_extras:
    modal: [modal]
    daytona: [daytona]
    dev: [debugpy, pytest, pytest-asyncio, pytest-xdist, mcp]
    messaging: [python-telegram-bot, discord.py, aiohttp, slack-bolt, slack-sdk]
    cron: [croniter]
    slack: [slack-bolt, slack-sdk]
    matrix: [matrix-nio]
    cli: [simple-term-menu]
    tts-premium: [elevenlabs]
    voice: [faster-whisper, sounddevice, numpy]
    pty: [ptyprocess, pywinpty]
    honcho: [honcho-ai]
    mcp: [mcp]
    memory_services: [langsmith, langmem, langgraph, zep-cloud, letta-client]
    homeassistant: [aiohttp]
    sms: [aiohttp]
    acp: [agent-client-protocol]
    dingtalk: [dingtalk-stream]
    feishu: [lark-oapi]
    rl:
      - atroposlib@git+https://github.com/NousResearch/atropos.git
      - tinker@git+https://github.com/thinking-machines-lab/tinker.git
      - fastapi
      - uvicorn
      - wandb
    yc-bench: [yc-bench@git+https://github.com/collinear-ai/yc-bench.git]

  node_packages_root:
    description: package.json at repo root
    dependencies: [agent-browser, "@askjo/camoufox-browser"]
    engines_node: ">=18.0.0"

  memory_provider_plugins:
    # plugins/memory/* — one active external provider at a time
    - mem0
    - honcho
    - openviking
    - hindsight
    - holographic
    - retaindb
    - byterover

  memory_tools_optional_cloud:
    install_extra: memory_services
    components:
      - name: langmem
        storage_note: local_sqlite_under_hermes_home
      - name: zep_cloud
      - name: letta
      - name: langsmith
    host_scoped_env_suffixes: [OPERATOR, DROPLET]
    env_keys_for_scoping:
      - HERMES_MEMORY_KEY_SUFFIX
      - LANGSMITH_API_KEY
      - LANGSMITH_API_KEY_OPERATOR
      - LANGSMITH_API_KEY_DROPLET
      - ZEP_API_KEY
      - ZEP_API_KEY_OPERATOR
      - ZEP_API_KEY_DROPLET
      - LETTA_API_KEY
      - LETTA_API_KEY_OPERATOR
      - LETTA_API_KEY_DROPLET

  mem0_env_and_config:
    env_keys:
      - MEM0_API_KEY
      - MEM0_USER_ID
      - MEM0_AGENT_ID
      - MEM0_ORG_ID
      - MEM0_PROJECT_ID
    config_file_under_hermes_home: mem0.json

  integration_repo_paths:
    env_keys:
      - HERMES_PAPERCLIP_REPO
      - HERMES_AUTORESEARCH_REPO

  gateway_platform_adapters:
    # gateway/platforms/*.py
    - telegram
    - slack
    - discord
    - whatsapp
    - email
    - signal
    - mattermost
    - matrix
    - homeassistant
    - sms
    - webhook
    - dingtalk
    - feishu
    - wecom
    - api_server

  terminal_backends:
    # tools/environments/
    - local
    - docker
    - singularity
    - modal
    - daytona
    - ssh
    - persistent_shell

  platforms:
    in_use_documented:
      - name: vercel
        usage: [ai_gateway, skills_ecosystem_references]
      - name: github
        usage: [source, issues, actions, skills_hub_tokens]
    deployment_topology:
      - operator_workstation_ssh
      - droplet_vps_ssh
      - tailscale_private_mesh
      - launchd_or_systemd_watchdogs
    roadmap_not_in_core_code:
      - supabase
      - sentry
      - doppler

  saas_llm_and_routing_examples:
    # Configure via env; see website/docs/reference/environment-variables.md
    - openrouter
    - openai
    - anthropic
    - google_gemini
    - z_ai_glm
    - kimi_moonshot
    - minimax
    - deepseek
    - alibaba_dashscope
    - opencode_zen
    - opencode_go
    - huggingface_inference_providers
    - vercel_ai_gateway
    - nous_portal

  saas_tools_examples:
    - exa
    - parallel
    - firecrawl
    - tavily
    - browserbase
    - browser_use
    - fal_ai
    - groq
    - elevenlabs
    - honcho
    - tinker
    - weights_and_biases
    - daytona
    - modal

  metadata_services:
    - models.dev

  environment_variable_names_sample_grouped:
    # Non-exhaustive; full set in hermes_cli/config.py OPTIONAL_ENV_VARS + _EXTRA_ENV_KEYS
    llm_and_providers:
      - OPENROUTER_API_KEY
      - OPENAI_API_KEY
      - OPENAI_API_KEY_DROPLET
      - OPENAI_BASE_URL
      - ANTHROPIC_API_KEY
      - ANTHROPIC_TOKEN
      - GEMINI_API_KEY
      - GOOGLE_API_KEY
      - GEMINI_BASE_URL
      - GLM_API_KEY
      - ZAI_API_KEY
      - Z_AI_API_KEY
      - GLM_BASE_URL
      - KIMI_API_KEY
      - KIMI_BASE_URL
      - MINIMAX_API_KEY
      - MINIMAX_BASE_URL
      - MINIMAX_CN_API_KEY
      - MINIMAX_CN_BASE_URL
      - DEEPSEEK_API_KEY
      - DEEPSEEK_BASE_URL
      - DASHSCOPE_API_KEY
      - DASHSCOPE_BASE_URL
      - OPENCODE_ZEN_API_KEY
      - OPENCODE_ZEN_BASE_URL
      - OPENCODE_GO_API_KEY
      - OPENCODE_GO_BASE_URL
      - HF_TOKEN
      - HUGGINGFACE_API_KEY
      - HF_BASE_URL
      - AI_GATEWAY_API_KEY
      - AI_GATEWAY_BASE_URL
      - NOUS_BASE_URL
    tools:
      - EXA_API_KEY
      - PARALLEL_API_KEY
      - FIRECRAWL_API_KEY
      - FIRECRAWL_API_URL
      - TAVILY_API_KEY
      - BROWSERBASE_API_KEY
      - BROWSERBASE_PROJECT_ID
      - BROWSER_USE_API_KEY
      - CAMOFOX_URL
      - FAL_KEY
      - GITHUB_TOKEN
      - HONCHO_API_KEY
      - HONCHO_BASE_URL
    messaging:
      - TELEGRAM_BOT_TOKEN
      - SLACK_BOT_TOKEN
      - SLACK_APP_TOKEN
      - DISCORD_BOT_TOKEN
      - WHATSAPP_ENABLED
    hermes_operational:
      - HERMES_GATEWAY_LOCK_INSTANCE
      - HERMES_CLI_INSTANCE_LABEL
      - HERMES_TURN_DONE_NOTIFY_URL
      - HERMES_LIST_SESSIONS_ALL_SOURCES
      - HERMES_OPENAI_PRIMARY_MODE
    operator_ssh:
      - MACMINI_SSH_USER
      - MACMINI_SSH_HOST
      - MACMINI_SSH_PORT
      - MACMINI_SSH_LAN_IP
      - SSH_IP_OPERATOR

  extra_env_keys_partial_from_config_py:
    # _EXTRA_ENV_KEYS frozenset — partial list for discovery
    - OPENAI_API_KEY
    - OPENAI_API_KEY_DROPLET
    - OPENAI_BASE_URL
    - ANTHROPIC_API_KEY
    - ANTHROPIC_TOKEN
    - AUXILIARY_VISION_MODEL
    - DISCORD_HOME_CHANNEL
    - TELEGRAM_HOME_CHANNEL
    - SIGNAL_ACCOUNT
    - SIGNAL_HTTP_URL
    - DINGTALK_CLIENT_ID
    - DINGTALK_CLIENT_SECRET
    - FEISHU_APP_ID
    - FEISHU_APP_SECRET
    - FEISHU_ENCRYPT_KEY
    - FEISHU_VERIFICATION_TOKEN
    - WECOM_BOT_ID
    - WECOM_SECRET
    - TERMINAL_ENV
    - TERMINAL_SSH_KEY
    - TERMINAL_SSH_PORT
    - WHATSAPP_MODE
    - WHATSAPP_ENABLED
    - MATRIX_PASSWORD
    - MATRIX_ENCRYPTION

  canonical_reference_paths_in_repo:
    contributing: CONTRIBUTING.md
    agents_guide: AGENTS.md
    pyproject: pyproject.toml
    optional_env_vars_source: hermes_cli/config.py
    env_example: .env.example
    env_reference_doc: website/docs/reference/environment-variables.md

  operational_checklist_machine:
    local_dev:
      - python_3_11_plus
      - editable_install_with_dev_extra
      - hermes_home_config_and_env
      - at_least_one_llm_key
      - pytest_before_merge
    gateway:
      - messaging_extra_installed
      - one_live_gateway_per_bot_token
      - HERMES_GATEWAY_LOCK_INSTANCE_if_shared_home

  open_decisions:
    - default_llm_path_per_environment
    - production_profile_naming_chief_orchestrator_vs_droplet_variant
    - supabase_adoption_scope
    - sentry_first_scope_gateway_vs_cli
```
