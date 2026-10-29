from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.runtime_profile import (  # noqa: E402
    ADAPTER_FAMILIES,
    PROFILE_KEYS,
    REASONING_VALUES,
    RUNTIME_PROFILE_SCHEMA_ID,
    RuntimeProfileError,
    normalize_runtime_profile,
    normalize_runtime_profile_projection,
    project_runtime_profile,
    project_selected_runtime_profile,
    resolve_runtime_profile_route,
    runtime_profiles_from_config,
    select_runtime_profile,
)


def local_profile() -> dict[str, object]:
    return {
        "schema_id": "researchos-runtime-profile-v1",
        "profile_id": "codex_local",
        "adapter_family": "local_codex",
        "provider": "codex",
        "enabled": True,
        "allowed_scopes": ["private", "personal_vault"],
        "model": "auto",
        "allowed_models": ["auto", "gpt-5.6-sol"],
        "reasoning_effort": "high",
        "allowed_reasoning_efforts": ["auto", "medium", "high"],
        "endpoint_ref": "local:codex-cli",
        "credential_ref": {"kind": "none", "name": ""},
        "capabilities": {
            "result_modes": ["answer", "artifact", "writeback"],
            "streaming": False,
            "cancel": "unsupported",
            "tool_calling": False,
            "agent_loop": False,
        },
        "timeout_seconds": 900,
        "cost_policy": {"mode": "local_unmetered", "budget_ref": ""},
        "fallback_policy": {"mode": "none"},
    }


def claude_code_profile() -> dict[str, object]:
    value = local_profile()
    value.update({
        "profile_id": "claude_code_answer",
        "adapter_family": "local_claude_code",
        "provider": "claude_code",
        "enabled": False,
        "allowed_models": ["auto"],
        "reasoning_effort": "auto",
        "allowed_reasoning_efforts": ["auto"],
        "endpoint_ref": "local:claude-code-cli",
        "capabilities": {
            "result_modes": ["answer"], "streaming": False, "cancel": "unsupported",
            "tool_calling": False, "agent_loop": False,
        },
    })
    return value


