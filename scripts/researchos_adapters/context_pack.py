"""The bounded context pack and its ContextReceipt: what an executor may receive, and the record of
what left and where (Soul §4).

Every executor — the session Agent, a provider, a copy packet — receives context only through
``build_context_pack``. Only public and internal sources are delivered; sensitive ones need the
researcher's own terminal confirmation; private and unrecognised labels are excluded. Whole sources
are delivered or excluded, never cut mid-text.
"""

from __future__ import annotations

import hashlib
import sys
import uuid
from pathlib import Path

from researchos_kernel.context_receipt import AXIS_STATES, CONTEXT_RECEIPT_SCHEMA_ID, normalize_context_receipt

from .markdown_repo import split_frontmatter

DELIVERABLE = {"public", "internal"}


def terminal_confirms(ref: str, label: str, destination: str = "the session Agent") -> bool:
    """Soul §4: sensitive material needs the researcher's own confirmation on this machine. A flag
    the session Agent types is not that; an interactive terminal answer is."""
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        return False
    sys.stderr.write(f"Deliver sensitive source {ref} ({label}) to {destination}? [y/N] ")
    sys.stderr.flush()
    return sys.stdin.readline().strip().lower() in {"y", "yes"}


def receipt_axes(**states) -> dict:
    """Receipt axes; every stated axis carries its evidence, the rest stay unknown."""
    axes = {axis: {"state": "unknown", "evidence_ref": ""} for axis in AXIS_STATES}
    for axis, (state, evidence) in states.items():
        axes[axis] = {"state": state, "evidence_ref": evidence[:160]}
    return axes


def portfolio_sensitivity(root: Path, snapshot) -> tuple:
    """(label, declared fields) of the portfolio, which is not a node (its commitments are).

    Soul §4: a source may declare which of its fields are delivered as internal; undeclared
    fields keep the source's label, and the declaration does not change that label."""
    path = root / snapshot.portfolio_path if snapshot.portfolio_path else None
    if not path or not path.is_file():
        return "unknown", []
    scalars, _, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    declared = str(scalars.get("context_fields") or "").split(" #", 1)[0]
    return (str(scalars.get("sensitivity") or "internal").strip().lower(),
            [field.strip() for field in declared.split(",") if field.strip()])


