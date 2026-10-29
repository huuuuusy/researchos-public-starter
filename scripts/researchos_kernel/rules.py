"""Rule table R: v2 task-extension descriptors and their script evaluators.

Every rule belongs to one family (plan v4 §5.1). This minimal kernel executes the
script rules; model-executed rules (edge recheck by a model, summary refresh,
evidence fill, new-use discovery, new material intake) arrive with dispatch.
A rule only emits *findings*; the boundary turns findings into requirements.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .ledger import digest
from .messages import t

SCHEMA_ID = "researchos-task-extension-v2"
CONTRACT_ID = "researchos-task-extension-v2.schema.json"
CONTRACT_RELATIVE = "09_templates/data_contracts/researchos-task-extension-v2.schema.json"
RULES_RELATIVE = "config/extensions/rules"
PURPOSE_VERSION = "keep-judgments-grounded-v1"
# Report D5 cause `time`: a rule declares a time trigger through its schema-enumerated `family`.
TIME_FAMILY = "time_elapsed"


def time_triggered(rule: dict) -> bool:
    return rule.get("family") == TIME_FAMILY

# Consequence by dependency distance to an active commitment (plan v4 §5, filter layer).
TOUCHES_JUDGMENT, TOUCHES_NEXT_STEP, TOUCHES_BASIS, UNRELATED = 1.0, 0.7, 0.3, 0.0


@dataclass
class Finding:
    rule_id: str
    rule_version: str
    binding_key: str
    summary: str
    read_set: dict
    commitment_id: str = ""
    consequence: float = UNRELATED
    only_you: bool = True
    due_days: int | None = None
    judgment_id: str = ""
    details: list = field(default_factory=list)
    options: list = field(default_factory=list)

    @property
    def issue_id(self) -> str:
        return digest([self.rule_id, self.binding_key, PURPOSE_VERSION])

    @property
    def read_digest(self) -> str:
        return digest(self.read_set)


def _locate(root: Path, fallback_root: Path | None, relative: str) -> Path:
    """A graph root without its own copy borrows the installation's (e.g. a demo graph)."""
    path = root / relative
    if not path.exists() and fallback_root is not None:
        return fallback_root / relative
    return path


def load_contract(root: Path, fallback_root: Path | None = None) -> tuple:
    """Return (contract, problems). Fail closed: without the contract no descriptor is admitted."""
    path = _locate(root, fallback_root, CONTRACT_RELATIVE)
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {}, [f"{CONTRACT_RELATIVE}: unreadable ({error})"]
    if contract.get("$id") != CONTRACT_ID:
        return {}, [f"{CONTRACT_RELATIVE}: $id must be {CONTRACT_ID}"]
    return contract, []


def _violations(value, schema: dict, where: str = "") -> list:
    """The subset of JSON Schema the v2 contract declares. One owner for the descriptor shape."""
    at = f" at {where}" if where else ""
    if "const" in schema and value != schema["const"]:
        return [f"{where or 'value'} must be {schema['const']!r}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{where or 'value'} must be one of {sorted(schema['enum'])}"]
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            return [f"expected an object{at}"]
        found = []
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                found.append(f"missing {key}{at}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    found.append(f"unknown field {key}{at}")
        for key, item in value.items():
            if key in properties:
                found.extend(_violations(item, properties[key], f"{where}.{key}" if where else key))
        return found
    if kind == "array":
        if not isinstance(value, list):
            return [f"expected a list{at}"]
        found = []
        if len(value) < int(schema.get("minItems", 0)):
            found.append(f"{where or 'value'} needs at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems") and len(value) != len({json.dumps(item, sort_keys=True) for item in value}):
            found.append(f"{where or 'value'} must not repeat a value")
        for index, item in enumerate(value):
            found.extend(_violations(item, schema.get("items", {}), f"{where}[{index}]"))
        return found
    if kind == "string":
        if not isinstance(value, str):
            return [f"expected a string{at}"]
        if len(value) < int(schema.get("minLength", 0)):
            return [f"{where or 'value'} must not be empty"]
        if "pattern" in schema and not re.match(schema["pattern"], value):
            return [f"{where or 'value'} must match {schema['pattern']}"]
        return []
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"expected an integer{at}"]
        if "minimum" in schema and value < schema["minimum"]:
            return [f"{where or 'value'} must be at least {schema['minimum']}"]
        return []
    if kind == "boolean" and not isinstance(value, bool):
        return [f"expected a boolean{at}"]
    return []


