"""Platform adapters for the ResearchOS kernel: read the Markdown research graph (``markdown_repo``),
plan the admission writes into it (``writeback``), stage and roll back writes (``filesystem_staging``),
keep the run-state ledger (``run_state``), build the bounded context pack and its receipt
(``context_pack``) and dispatch a bounded run to a local runner (``dispatch``). The launch
boundary that ``dispatch`` and the Dashboard runner share lives here too: the provider registry,
runtime configuration and profiles (``provider_registry``, ``provider_config``, ``runtime_profile``),
the execution port and its two local CLI adapters (``provider_adapter``, ``claude_code_adapter``),
model discovery (``model_catalog``), the subprocess runner (``command_runner``), CLI permission
profiles (``runner_permissions``), the result parser (``work_session_result``) and machine
authorization (``policy_gateway`` over ``runner_authority``).

Shared by the private vault and the public starter. Stdlib and the kernel only; nothing here
imports ``researchos_server`` (validate_agent_architecture.py enforces the direction).
"""