def build_context_pack(result, ledger, root: Path, config: dict, runtime_scope: str, target: str, *,
                       service: str, service_source: str, surface: str, delivery: str,
                       destination: str = "the session Agent", run_id: str = "", task_id: str = "",
                       episode_id: str = "") -> dict:
    """The bounded pack for ``target`` over the boundary ``result`` and its receipt; ``ledger``
    records what left and where."""
    snapshot = result.snapshot
    limit = int(config.get("context", {}).get("max_chars", 40000))
    portfolio_label, context_fields = portfolio_sensitivity(root, snapshot)
    withheld_fields, released = [], []
    cards, blocks = [], []  # (kind, ref, label, sensitivity, text)
    if target.startswith("commitment:") or target in snapshot.commitments:
        cid = target.split(":", 1)[-1]
        commitment = snapshot.commitments.get(cid)
        if not commitment:
            raise SystemExit(f"unknown commitment: {target}")
        if portfolio_label != "private" or not context_fields:
            # Soul §4: only a private portfolio may release declared fields; a sensitive one still
            # needs the researcher's terminal confirmation, an unrecognised label is excluded.
            cards.append(("commitment", f"commitment:{cid}", commitment.title, portfolio_label,
                          f"# commitment:{cid} {commitment.title}\n" +
                          "\n".join(f"- {k}: {v}" for k, v in commitment.fields.items())))
        else:
            # Only the fields the source itself declared; the title is a field like any other.
            shown = {k: v for k, v in commitment.fields.items() if k in context_fields}
            released = [k for k in context_fields if k in shown or (k == "title" and commitment.title)]
            withheld_fields = sorted(k for k in commitment.fields if k not in context_fields)
            title = commitment.title if "title" in context_fields else ""
            cards.append(("commitment", f"commitment:{cid}", title or f"commitment:{cid}", "declared_fields",
                          f"# commitment:{cid}" + (f" {title}" if title else "") + "\n" +
                          "\n".join(f"- {k}: {v}" for k, v in shown.items())))
        judgments = [j for j in snapshot.judgments.values() if snapshot.commitment_for_judgment(j) == cid]
        for judgment in judgments:
            host = snapshot.nodes.get(judgment.path)
            label = host.sensitivity if host else (portfolio_label if judgment.path == snapshot.portfolio_path
                                                   else "unknown")
            blocks.append(("judgment", f"judgment:{judgment.id}", judgment.conclusion or judgment.id, label,
                           judgment.raw))
        refs = [commitment.get("source_path")] + [b.ref for j in judgments for b in j.basis]
    else:
        if not snapshot.resolve(target)[0]:
            raise SystemExit(f"not found in the scanned graph: {target}")
        refs = [target]
    seen = {ref for _, ref, *_ in cards + blocks}
    heading = " ({})" if config.get("language") == "en" else "（{}）"
    for ref in refs:
        resolved, _ = snapshot.resolve(ref) if ref else ("", "")
        node = snapshot.nodes.get(resolved)
        if not node or resolved in seen:
            continue
        seen.add(resolved)
        body = (root / node.path).read_text(encoding="utf-8")
        cards.append(("node", resolved, node.title, node.sensitivity,
                      f"# {node.title}{heading.format(f'{node.path}@{node.version[:8]}')}\n{body}"))
    sources = cards + blocks  # the cards a judgment rests on come before the judgments
    dropped = [ref for _, ref, *_ in sources[20:]]  # one receipt records at most 20 sources
    sources = sources[:20]

    egress = ("egressed", f"{service} ({service_source})") if service else None
    parts, delivered, excluded, rows, used = [], [], [], [], 0
    for kind, ref, label, sensitivity, text in sources:
        grant = f"session_scope:{sensitivity}" if sensitivity in DELIVERABLE else \
            ("source_declared_fields:" + ",".join(released) if sensitivity == "declared_fields" else "")
        if sensitivity == "sensitive" and terminal_confirms(ref, label, destination):
            grant = "researcher_terminal_confirmation"
        if not grant:
            why = f"sensitivity:{sensitivity}"
            if sensitivity == "sensitive":
                why += ":needs the researcher's terminal confirmation"
            axes = receipt_axes(authorization=("unauthorized", why), selection=("not_selected", why),
                                delivery=("not_delivered", why), exclusion=("excluded", why),
                                egress=("not_egressed", why))
            excluded.append({"ref": ref, "reason": why})
        elif used + len(text) > limit:
            why = f"budget:max_chars={limit}"
            axes = receipt_axes(authorization=("authorized", grant), selection=("selected", "ros_context"),
                                delivery=("not_delivered", why), exclusion=("excluded", why),
                                egress=("not_egressed", why))
            excluded.append({"ref": ref, "reason": why})
        else:
            axes = receipt_axes(authorization=("authorized", grant), selection=("selected", "ros_context"),
                                delivery=("delivered", delivery), exclusion=("not_excluded", "ros_context"),
                                **({"egress": egress} if egress else {}))
            parts.append(text)
            delivered.append(ref)
            used += len(text) + 7
        rows.append({"source_id": "", "kind": kind, "ref_digest": hashlib.sha256(ref.encode("utf-8")).hexdigest(),
                     # An excluded source's label is withheld too: an unsalted digest of a private title can be guessed.
                     "label_digest": hashlib.sha256((label if axes["delivery"]["state"] == "delivered" else "").encode("utf-8")).hexdigest(),
                     "requested": True, **axes})
    excluded += [{"ref": ref, "reason": "capacity:20_sources_per_receipt"} for ref in dropped]
    receipt = normalize_context_receipt({
        "schema_id": CONTEXT_RECEIPT_SCHEMA_ID, "receipt_id": "",
        "task_id": task_id or "task:" + hashlib.sha256(f"ros-context:{target}".encode("utf-8")).hexdigest(),
        "run_id": run_id or f"ros-context-{uuid.uuid4().hex[:12]}", "runtime_scope": runtime_scope,
        "producer": {"kind": "ros", "surface": surface, "evidence_class": "server_recorded"},
        "sources": rows, "rejected_claims": []}, trusted_producer=True)
    pack = "\n\n---\n\n".join(parts)
    with ledger.lock():
        # The ledger references the receipt by id and keeps what went where; the receipt itself
        # belongs with the TaskEnvelope of its episode (CC-6), not in a store of its own.
        ledger.decision("inspect", read_set=delivered, episode_id=episode_id, detail={
            "action": "context_delivered", "purpose": target, "service": service or "unknown",
            "service_claim": service_source, "context_receipt_id": receipt["receipt_id"],
            "excluded": excluded, "withheld_fields": withheld_fields})
    return {"delivered": delivered, "excluded": excluded, "service": service or "unknown",
            "service_claim": service_source, "receipt_id": receipt["receipt_id"], "withheld_fields": withheld_fields,
            "context_receipt": receipt, "pack": pack, "dropped": len(dropped)}
