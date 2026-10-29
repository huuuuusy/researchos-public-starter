#!/usr/bin/env python3
"""Build, validate, and inspect ResearchOS semantic receipts without Dashboard or a server."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

from researchos_kernel.atomic_files import atomic_write_bytes
from researchos_kernel.ledger import digest
from researchos_kernel.context_receipt import (
    CONTEXT_RECEIPT_SCHEMA_ID,
    build_requested_context_receipt,
    normalize_context_receipt,
    source_identity,
)
from researchos_kernel.handoff_receipt import (
    HANDOFF_RECEIPT_SCHEMA_ID,
    build_handoff_receipt,
    normalize_handoff_receipt,
)


MAX_INPUT_BYTES = 1_048_576


class ReceiptCliError(ValueError):
    pass


def _relative_path(root: Path, value: str, *, must_exist: bool) -> Path:
    lexical = PurePosixPath(value)
    if not value or lexical.is_absolute() or ".." in lexical.parts:
        raise ReceiptCliError("path_not_allowed")
    target = root.joinpath(*lexical.parts)
    cursor = root
    for part in lexical.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ReceiptCliError("symlink_not_allowed")
    try:
        target.resolve(strict=must_exist).relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        raise ReceiptCliError("path_not_allowed") from exc
    return target


def _read_json(root: Path, value: str) -> dict[str, object]:
    if value == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        path = _relative_path(root, value, must_exist=True)
        if not path.is_file():
            raise ReceiptCliError("input_not_file")
        raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ReceiptCliError("input_too_large")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptCliError("invalid_json") from exc
    if not isinstance(parsed, dict):
        raise ReceiptCliError("invalid_json_object")
    return parsed


def _write_json(root: Path, value: str, payload: object) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if value == "-":
        sys.stdout.buffer.write(encoded)
        return
    target = _relative_path(root, value, must_exist=False)
    if target.exists():
        raise ReceiptCliError("output_exists")
    parent = target.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ReceiptCliError("output_parent_not_allowed")
    atomic_write_bytes(target, encoded)


def _context_from_spec(spec: dict[str, object]) -> dict[str, object]:
    required = {
        "task_id", "run_id", "runtime_scope", "producer_kind", "producer_surface", "source_refs",
    }
    if set(spec) != required:
        raise ReceiptCliError("context_spec_invalid")
    return build_requested_context_receipt(
        task_id=str(spec["task_id"]), run_id=str(spec["run_id"]), runtime_scope=str(spec["runtime_scope"]),
        producer_kind=str(spec["producer_kind"]), producer_surface=str(spec["producer_surface"]),
        source_refs=spec["source_refs"],
    )


def _statement(value: object, *, field: str, states: set[str], evidence_ref: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"state", "text"}:
        raise ReceiptCliError(f"{field}_invalid")
    state = str(value["state"])
    text = str(value["text"])
    if state not in states or state == "unknown" and text:
        raise ReceiptCliError(f"{field}_invalid")
    return {"state": state, "text": text, "evidence_ref": evidence_ref if state != "unknown" else ""}


def _handoff_from_spec(root: Path, spec: dict[str, object]) -> dict[str, object]:
    required = {
        "context_receipt", "source", "source_path", "last_judgment", "open_boundary",
        "next_safe_action", "forbidden_actions", "target_client",
    }
    if set(spec) != required or not isinstance(spec["source"], dict) or set(spec["source"]) != {"kind", "ref"}:
        raise ReceiptCliError("handoff_spec_invalid")
    source = spec["source"]
    kind, ref = str(source["kind"]), str(source["ref"])
    source_id = source_identity(kind, ref)
    context = normalize_context_receipt(spec["context_receipt"], trusted_producer=True)
    if source_id not in {item["source_id"] for item in context["sources"]}:
        raise ReceiptCliError("handoff_receipt_source_not_in_context")
    if kind != "file":
        raise ReceiptCliError("source_kind_requires_trusted_mapping")
    source_path = _relative_path(root, str(spec["source_path"]), must_exist=True)
    identity_path = _relative_path(root, ref, must_exist=True)
    if identity_path.resolve() != source_path.resolve():
        raise ReceiptCliError("source_identity_path_mismatch")
    if not source_path.is_file():
        raise ReceiptCliError("source_not_file")
    source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    spec_evidence = f"local_input:{digest({key: value for key, value in spec.items() if key != 'context_receipt'})}"
    forbidden = spec["forbidden_actions"]
    if not isinstance(forbidden, dict) or set(forbidden) != {"state", "items"}:
        raise ReceiptCliError("forbidden_actions_invalid")
    forbidden_state = str(forbidden["state"])
    forbidden_items = forbidden["items"]
    if forbidden_state not in {"unknown", "recorded"} or not isinstance(forbidden_items, list):
        raise ReceiptCliError("forbidden_actions_invalid")
    if forbidden_state == "unknown" and forbidden_items:
        raise ReceiptCliError("forbidden_actions_invalid")
    target = spec["target_client"]
    if not isinstance(target, dict) or set(target) != {"kind", "surface"}:
        raise ReceiptCliError("target_client_invalid")
    last_judgment = _statement(
        spec["last_judgment"], field="last_judgment", states={"unknown", "candidate"}, evidence_ref=spec_evidence,
    )
    return build_handoff_receipt(
        context_receipt=spec["context_receipt"], source_id=source_id, revision_scheme="sha256",
        revision_value=source_digest, revision_evidence_ref=f"file_sha256:{source_digest}",
        producer_kind="researchos_cli", producer_surface="terminal", evidence_class="tool_recorded",
        last_judgment=last_judgment,
        open_boundary=_statement(
            spec["open_boundary"], field="open_boundary", states={"unknown", "recorded"}, evidence_ref=spec_evidence,
        ),
        next_safe_action=_statement(
            spec["next_safe_action"], field="next_safe_action", states={"unknown", "recommended"}, evidence_ref=spec_evidence,
        ),
        forbidden_actions={
            "state": forbidden_state, "items": [str(item) for item in forbidden_items],
            "evidence_ref": spec_evidence if forbidden_state == "recorded" else "",
        },
        target_client={"kind": str(target["kind"]), "surface": str(target["surface"])},
    )


def _normalize(value: dict[str, object]) -> dict[str, object]:
    schema_id = value.get("schema_id")
    if schema_id == CONTEXT_RECEIPT_SCHEMA_ID:
        return normalize_context_receipt(value, trusted_producer=True)
    if schema_id == HANDOFF_RECEIPT_SCHEMA_ID:
        return normalize_handoff_receipt(value, trusted_producer=True)
    raise ReceiptCliError("unsupported_receipt")


def _summary(receipt: dict[str, object]) -> dict[str, object]:
    schema_id = str(receipt["schema_id"])
    identity = receipt.get("receipt_id") if schema_id == CONTEXT_RECEIPT_SCHEMA_ID else receipt.get("handoff_id")
    summary: dict[str, object] = {
        "ok": True, "schema_id": schema_id, "id": identity,
        "task_id": receipt["task_id"], "runtime_scope": receipt["runtime_scope"], "digest": digest(receipt),
        "validation_scope": "structure_only",
        "producer_trust": "unverified",
        "source_freshness": "not_checked",
        "human_decision_verified": False,
    }
    if schema_id == HANDOFF_RECEIPT_SCHEMA_ID:
        summary["states"] = {
            field: receipt[field]["state"]  # type: ignore[index]
            for field in ("source_revision", "last_judgment", "open_boundary", "next_safe_action", "forbidden_actions")
        }
        summary["asserted_states"] = dict(summary["states"])
        summary["states"]["source_revision"] = "unknown"
        if summary["states"]["last_judgment"] == "human_recorded":
            summary["states"]["last_judgment"] = "unknown"
        summary["target_client"] = receipt["target_client"]
    else:
        summary["source_count"] = len(receipt["sources"])  # type: ignore[arg-type]
    return summary


def _recheck_source(root: Path, receipt: dict[str, object], ref: str) -> dict[str, object]:
    if receipt["schema_id"] != HANDOFF_RECEIPT_SCHEMA_ID:
        raise ReceiptCliError("source_recheck_requires_handoff")
    revision = receipt["source_revision"]
    if revision["source_id"] != source_identity("file", ref):
        raise ReceiptCliError("source_identity_path_mismatch")
    path = _relative_path(root, ref, must_exist=True)
    if not path.is_file():
        raise ReceiptCliError("source_not_file")
    file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if (revision["scheme"] != "sha256" or revision["value_digest"] != digest(file_digest)
            or revision["evidence_ref"] != f"file_sha256:{file_digest}"):
        raise ReceiptCliError("source_revision_mismatch")
    summary = _summary(receipt)
    summary.update(validation_scope="structure_and_current_source", source_freshness="matches_current_file")
    summary["states"]["source_revision"] = "verified"
    # A checksum match does not authenticate who wrote the receipt or a decision.
    return summary


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--root", default=".", help="Explicit local root for relative input/output paths")
    subcommands = value.add_subparsers(dest="command", required=True)
    for name in ("build-context", "build-handoff"):
        command = subcommands.add_parser(name)
        command.add_argument("--input", required=True, help="Relative JSON file or - for stdin")
        command.add_argument("--output", required=True, help="New relative JSON file or - for stdout")
    for name in ("validate", "inspect", "recheck-source"):
        command = subcommands.add_parser(name)
        command.add_argument("--input", required=True, help="Relative receipt JSON file or - for stdin")
        if name == "recheck-source":
            command.add_argument("--source", required=True, help="Exact relative file ref used to build the handoff")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve(strict=True)
    try:
        payload = _read_json(root, args.input)
        if args.command == "build-context":
            _write_json(root, args.output, _context_from_spec(payload))
        elif args.command == "build-handoff":
            _write_json(root, args.output, _handoff_from_spec(root, payload))
        else:
            normalized = _normalize(payload)
            summary = _recheck_source(root, normalized, args.source) if args.command == "recheck-source" else _summary(normalized)
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    except (ReceiptCliError, ValueError) as exc:
        print(json.dumps({"ok": False, "error_type": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