class RuntimeProfileTest(unittest.TestCase):
    def test_strict_profile_preserves_model_and_reasoning_without_authority(self) -> None:
        profile = normalize_runtime_profile(local_profile())
        self.assertEqual(profile["model"], "auto")
        self.assertEqual(profile["reasoning_effort"], "high")
        self.assertEqual(profile["capabilities"]["result_modes"], ["answer", "artifact", "writeback"])
        self.assertEqual(profile["capabilities"]["cancel"], "unsupported")
        self.assertFalse({"authority", "authorization", "egress"} & set(profile))

    def test_unknown_model_reasoning_provider_and_family_fail_closed(self) -> None:
        attacks = []
        model = local_profile(); model["model"] = "unlisted"; attacks.append(model)
        reasoning = local_profile(); reasoning["reasoning_effort"] = "root"; attacks.append(reasoning)
        provider = local_profile(); provider["provider"] = "unknown"; attacks.append(provider)
        mismatch = local_profile(); mismatch["adapter_family"] = "anthropic"; attacks.append(mismatch)
        for attack in attacks:
            with self.subTest(attack=attack):
                with self.assertRaises(RuntimeProfileError):
                    normalize_runtime_profile(attack)

    def test_raw_endpoint_secret_credential_and_fallback_fail_closed(self) -> None:
        raw_url = claude_code_profile(); raw_url["endpoint_ref"] = "https://api.example.invalid/v1"
        raw_key = claude_code_profile(); raw_key["credential_ref"] = {"kind": "env", "name": "sk-secret"}
        fallback = claude_code_profile(); fallback["fallback_policy"] = {"mode": "automatic"}
        public_scope = claude_code_profile(); public_scope["allowed_scopes"] = ["public_starter"]
        for attack in (raw_url, raw_key, fallback, public_scope):
            with self.assertRaises(RuntimeProfileError):
                normalize_runtime_profile(attack)

    def test_claude_code_is_answer_only_without_tools_agent_loop_or_cancel(self) -> None:
        for field, value in (
            ("result_modes", ["answer", "artifact"]), ("streaming", True),
            ("cancel", "best_effort"), ("tool_calling", True), ("agent_loop", True),
        ):
            attack = claude_code_profile()
            attack["capabilities"] = copy.deepcopy(attack["capabilities"])
            attack["capabilities"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(RuntimeProfileError):
                    normalize_runtime_profile(attack)

    def test_local_profile_cannot_claim_unimplemented_streaming_tools_or_cancel(self) -> None:
        for field, value in (
            ("streaming", True), ("cancel", "supported"),
            ("tool_calling", True), ("agent_loop", True),
        ):
            attack = local_profile()
            attack["capabilities"] = copy.deepcopy(attack["capabilities"])
            attack["capabilities"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(RuntimeProfileError):
                    normalize_runtime_profile(attack)

    def test_profiles_derive_from_the_providers_block_without_mutation(self) -> None:
        config = json.loads((ROOT / "config/researchos.runtime.example.json").read_text(encoding="utf-8"))
        before = copy.deepcopy(config)
        profiles = runtime_profiles_from_config(config)
        self.assertEqual(set(profiles), {"codex", "claude_code"})
        self.assertEqual(profiles["codex"]["adapter_family"], "local_codex")
        self.assertEqual(profiles["claude_code"]["credential_ref"], {"kind": "none", "name": ""})
        self.assertEqual(profiles["claude_code"]["capabilities"]["result_modes"], ["answer"])
        self.assertEqual(config, before)

        malformed = copy.deepcopy(config)
        malformed["providers"]["claude_code"]["enabled"] = "false"
        with self.assertRaisesRegex(RuntimeProfileError, "runtime_profile_enabled_invalid"):
            runtime_profiles_from_config(malformed)

    def test_unknown_disabled_and_public_selection_fail_closed(self) -> None:
        config = json.loads((ROOT / "config/researchos.runtime.example.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(RuntimeProfileError, "runtime_profile_unknown"):
            select_runtime_profile(config, profile_id="missing", runtime_scope="private")
        with self.assertRaisesRegex(RuntimeProfileError, "runtime_profile_disabled"):
            select_runtime_profile(config, profile_id="claude_code", runtime_scope="private")
        with self.assertRaisesRegex(RuntimeProfileError, "public_starter_copy_only"):
            select_runtime_profile(config, profile_id="codex", runtime_scope="public_starter")

    def test_route_resolves_explicit_profile_and_preserves_legacy_provider_lane(self) -> None:
        config = json.loads((ROOT / "config/researchos.runtime.example.json").read_text(encoding="utf-8"))
        self.assertEqual(resolve_runtime_profile_route(config, {}, runtime_scope="private"), ("codex", "codex"))
        self.assertEqual(
            resolve_runtime_profile_route(config, {"provider": "not-registered"}, runtime_scope="private"),
            ("not-registered", "not-registered"),
        )
        with self.assertRaisesRegex(RuntimeProfileError, "runtime_profile_disabled"):
            resolve_runtime_profile_route(config, {"runtime_profile_id": "claude_code"}, runtime_scope="private")

    def test_safe_projection_never_contains_endpoint_or_credential_reference(self) -> None:
        private = project_runtime_profile(claude_code_profile(), runtime_scope="private")
        public = project_runtime_profile(claude_code_profile(), runtime_scope="public_starter")
        for projection in (private, public):
            serialized = json.dumps(projection, sort_keys=True)
            self.assertNotIn("endpoint_ref", serialized)
            self.assertNotIn("credential_ref", serialized)
            self.assertNotIn("local:claude-code-cli", serialized)
        self.assertEqual(public["status"], "copy_only")
        self.assertEqual(public["execution_scope"], "none")
        self.assertEqual(private["status"], "disabled")
        self.assertEqual(private["execution_scope"], "none")

    def test_selected_projection_is_read_only_and_reports_verification_without_dispatch(self) -> None:
        config = {
            "schema_id": "researchos-runtime-config-v1", "default_runtime_profile": "codex",
            "providers": {"codex": {"type": "local_codex", "default_model": "auto", "enabled": True}},
        }
        before_probe = project_selected_runtime_profile(config, runtime_scope="private")
        after_probe = project_selected_runtime_profile(config, runtime_scope="private", execution_available=True)
        self.assertEqual("local_probe_required", before_probe["verification_state"])
        self.assertEqual("local_probe_passed", after_probe["verification_state"])
        self.assertEqual("candidate_off", after_probe["selector_state"])
        self.assertEqual("copy_only", after_probe["configuration_handoff"]["mode"])
        self.assertEqual(
            "python3 scripts/runtime_profile_cli.py show --profile codex",
            after_probe["configuration_handoff"]["command"],
        )
        self.assertNotIn("dispatch", json.dumps(after_probe))

    def test_claude_code_projection_is_answer_only(self) -> None:
        profile = claude_code_profile(); profile["enabled"] = True
        projected = project_runtime_profile(profile, runtime_scope="personal_vault", execution_available=True)
        self.assertEqual("answer_only", projected["execution_scope"])
        self.assertEqual("local_probe_passed", projected["verification_state"])
        self.assertEqual(["answer"], projected["result_modes"])

    def test_invalid_selection_fails_closed_to_validation_handoff(self) -> None:
        invalid = project_selected_runtime_profile(
            {"schema_id": "researchos-runtime-config-v1", "default_provider": "missing", "providers": {}},
            runtime_scope="private",
        )
        self.assertEqual("invalid", invalid["status"])
        self.assertEqual("none", invalid["execution_scope"])
        self.assertEqual("configuration_invalid", invalid["verification_state"])
        self.assertEqual("python3 scripts/runtime_profile_cli.py validate", invalid["configuration_handoff"]["command"])

    def test_projection_normalizer_rejects_secret_extra_key_and_forged_live_claim(self) -> None:
        safe = project_runtime_profile(local_profile(), runtime_scope="private")
        attacks = []
        secret = copy.deepcopy(safe); secret["credential_ref"] = {"name": "SECRET"}; attacks.append(secret)
        forged = copy.deepcopy(safe); forged["verification_state"] = "not_live_verified"; attacks.append(forged)
        command = copy.deepcopy(safe); command["configuration_handoff"]["command"] = "curl https://evil"; attacks.append(command)
        mismatched = copy.deepcopy(safe); mismatched["profile_id"] = "other"; attacks.append(mismatched)
        for attack in attacks:
            with self.assertRaises(RuntimeProfileError):
                normalize_runtime_profile_projection(attack)

    def test_schema_has_exact_required_fields_and_no_secret_or_authority_field(self) -> None:
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-runtime-profile-v1.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        serialized = json.dumps(schema, sort_keys=True)
        self.assertNotIn("api_key", serialized)
        self.assertNotIn('"authority"', serialized)
        projection = json.loads((ROOT / "09_templates/data_contracts/researchos-runtime-profile-projection-v1.schema.json").read_text())
        self.assertFalse(projection["additionalProperties"])
        self.assertEqual(set(projection["required"]), set(projection["properties"]))
        projected_schema = json.dumps(projection, sort_keys=True)
        for forbidden in ("endpoint_ref", "credential_ref", "api_key", "budget_ref", "source_ref"):
            self.assertNotIn(forbidden, projected_schema)


    def test_schema_vocabulary_matches_the_owner_and_example_profiles_project_safely(self) -> None:
        schema = json.loads((ROOT / "09_templates/data_contracts/researchos-runtime-profile-v1.schema.json").read_text())
        properties = schema["properties"]
        self.assertEqual(PROFILE_KEYS, set(properties))
        self.assertEqual(PROFILE_KEYS, set(schema["required"]))
        self.assertEqual(RUNTIME_PROFILE_SCHEMA_ID, properties["schema_id"]["const"])
        self.assertEqual(tuple(ADAPTER_FAMILIES), tuple(properties["adapter_family"]["enum"]))
        self.assertEqual(set(REASONING_VALUES), set(properties["reasoning_effort"]["enum"]))
        config = json.loads((ROOT / "config/researchos.runtime.example.json").read_text(encoding="utf-8"))
        profiles = runtime_profiles_from_config(config)
        for profile in profiles.values():
            for scope in ("private", "public_starter"):
                with self.subTest(profile=profile["profile_id"], scope=scope):
                    self.assertFalse({"endpoint_ref", "credential_ref"} & set(project_runtime_profile(profile, runtime_scope=scope)))
        self.assertEqual("copy_only", project_runtime_profile(profiles["codex"], runtime_scope="public_starter")["status"])


if __name__ == "__main__":
    unittest.main()