def load_registry(root: Path, fallback_root: Path | None = None) -> tuple:
    """Return (descriptors_by_id, problems) for every declared descriptor, scope-independent.

    This is the one admission port for v2 task extensions: the kernel reads it to schedule,
    ``scripts/validate_task_extensions.py`` reads it to gate. Neither validates on its own."""
    contract, problems = load_contract(root, fallback_root)
    if not contract:
        return {}, problems
    descriptors, sources = {}, {}
    directory = _locate(root, fallback_root, RULES_RELATIVE)
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            problems.append(f"{path.name}: unreadable ({error})")
            continue
        found = _violations(data, contract)
        if found:
            problems.extend(f"{path.name}: {row}" for row in found)
            continue
        if data["id"] in descriptors:
            problems.append(f"{path.name}: duplicate rule id {data['id']} (already in {sources[data['id']]})")
            continue
        descriptors[data["id"]], sources[data["id"]] = data, path.name
    return descriptors, problems


WRITE_CLASS_RELATIVE = "09_templates/data_contracts/researchos-write-class-v1.json"


DELEGABLE_AUTO_START = ("public", "internal")


def write_class(root: Path, fallback_root: Path | None = None) -> dict | None:
    try:
        return json.loads(_locate(root, fallback_root, WRITE_CLASS_RELATIVE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def delegation_problems(rule: dict, classes: dict | None) -> list:
    """Why a rule may not be resolved by a script (HJ-7). Deleg(a) := Registered(a) ∧ scope(a) ⊆ Sc_ε
    ∧ Reversible(a) ∧ Auth(α_ε, a). Stated as an allowlist, so an unrecognised target is refused:
      - Registered: it is a descriptor in the registry (the caller only passes those) run by a script,
        not a model whose output a script would wave through;
      - scope(a) ⊆ Sc_ε: its scope is its own;
      - Reversible: it returns a writeback, bounded to a non-empty list of `commitment:<field>` targets
        that the write-class contract names as fact class;
      - Auth: it declares how far it may start on its own (`pre.auto_start_max`) within public/internal.
    Everything else — any judgment-class field, path, relation, rule or an unbounded write — is open
    judgment and goes to Review. The descriptor schema has no field saying a check's basis is the
    researcher's judgment, so that case cannot be declared yet; no current check has that basis."""
    if rule.get("resolver") != "script":
        return []
    if not classes or "fact" not in classes:
        return ["the write-class contract is unreadable"]
    found = []
    if rule.get("executor") != "script":
        found.append(f"its executor is {rule.get('executor')}, not a script")
    if rule.get("scope_selector", "own_scope") != "own_scope":
        found.append("its scope is not its own")
    expect = rule.get("expect") or {}
    if expect.get("result") != "writeback":
        found.append("its result is not a reversible writeback")
    targets = expect.get("write_scope") or []
    if not targets:
        found.append("it declares no bounded write scope")
    facts = set(classes["fact"].get("commitment_fields", []))
    for target in targets:
        kind, _, name = str(target).partition(":")
        if kind != "commitment" or name not in facts:
            found.append(f"it writes {target}, which is not a fact-class commitment field")
    if (rule.get("pre") or {}).get("auto_start_max") not in DELEGABLE_AUTO_START:
        found.append("it declares no authorised auto-start bound (pre.auto_start_max)")
    return found


def load_rules(root: Path, runtime_scope: str, fallback_root: Path | None = None) -> tuple:
    """Return (rules_by_id, problems): the descriptors this scope may schedule. A rule that asks to
    be resolved by a script but is not delegable is still scheduled, resolved by a human (HJ-7)."""
    descriptors, problems = load_registry(root, fallback_root)
    rules = {rule_id: data for rule_id, data in descriptors.items()
             if runtime_scope in data["available_in"] and data.get("enabled", True)}
    classes = write_class(root, fallback_root)
    for rule_id, data in sorted(rules.items()):
        reasons = delegation_problems(data, classes)
        if reasons:
            rules[rule_id] = dict(data, resolver="human")
            problems.append(f"{rule_id}: not delegable ({'; '.join(reasons)}); resolved by a human")
    return rules, problems


def _active(config: dict, commitment) -> bool:
    return commitment is not None and commitment.state in set(config.get("active_states", []))


def _options(*rows) -> list:
    return [{"label": label, "action": action} for label, action in rows]


def _defer(lang: str) -> str:
    return f"ros decide {t(lang, 'ph.requirement')} defer --until {t(lang, 'ph.date')}"


def _lang(config: dict) -> str:
    return config.get("language", "zh-CN")


# Each script rule is a pair: its declared check, evaluated positively on one subject (Soul §3), and
# an evaluator that walks the rule's domain and turns every subject the check does not pass into a
# finding. The predicate lives in the check alone, so "why it is raised" and "when it closes" cannot
# drift apart; the evaluator only adds what a finding shows (summary, details, options, read set).
# A requirement whose finding disappears for any other reason — its subject became inactive, a field
# stopped parsing, a filter now skips it — does not thereby pass its check.
MET, UNMET, UNKNOWN = "met", "unmet", "unknown"


def _commitment(snapshot, key: str):
    kind, _, rest = key.partition(":")
    return snapshot.commitments.get(rest) if kind == "commitment" else None


def _edge_parts(snapshot, rest: str) -> tuple:
    """Split an ``edge:`` key on the node ref it starts with, so a `|` inside a path survives."""
    for ref in sorted(snapshot.nodes, key=len, reverse=True):
        if rest.startswith(ref + "|"):
            relation_type, _, target = rest[len(ref) + 1:].partition("|")
            return ref, relation_type, target
    ref, relation_type, target = (rest.split("|", 2) + ["", ""])[:3]
    return ref, relation_type, target


def _basis_rows(snapshot, judgment) -> list:
    """(basis, resolved ref, current version, state) for each basis in order; state is unresolved,
    unpinned (no version recorded), changed (pinned to another version) or current."""
    rows = []
    for basis in judgment.basis:
        ref, version = snapshot.resolve(basis.ref)
        state = ("unresolved" if not ref else "unpinned" if not basis.version
                 else "current" if version.startswith(basis.version) else "changed")
        rows.append((basis, ref, version, state))
    return rows


def _edge_sides(node, relation: dict, target_version: str) -> dict:
    """side -> whether it still matches the version it was confirmed at, for each side the edge declares."""
    confirmed = relation.get("confirmed_versions") or {}
    current = {"source": node.version, "target": target_version}
    return {side: current[side].startswith(str(confirmed[side])) for side in ("source", "target") if confirmed.get(side)}


def _check_basis(snapshot, config, rule, key, ledger_state, today):
    kind, _, rest = key.partition(":")
    if kind == "judgment":
        judgment = snapshot.judgments.get(rest)
        if not judgment:
            return UNKNOWN, "subject_absent", "subject_absent"
        if not judgment.basis:
            return UNKNOWN, "judgment has no basis to be current", "no_basis"
        for basis, ref, _, state in _basis_rows(snapshot, judgment):
            if state == "unresolved":
                return UNKNOWN, f"basis {basis.ref} does not resolve", "basis_unresolved"
            if state != "current":
                return UNMET, f"basis {ref} is not pinned to its current version", ""
        return MET, "every basis is pinned to its current version", ""
    if kind == "edge":
        ref, relation_type, target = _edge_parts(snapshot, rest)
        node = snapshot.nodes.get(ref)
        for relation in node.relations if node else []:
            if (str(relation.get("status", "")).lower() == "confirmed" and relation.get("type", "") == relation_type
                    and snapshot.resolve(str(relation.get("target", "")))[0] == target):
                sides = _edge_sides(node, relation, snapshot.resolve(target)[1])
                if len(sides) < 2:
                    return UNKNOWN, "confirmed edge carries no confirmed versions", "no_confirmed_versions"
                if all(sides.values()):
                    return MET, "both sides match their confirmed versions", ""
                return UNMET, "a side changed after the edge was confirmed", ""
        return UNKNOWN, "subject_absent", "subject_absent"
    return UNKNOWN, "subject_absent", "subject_absent"


def basis_recheck(snapshot, config, rule, ledger_state, today: date) -> list:
    findings, lang = [], _lang(config)
    for judgment in snapshot.judgments.values():
        # A judgment without a basis has nothing to re-check: its check stays unknown, but it is not raised here.
        if not judgment.basis or _check_basis(snapshot, config, rule, f"judgment:{judgment.id}", ledger_state,
                                              today)[0] == MET:
            continue
        commitment_id = snapshot.commitment_for_judgment(judgment)
        commitment = snapshot.commitments.get(commitment_id)
        rows = _basis_rows(snapshot, judgment)
        read_set = {f"judgment:{judgment.id}": judgment.block_hash}
        read_set.update({ref: version for _, ref, version, state in rows if state != "unresolved"})
        details = [t(lang, "basis.changed" if state == "changed" else "basis.unpinned",
                     title=snapshot.title_of(ref), ref=ref) for _, ref, _, state in rows if state in {"changed", "unpinned"}]
        details += [t(lang, "basis.unresolved", ref=basis.ref) for basis, _, _, state in rows if state == "unresolved"]
        findings.append(Finding(
            rule_id=rule["id"], rule_version=rule["version"], binding_key=f"judgment:{judgment.id}",
            summary=t(lang, "basis.summary", title=judgment.conclusion or judgment.id),
            read_set=read_set, commitment_id=commitment_id,
            consequence=TOUCHES_JUDGMENT if _active(config, commitment) else TOUCHES_BASIS,
            judgment_id=judgment.id, details=details,
            options=_options(
                (t(lang, "basis.opt.reconfirm"), f"ros admit --reconfirm {judgment.id}"),
                (t(lang, "basis.opt.revise"),
                 f"ros propose judgment --file {t(lang, 'ph.draft')} --target {t(lang, 'ph.target')}"),
                (t(lang, "opt.defer"), _defer(lang)),
            ),
        ))
    for node in snapshot.nodes.values():
        for relation in node.relations:
            if str(relation.get("status", "")).lower() != "confirmed":
                continue
            target_ref, target_version = snapshot.resolve(str(relation.get("target", "")))
            if not target_ref:
                continue
            # Raised when a side it declares has moved. Closing needs both sides declared and matching,
            # so an edge confirmed without versions is never raised and never closes on its own.
            stale = [t(lang, "edge.side.source", title=node.title) if side == "source"
                     else t(lang, "edge.side.target", title=snapshot.title_of(target_ref))
                     for side, current in _edge_sides(node, relation, target_version).items() if not current]
            if not stale:
                continue
            tracking = [c for c in snapshot.commitments.values()
                        if _active(config, c) and c.get("source_path") in {node.path, target_ref}]
            findings.append(Finding(
                rule_id=rule["id"], rule_version=rule["version"],
                binding_key=f"edge:{node.ref}|{relation.get('type', '')}|{target_ref}",
                summary=t(lang, "edge.summary", source=node.title, type=relation.get("type", ""),
                          target=snapshot.title_of(target_ref)),
                read_set={node.ref: node.version, target_ref: target_version},
                commitment_id=tracking[0].id if tracking else "",
                consequence=TOUCHES_BASIS if tracking else UNRELATED,
                details=[t(lang, "edge.changed", side=row) for row in stale],
                options=_options((t(lang, "edge.opt.reconfirm"), t(lang, "edge.opt.reconfirm.action")),
                                 (t(lang, "opt.defer"), _defer(lang))),
            ))
    return findings


def _verified_age(commitment, today: date) -> tuple | None:
    """(last verified, age in days, limit) of a commitment; None when either field cannot be read."""
    try:
        verified = date.fromisoformat(commitment.get("last_verified"))
        limit = max(1, int(commitment.get("stale_after_days", "14") or 14))
    except ValueError:
        return None
    return verified, (today - verified).days, limit


def _check_status(snapshot, config, rule, key, ledger_state, today):
    commitment = _commitment(snapshot, key)
    if not commitment:
        return UNKNOWN, "subject_absent", "subject_absent"
    parsed = _verified_age(commitment, today)
    if parsed is None:
        return UNKNOWN, "last_verified or stale_after_days cannot be read", "unreadable_field"
    _, age, limit = parsed
    return (MET, f"verified {age} day(s) ago, within {limit}", "") if age <= limit else \
        (UNMET, f"verified {age} day(s) ago, beyond {limit}", "")


def status_verify(snapshot, config, rule, ledger_state, today: date) -> list:
    # Raised only for active commitments; the check itself does not look at activity (as declared).
    findings, lang = [], _lang(config)
    for commitment in snapshot.commitments.values():
        if not _active(config, commitment) or _check_status(snapshot, config, rule, f"commitment:{commitment.id}",
                                                            ledger_state, today)[0] != UNMET:
            continue
        verified, age, limit = _verified_age(commitment, today)
        changed = snapshot.changed_after(commitment.get("source_path"), verified)
        detail = (t(lang, "status.source_changed", source=commitment.get("source_path"), date=changed) if changed
                  else t(lang, "status.no_change"))
        findings.append(Finding(
            rule_id=rule["id"], rule_version=rule["version"], binding_key=f"commitment:{commitment.id}",
            summary=t(lang, "status.summary", title=commitment.title, age=age, limit=limit),
            read_set={"last_verified": commitment.get("last_verified"), "stale_after_days": str(limit), "source_changed": changed},
            commitment_id=commitment.id, consequence=TOUCHES_NEXT_STEP, only_you=False, details=[detail],
            options=_options((t(lang, "status.opt.verified"), t(lang, "status.opt.verified.action")),
                             (t(lang, "opt.defer.short"), _defer(lang))),
        ))
    return findings


def _due_in(config, rule, commitment, today: date) -> tuple:
    """(due date, days until it, warning window); the date is None when none can be read."""
    due = commitment.due_date()
    window = int(rule.get("trigger", {}).get("days", config.get("deadline_warning_days", 7)))
    return due, (due - today).days if due else None, window


def _check_deadline(snapshot, config, rule, key, ledger_state, today):
    commitment = _commitment(snapshot, key)
    if not commitment:
        return UNKNOWN, "subject_absent", "subject_absent"
    if not _active(config, commitment):
        return MET, f"commitment inactive ({commitment.state})", ""  # declared: ..._or_commitment_inactive
    due, days, window = _due_in(config, rule, commitment, today)
    if not due:
        return UNKNOWN, "no readable due date", "no_due_date"
    return (MET, f"due in {days} day(s), outside the {window}-day window", "") if days > window else \
        (UNMET, f"due in {days} day(s), inside the {window}-day window", "")


def deadline_warning(snapshot, config, rule, ledger_state, today: date) -> list:
    findings, lang = [], _lang(config)
    for commitment in snapshot.commitments.values():
        if _check_deadline(snapshot, config, rule, f"commitment:{commitment.id}", ledger_state, today)[0] != UNMET:
            continue
        due, days, _ = _due_in(config, rule, commitment, today)
        summary = (t(lang, "deadline.due_in", title=commitment.title, days=days, date=due.isoformat()) if days >= 0
                   else t(lang, "deadline.overdue", title=commitment.title, days=-days, date=due.isoformat()))
        findings.append(Finding(
            rule_id=rule["id"], rule_version=rule["version"], binding_key=f"commitment:{commitment.id}",  # the date lives in the read set: a new date advances the generation
            summary=summary,
            read_set={"due": due.isoformat(), "state": commitment.state},
            commitment_id=commitment.id, consequence=TOUCHES_NEXT_STEP, due_days=days,
            details=[t(lang, "deadline.next", next=commitment.get("next_step") or t(lang, "not_written"))],
            options=_options(
                (t(lang, "deadline.opt.keep"), f"ros decide {t(lang, 'ph.requirement')} defer --until {t(lang, 'ph.due')}"),
                (t(lang, "deadline.opt.adjust"), t(lang, "deadline.opt.adjust.action")),
                (t(lang, "deadline.opt.status_quo"), f"ros decide {t(lang, 'ph.requirement')} cancel --reason {t(lang, 'ph.reason')}")),
        ))
    return findings


def _check_confirmed(snapshot, config, rule, key, ledger_state, today):
    kind, _, rest = key.partition(":")
    judgment = snapshot.judgments.get(rest) if kind == "judgment" else None
    if not judgment:
        return UNKNOWN, "subject_absent", "subject_absent"
    if judgment.block_hash in ledger_state.get("admitted_judgments", {}).get(judgment.id, set()):
        return MET, "this block version was admitted", ""
    if judgment.block_hash in ledger_state.get("confirmed_judgments", {}).get(judgment.id, set()):
        return MET, "this block version was confirmed after the fact (break-glass; not an admission)", ""
    return UNMET, "this block version was never admitted or confirmed", ""


def confirm_judgment_change(snapshot, config, rule, ledger_state, today: date) -> list:
    admitted = ledger_state.get("admitted_judgments", {})
    findings, lang = [], _lang(config)
    for judgment in snapshot.judgments.values():
        if _check_confirmed(snapshot, config, rule, f"judgment:{judgment.id}", ledger_state, today)[0] != UNMET:
            continue
        commitment_id = snapshot.commitment_for_judgment(judgment)
        commitment = snapshot.commitments.get(commitment_id)
        is_new = judgment.id not in admitted
        findings.append(Finding(
            rule_id=rule["id"], rule_version=rule["version"], binding_key=f"judgment:{judgment.id}",
            summary=t(lang, "confirm.new" if is_new else "confirm.modified", title=judgment.conclusion or judgment.id),
            read_set={f"judgment:{judgment.id}": judgment.block_hash},
            commitment_id=commitment_id,
            consequence=TOUCHES_JUDGMENT if _active(config, commitment) else TOUCHES_BASIS,
            judgment_id=judgment.id, details=[t(lang, "confirm.where", path=judgment.path, line=judgment.line)],
            options=_options((t(lang, "confirm.opt.confirm"), f"ros admit --confirm {judgment.id}"),
                             (t(lang, "confirm.opt.edit"), t(lang, "confirm.opt.edit.action", path=judgment.path, id=judgment.id)),
                             (t(lang, "opt.defer.short"), _defer(lang))),
        ))
    return findings


def _check_question(snapshot, config, rule, key, ledger_state, today):
    commitment = _commitment(snapshot, key)
    if not commitment:
        return UNKNOWN, "subject_absent", "subject_absent"
    return (MET, "question written", "") if commitment.get("question") else (UNMET, "no question", "")


def missing_question(snapshot, config, rule, ledger_state, today: date) -> list:
    # Raised only for active commitments the researcher leads; the check asks only whether Q is written.
    findings, lang = [], _lang(config)
    for commitment in snapshot.commitments.values():
        if not _active(config, commitment) or commitment.get("responsibility") != "lead" or \
                _check_question(snapshot, config, rule, f"commitment:{commitment.id}", ledger_state, today)[0] != UNMET:
            continue
        findings.append(Finding(
            rule_id=rule["id"], rule_version=rule["version"], binding_key=f"commitment:{commitment.id}",
            summary=t(lang, "question.summary", title=commitment.title),
            read_set={"question": ""},
            commitment_id=commitment.id, consequence=TOUCHES_NEXT_STEP,
            details=[t(lang, "question.detail")],
            options=_options((t(lang, "question.opt.write"), t(lang, "question.opt.write.action")),
                             (t(lang, "opt.defer.short"), _defer(lang))),
        ))
    return findings


def domain(snapshot, rule: dict) -> set:
    """The keys this rule matches over, from its declared ``evaluates``. The kernel needs this
    to tell "checked and passed" from "never looked at": a key in the domain that no boundary
    evaluated is coverage unknown (canon 《图的三个轴》), never a pass."""
    keys = set()
    for collection in rule.get("evaluates", []):
        if collection == "judgments":
            keys |= {f"judgment:{jid}" for jid in snapshot.judgments}
        elif collection == "commitments":
            keys |= {f"commitment:{cid}" for cid in snapshot.commitments}
        elif collection == "nodes":
            keys |= set(snapshot.nodes)
    return keys


def subject_version(snapshot, key: str) -> str:
    """The version of a requirement's subject that a met check is evidence about ("" if gone)."""
    kind, _, rest = key.partition(":")
    if kind == "judgment":
        judgment = snapshot.judgments.get(rest)
        return judgment.block_hash if judgment else ""
    if kind == "commitment":
        commitment = snapshot.commitments.get(rest)
        return commitment.version if commitment else ""
    if kind == "edge":
        ref, _, target = _edge_parts(snapshot, rest)
        node = snapshot.nodes.get(ref)
        return digest([node.version, snapshot.resolve(target)[1]]) if node else ""
    return rest if kind == "coverage" else ""


# Every script rule the kernel can run, by the condition its descriptor declares (``trigger.when``) ->
# (evaluator, its declared check). The family stays what the descriptor says it is (it decides whether
# elapsed time is a cause), and the evaluator reads its parameters (a deadline's `days`) from the rule,
# so a second rule of an existing kind, such as a 14-day deadline warning, is one JSON file.
EVALUATORS = {
    "basis_version_changed": (basis_recheck, _check_basis),
    "last_verified_older_than_stale_after_days": (status_verify, _check_status),
    "due_date_within_days": (deadline_warning, _check_deadline),
    "judgment_block_without_admission_receipt": (confirm_judgment_change, _check_confirmed),
    "active_lead_commitment_without_question": (missing_question, _check_question),
}


def evaluator_for(rule: dict) -> tuple | None:
    """(evaluator, check) for a descriptor's declared condition, or None when this kernel cannot run it."""
    return EVALUATORS.get((rule.get("trigger") or {}).get("when", ""))


# Report D2: an unknown is undecidable by evidence only when its basis is researcher judgment, its
# per-check budget is spent, or what blocks it lies outside the scope. A vanished subject and a basis
# that resolves to nothing are the last case; an unreadable field or a missing basis is fixed at the
# source, so it stays open work instead of becoming a question. Each check returns its unknown's code
# with its reason, so a question's identity does not follow the reason's wording.
UNDECIDABLE_CODES = frozenset({"subject_absent", "basis_unresolved"})


def check(snapshot, config, rule: dict, key: str, ledger_state: dict, today: date) -> tuple:
    """(result, why, code) of the rule's declared check on one subject; ``code`` names the kind of an
    unknown and is empty otherwise. A rule without an executable check is unknown."""
    evaluator = evaluator_for(rule)
    if evaluator is None:
        return UNKNOWN, "rule declares no executable check", "no_check"
    kind, _, rest = key.partition(":")
    if kind == "commitment" and rest in getattr(snapshot, "ambiguous_commitments", frozenset()):
        # CC-5: the commitment is declared twice; that is fixed in the portfolio, not asked about.
        return UNKNOWN, "the commitment's identity is ambiguous in the portfolio", "subject_ambiguous"
    return evaluator[1](snapshot, config, rule, key, ledger_state, today)


def evaluate(snapshot, config: dict, rules: dict, ledger_state: dict, today: date) -> dict:
    findings = {}
    for _, rule in sorted(rules.items()):
        evaluator = evaluator_for(rule)
        if evaluator is None or rule.get("executor") != "script":
            continue  # declared but not executable in this kernel version
        for finding in evaluator[0](snapshot, config, rule, ledger_state, today):
            findings[finding.issue_id] = finding
    return findings
