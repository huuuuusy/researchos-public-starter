# Public Data Helper Boundary

## Agent Summary

The public starter keeps a deliberately small supported boundary here: `maintenance_pipeline.py` owns local auto-update sequencing; `task_extensions.py` owns validated declarative routes; `plugin_lifecycle.py` owns reversible installation of bundled examples; `conversation_contract.py` owns result and writeback authority; `repository_layout.py` owns personal-vault layers; frontend/style manifests remain read-only validation inputs.

Use these public entrypoints instead:

- `scripts/build_public_starter_data.py` for demo and personal-vault projections;
- `scripts/start_researchos.py` for local runtime;
- `scripts/manage_plugins.py` for bundled example install, disable, enable, and uninstall;
- `scripts/validate_public_safety.py` for release safety;
- `scripts/check_all_links.py` and the tests under `evals/` for regression checks.

Put new behavior behind a documented entrypoint and an explicit owner module, then add a regression test. `scripts/validate_agent_architecture.py` fails if an unsupported data helper is reintroduced.
