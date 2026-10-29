"""Public-starter repository layers and material-zone semantics."""

from __future__ import annotations


CANONICAL_LAYER_DIRS = (
    "00_identity",
    "01_knowledge",
    "02_decisions",
    "03_cognition",
    "04_people",
    "05_workflows",
    "06_active_context",
    "07_archive",
    "08_exports",
    "09_templates",
)
CANONICAL_MEMORY_DIRS = CANONICAL_LAYER_DIRS[:6]
CURRENT_STATE_DIRS = ("06_active_context",)
PERSONAL_VAULT_LAYER_DIRS = (*CANONICAL_MEMORY_DIRS, *CURRENT_STATE_DIRS)
