"""One on-demand decision boundary (plan v4 appendix §5; technical report Section 3).

absorb observations -> evaluate rules on the current graph -> merge requirements
by issue_id (generation advances when the read set changes) -> resolve only what
its declared check establishes on the current subject -> advance the cursor last. There is no timer: most ``ros``
commands run a boundary first (ros.py names the exceptions). Running it twice on the same sources appends
nothing. Records go to the context-impact review ledger family (see ``ledger``).
Dispatch and collection (steps 2 and 7) arrive with the executor port (D4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import rules as rule_table
from . import scope as scope_axis
from .ledger import OPEN_STATUSES, Ledger, binding, digest, now_iso, requirement_binding
from .messages import t

# Report D3: the five exits of a bounded question, each with its own destination.
ASK_OPTIONS = ("satisfied", "unsatisfied", "narrow", "cancel", "defer")



@dataclass
class BoundaryResult:
    snapshot: object
    findings: dict
    states: dict
    requirements: dict
    changed: dict = field(default_factory=dict)
    transitions: list = field(default_factory=list)
    problems: list = field(default_factory=list)
    scope: object = None       # the frozen scope of this boundary (Sc_ε)
    coverage: dict = field(default_factory=dict)
    suppressed: int = 0        # findings on keys of closed episodes: no longer derived (report D0)
    placements: dict = field(default_factory=dict)
    rule_versions: dict = field(default_factory=dict)  # Ver of this boundary: rule id -> descriptor version
    coverage_domains: dict = field(default_factory=dict)  # coverage requirement -> uncovered keys (None = unknown)
    source_digest: str = ""  # sv of this boundary
    point_id: str = ""       # its decision point
    unknowns: dict = field(default_factory=dict)  # requirement -> which kind of unknown (CC-11)


def diff_versions(before: dict, after: dict) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(ref for ref in set(after) & set(before) if after[ref] != before[ref])
    return {"added": added, "removed": removed, "modified": modified}


def ledger_for(root: Path, config: dict) -> Ledger:
    return Ledger(root / config["requirement_ledger"])


def run_boundary(root: Path, config: dict, *, snapshot_builder, today: date | None = None,
                 runtime_scope: str = "private", install_root: Path | None = None,
                 ask_room: int | None) -> BoundaryResult:
    """``ask_room``: how many new questions the open episodes may still ask (β^ask, CC-10). It has no
    default: a caller states the room, or states None (no episode caps questions)."""
    today = today or date.today()
    ledger = ledger_for(root, config)
    with ledger.lock():
        cursor = ledger.read_cursor()
        snapshot, cache = snapshot_builder(root, config, cursor.get("cache"))
        versions = snapshot.version_map()
        changed = diff_versions(cursor.get("versions", {}), versions)
        rules, rule_problems = rule_table.load_rules(root, runtime_scope, install_root)
        trajectory = ledger.trajectory()
        derived = ledger.derive_states(trajectory)
        registry = ledger.requirements(trajectory)
        findings = rule_table.evaluate(snapshot, config, rules, derived, today)
        evaluated = {rule_id for rule_id, rule in rules.items() if rule.get("enabled", True)}

        states = derived["issues"]
        # One check record per (requirement, generation, result, basis): replaying a boundary on
        # unchanged sources must append nothing (CR-16), whatever the check said last time.
        recorded = {(row["payload"].get("binding", {}).get("issue_id"), row["payload"].get("binding", {}).get("generation"),
                     row["payload"].get("result"), row["payload"].get("basis")): row["id"]
                    for row in trajectory if row.get("kind") == "check"}

        def check_once(result, *, bound, **fields):
            """Record a check once per (requirement, generation, result, basis); return its id either way."""
            marker = (bound["issue_id"], bound["generation"], result, fields.get("basis", ""))
            if marker not in recorded:
                recorded[marker] = ledger.check(result, bound=bound, **fields)["id"]
            return recorded[marker]
        asks = ledger.asks(trajectory)

        def withdraw(ask_id, issue_id, why):
            question = asks.get(ask_id)
            if question and question.get("state") == "asked":
                row = ledger.restate_ask(ask_id, question, issue_id, "withdrawn", detail={"reason": why})
                asks[ask_id] = row["payload"]
        cursor_digest = digest(versions)
        point_id = digest([cursor_digest, today.isoformat(), len(trajectory)])
        transitions = []

        # Sc_ε: frozen extensionally, once, before anything is judged complete. Containment
        # changes and episode closures after this point belong to the next episode, not this one.
        # The source closes an episode; the local ledger may only refute the receipt (report D0).
        placements = scope_axis.placements_from_snapshot(snapshot, ledger.closure_receipts(trajectory))
        frozen, scope_problems = scope_axis.freeze(
            placements, str(config.get("scope_node", scope_axis.ROOT_SCOPE)), frozen_at=now_iso(),
            cross=config.get("cross_scope_keys", []))
        scope_problems = scope_axis.closure_problems(placements) + scope_problems
        # A closed episode has left cl(n): its keys no longer derive requirements (report D0).
        # The source is authoritative for closure (a clean clone keeps it closed); Done treats an unverified
        # closure conservatively instead — see completion().
        closed_keys = {key for key, place in placements.items() if place.closed}
        suppressed = [issue for issue, finding in findings.items() if requirement_key(finding.binding_key) in closed_keys]
        for issue in suppressed:
            findings.pop(issue)
        # A descriptor that could not be read has an unknown domain: it is coverage unknown with
        # no key list, never silently absent. A descriptor that is *disabled* or out of this
        # runtime scope is out of the frozen spec instead — a deliberate off switch is not an
        # uninspected input, and counting it would make every boundary incomplete by definition.
        sources = source_versions(snapshot, versions)
        # Cold start: no cursor and nothing registered. A ledger with requirements but no cursor lost its spec.
        attribution = Attribution(cursor.get("spec"), cold=not cursor.get("digest") and not states,
                                  snapshot=snapshot, config=config,
                                  rules=rules, derived=derived, sources=sources, frozen=frozen, today=today)
        unreadable = sorted({problem.split(":", 1)[0] for problem in rule_problems if ":" in problem})
        in_scope, covered, global_rules = set(), set(), []
        coverage_domains = {}
        pending = [(rule_id, rule, rule_table.domain(snapshot, rule)) for rule_id, rule in sorted(rules.items())]
        pending += [(f"descriptor:{name}", {"version": ""}, None) for name in unreadable]
        for rule_id, rule, keys in pending:
            if keys is None:
                uncovered_label, keys = "unreadable descriptor", set()
            else:
                uncovered_label = ""

            if rule.get("scope_selector", "own_scope") == "global":
                global_rules.append(rule_id)
            elif keys:
                keys = {key for key in keys if key in frozen}
            in_scope |= keys
            if not uncovered_label and rule_id in evaluated and rule_table.evaluator_for(rule):
                covered |= keys
            elif keys or uncovered_label:
                # A declared rule that did not run leaves its whole domain uncovered. It is
                # registered as one requirement per rule, whose read set names the keys, so it
                # cannot close while any remain and the boundary cannot report completion.
                uncovered = sorted(keys)
                issue_id = digest([f"coverage:{rule_id}", rule_table.PURPOSE_VERSION])
                coverage_domains[issue_id] = None if uncovered_label else frozenset(uncovered)
                state = states.get(issue_id)
                read_set = {"uncovered_count": uncovered_label or str(len(uncovered)),
                            "uncovered_keys": uncovered[:20], "rule_id": rule_id}
                bound = binding(issue_id, (state or {}).get("generation", 0) + 1,
                                rule_version=str(rule.get("version", "")),
                                purpose_version=rule_table.PURPOSE_VERSION,
                                source_version_vector=digest(read_set))
                if state is None or state["read_digest"] != digest(read_set):
                    cause, miss_status = attribution.coverage(rule_id, rule, uncovered, state)
                    requirement = None if issue_id in registry else {
                        "rule_id": rule_id, "rule_version": str(rule.get("version", "")),
                        "purpose_version": rule_table.PURPOSE_VERSION, "binding": f"coverage:{rule_id}",
                        "commitment_id": "", "kind": "maintenance", "executor": "script", "resolver": "human"}
                    ledger.transition(bound, "open", "opened" if state is None else "refreshed",
                                      point_id=point_id, requirement=requirement,
                                      summary=f"coverage unknown: {rule_id} was not evaluated over "
                                              f"{uncovered_label or str(len(uncovered)) + ' key(s)'} "
                                              f"inside the frozen scope",
                                      read_set=read_set, cause=cause, miss_status=miss_status)
                check_once("not_evaluated", requirement_id=rule_id, bound=bound,
                           basis="declared rule not evaluated over its in-scope domain "
                                 "(coverage unknown, not evidence unknown)", point_id=point_id,
                           reason_code="coverage_unevaluated")
        coverage = scope_axis.coverage(frozen, covered | (frozen.members - in_scope))
        coverage.update({"coverage_unknown_in_scope": len(in_scope - covered) + len(unreadable),
                         "unreadable_descriptors": unreadable,
                         "uncovered_keys": sorted(in_scope - covered)[:20],
                         "in_scope_match_count": len(in_scope),
                         "evaluated_match_count": len(covered),
                         "global_rules": global_rules})

        unattributed, problems_d5, capped = [], [], []
        for issue_id, finding in sorted(findings.items()):
            state = states.get(issue_id)
            if state is None:
                action, generation = "opened", 1
            elif state["status"] == "resolved":
                action, generation = "reopened", state["generation"] + 1  # the condition holds again
            elif state["read_digest"] == finding.read_digest:
                continue  # same occurrence (open, deferred, waiting or cancelled): idempotent
            elif state["status"] == "cancelled":
                action, generation = "reopened", state["generation"] + 1  # a cancel binds one read set
            else:
                action, generation = "refreshed", state["generation"] + 1
            cause, miss_status = attribution.finding(finding, state, registry.get(issue_id, {}))
            if not cause:
                # D5: none of the seven causes holds, so this is not registrable work; say so loudly.
                # The spec remembers it, so a later boundary cannot count it as a miss.
                unattributed.append(issue_id)
                problems_d5.append(f"{finding.rule_id}: {finding.binding_key}: no cause holds; not registered (D5)")
                continue
            if state and state["status"] == "waiting" and state.get("reopen_trigger", "").startswith("answer:"):
                withdraw(state["reopen_trigger"][7:], issue_id, "the finding came back; the question is moot")
            requirement = None
            if issue_id not in registry:
                rule = rules[finding.rule_id]
                requirement = {"rule_id": finding.rule_id, "rule_version": finding.rule_version,
                               "purpose_version": rule_table.PURPOSE_VERSION, "binding": finding.binding_key,
                               "commitment_id": finding.commitment_id, "kind": rule.get("kind", "maintenance"),
                               "executor": rule["executor"], "resolver": rule["resolver"]}
            bound = binding(issue_id, generation, rule_version=finding.rule_version,
                            purpose_version=rule_table.PURPOSE_VERSION, source_version_vector=finding.read_digest)
            ledger.transition(bound, "open", action, point_id=point_id, requirement=requirement,
                              summary=finding.summary, read_set=finding.read_set, cause=cause, miss_status=miss_status)
            transitions.append((action, finding))

        if attribution.unknown:
            # D5: the previous spec was not frozen, so `miss` is undefined for the work above. One
            # requirement says so; it is always in scope, so this run cannot report completion.
            # It has one identity: a later loss while it is open adds nothing, after it closed reopens it.
            state = states.get(UNRECOMPUTABLE_ID)
            if state is None or state["status"] in {"resolved", "cancelled"}:
                bound = binding(UNRECOMPUTABLE_ID, (state or {}).get("generation", 0) + 1,
                                purpose_version=rule_table.PURPOSE_VERSION, source_version_vector=point_id)
                ledger.transition(bound, "open", "opened" if state is None else "reopened", point_id=point_id,
                                  cause="initial", miss_status="unknown",
                                  requirement=None if UNRECOMPUTABLE_ID in registry else {
                                      "rule_id": "previous_spec", "rule_version": SPEC_SCHEMA,
                                      "purpose_version": rule_table.PURPOSE_VERSION, "binding": UNRECOMPUTABLE,
                                      "commitment_id": "", "kind": "maintenance", "executor": "human", "resolver": "human"},
                                  summary=t(config.get("language", "zh-CN"), "spec.unrecomputable", count=attribution.unknown),
                                  read_set={"cursor": str(cursor.get("digest", "")), "point_id": point_id})
                transitions.append(("opened", {"rule_id": "previous_spec"}))

        executable = {rule_id for rule_id in evaluated if rule_table.evaluator_for(rules[rule_id])}
        for issue_id, state in sorted(states.items()):
            if issue_id in findings or state["status"] not in OPEN_STATUSES:
                continue
            registration = registry.get(issue_id, {})
            rule_id, subject = registration.get("rule_id", ""), registration.get("binding", "")
            bound = requirement_binding(issue_id, state, registration)
            trigger = state.get("reopen_trigger", "")
            if state["status"] == "waiting" and trigger.startswith("date:") and trigger[5:] <= today.isoformat():
                # A deferral with a registered trigger reopens when the trigger is reached (cause: time).
                ledger.transition(bound, "open", "reopened:time", point_id=point_id, summary=state.get("summary", ""),
                                  cause="time", miss_status="not_applicable")
                transitions.append(("reopened", registration))
                state = dict(state, status="open", reopen_trigger="")
                trigger = ""
            pending_ask = trigger[7:] if state["status"] == "waiting" and trigger.startswith("answer:") else ""
            if subject.startswith(("spec:", "field:")):
                # A requirement the kernel registered itself: the previous spec that cannot be
                # recomputed (D5), and a judgment-class field written directly (HJ-12). Neither has a
                # rule or a domain, so neither is coverage unknown; each is closed by a decision. Its
                # deferral is reopened above like any other, so a passed date does not strand it.
                continue
            if rule_id not in executable:
                # An unreadable, disabled, out-of-scope or non-executable rule says nothing.
                # A rule that is switched off or out of this runtime scope is out of the spec, not an
                # uninspected input (CC-11): recording it as coverage unknown would make every boundary
                # incomplete by definition. Only a declared, enabled rule that did not run is coverage.
                off = rule_id in rules and rule_id not in evaluated  # declared but switched off, not unread
                check_once("not_evaluated", requirement_id=rule_id, bound=bound, point_id=point_id,
                           basis="rule is disabled or out of this runtime scope (out of spec, not coverage unknown)"
                                 if off else
                                 "rule not evaluated in this boundary (coverage unknown, not evidence unknown)",
                           reason_code="out_of_spec" if off else "coverage_unevaluated")
                continue
            if subject.startswith("coverage:"):
                # Coverage unknown closes only when the rule actually ran over its domain.
                result, why, code = "met", "the declared rule was evaluated over its in-scope domain", ""
            else:
                # Soul §3: a requirement closes only when its declared check holds. The check is
                # evaluated positively on the bound subject; a finding that is simply no longer
                # produced — inactive subject, unreadable field, a filter that now skips it — is
                # not a check. Unmet or unknown keeps the requirement open for the researcher.
                result, why, code = rule_table.check(snapshot, config, rules[rule_id], subject, derived, today)
            declared = ",".join(rules[rule_id].get("check", []))
            basis = f"declared check {declared}: {why}"
            if pending_ask and (result != "unknown" or code not in rule_table.UNDECIDABLE_CODES):
                # Evidence decided it after all, or it became fixable at the source: withdraw the question.
                withdraw(pending_ask, issue_id, f"the check became {result} ({code or why})")
                if result != "met":
                    # Evidence decided it (unmet: D5 `evid`), or the source changed so it is fixable again
                    # (`src`): either way the question is moot and the requirement is work again.
                    ledger.transition(bound, "open", "check_decided", point_id=point_id, summary=state.get("summary", ""),
                                      cause="evid" if result == "unmet" else "src", miss_status="not_applicable")
            if result != "met":
                row = check_once(result, requirement_id=rule_id, bound=bound, checked_state_ids=[subject],
                                 basis=basis, point_id=point_id, reason_code=code)
                if result == "unknown" and code in rule_table.UNDECIDABLE_CODES:
                    # Report D3: evidence cannot decide this (D2), so it leaves as one bounded question,
                    # asked once per (class, unknown check, basis version) — not once per generation.
                    class_key = digest([rule_id, subject, code])
                    basis_version = str(rules[rule_id].get("version", ""))  # the check's current version
                    ask_id = digest([class_key, basis_version])
                    if asks.get(ask_id, {}).get("state") in {None, "withdrawn"} and ask_room is not None and ask_room <= 0:
                        # CC-10: the episode's question budget is spent. The unknown stays open work, not
                        # a question; it is reported, and the next episode may ask it.
                        capped.append(f"{rule_id}: {subject}: question not asked, the episode's ask budget is spent")
                    elif asks.get(ask_id, {}).get("state") in {None, "withdrawn"}:
                        if ask_room is not None:
                            ask_room -= 1
                        if pending_ask and pending_ask != ask_id:
                            withdraw(pending_ask, issue_id, "superseded by a new question on the same requirement")
                        # Soul §3: a decision stands in for a check only where the check's basis is
                        # researcher judgment; for a mechanical check "establish satisfied" is not offered.
                        options = [o for o in ASK_OPTIONS if o != "satisfied" or rules[rule_id].get("check_basis") == "researcher"]
                        question = ledger.ask(ask_id, class_key=class_key, issue_ids=[issue_id], check_id=row,
                                              basis_version=basis_version, options=options, state="asked",
                                              detail={"summary": state.get("summary", ""), "why": why, "code": code,
                                                      "subject": subject, "rule_id": rule_id},
                                              point_id=point_id)
                        asks[ask_id] = question["payload"]
                        if state["status"] != "waiting" or pending_ask != ask_id:
                            # Handed to the researcher: still an unclosed requirement, now waiting (Soul §3).
                            ledger.transition(bound, "waiting", "asked", point_id=point_id,
                                              summary=state.get("summary", ""), reopen_trigger=f"answer:{ask_id}")
                            transitions.append(("asked", registration))
                continue
            check = ledger.check("met", requirement_id=rule_id, bound=bound, checked_state_ids=[subject],
                                 evidence_ids=[f"{subject}@{rule_table.subject_version(snapshot, subject) or ''}"],
                                 basis=basis, point_id=point_id)
            ledger.transition(bound, "resolved", "check_met", point_id=point_id, summary=state.get("summary", ""),
                              check_ids=[check["id"]])
            transitions.append(("resolved", registration))

        if transitions or any(changed.values()) or cursor.get("digest") != cursor_digest:
            ledger.decision_point(cutoff=now_iso(), point_id=point_id)
            ledger.observation(changed_state_ids=(changed["modified"] + changed["added"])[:20], state_count=len(versions),
                               source_version_vector=cursor_digest,
                               detail={"added": len(changed["added"]), "modified": len(changed["modified"]),
                                       "removed": len(changed["removed"]), "transitions": len(transitions),
                                       "point_id": point_id, "scope": frozen.to_dict(),
                                       "coverage": {k: v for k, v in coverage.items() if k != "uncovered_keys"}})
        spec = {"schema": SPEC_SCHEMA, "at": today.isoformat(), "purpose_version": rule_table.PURPOSE_VERSION,
                "rules": {rule_id: str(rule.get("version", "")) for rule_id, rule in rules.items()},
                "evaluated": sorted(executable), "scope_node": frozen.node, "members": sorted(frozen.members),
                "covered": sorted(covered), "sources": sources, "unattributed": sorted(unattributed)}
        ledger.write_cursor({"digest": cursor_digest, "versions": versions, "cache": cache, "at": today.isoformat(),
                             "point_id": point_id, "spec": spec})
        final_trajectory = ledger.trajectory()
        final_states = ledger.derive_states(final_trajectory)
        final_requirements = ledger.requirements(final_trajectory)
        unknowns = classify_unknowns(final_states["issues"], final_requirements, final_trajectory,
                                     ledger.asks(final_trajectory))
        return BoundaryResult(snapshot=snapshot, findings=findings, states=final_states,
                              requirements=final_requirements, changed=changed,
                              transitions=transitions,
                              problems=list(snapshot.problems) + rule_problems + scope_problems + problems_d5 + capped,
                              scope=frozen, coverage=coverage, suppressed=len(suppressed), placements=placements,
                              rule_versions=dict(spec["rules"]), coverage_domains=coverage_domains,
                              source_digest=cursor_digest, point_id=point_id, unknowns=unknowns)


# CC-11: the kinds of unknown, read off the ledger rather than off whatever this boundary happened to
# re-check. A requirement whose finding is still produced is not re-checked (Soul §3), so a map built
# during the boundary would lose its kind on the next one, and a later branch could overwrite it —
# the kind must be as stable as the record it is derived from. The three kinds never substitute for
# one another: a run whose observation never came is held by the Run axis, not by a check.
EVIDENCE_UNCLASSIFIED = "evidence_unclassified"  # unknown, but the record does not say which kind


def classify_unknowns(states: dict, requirements: dict, trajectory: list, asks: dict | None = None) -> dict:
    """requirement -> the kind of unknown that blocks it now, from its latest check and its pending
    question. The live blocker wins over the record: a requirement waiting on an unanswered question
    is an evidence unknown only the researcher can decide, whatever a later boundary said of its rule."""
    asks = asks if asks is not None else {}
    latest: dict = {}
    for row in trajectory:
        if row.get("kind") == "check":
            payload = row["payload"]
            latest[payload.get("binding", {}).get("issue_id", "")] = payload
    kinds = {}
    for issue_id, state in states.items():
        if state["status"] not in OPEN_STATUSES:
            continue
        trigger = state.get("reopen_trigger", "")
        if trigger.startswith("answer:") and asks.get(trigger[7:], {}).get("state") == "asked":
            kinds[issue_id] = "evidence_researcher"
            continue
        if str(requirements.get(issue_id, {}).get("binding", "")).startswith("spec:"):
            continue  # the D5 "previous spec cannot be recomputed" requirement has no rule and no domain
        check = latest.get(issue_id, {})
        code = check.get("reason_code", "")
        if check.get("result") == "not_evaluated" and code == "coverage_unevaluated":
            kinds[issue_id] = "coverage_unevaluated"
        elif check.get("result") == "unknown":
            # A record written before the kind was recorded, or a reason the table does not know, says
            # only "unknown": it is reported as unclassified rather than assumed to be fixable.
            kinds[issue_id] = ("evidence_researcher" if code in rule_table.UNDECIDABLE_CODES
                               else EVIDENCE_UNCLASSIFIED if code in {"", "other"} else "evidence_decidable")
    return kinds


def requirement_key(binding_key: str) -> str:
    """The scope key a requirement is about: judgment:, commitment: as is; an edge by its source node;
    a field confirmation by the commitment whose field it is (HJ-12)."""
    kind, _, rest = binding_key.partition(":")
    if kind == "edge":
        return rest.split("|", 1)[0]
    if kind == "field":
        return "commitment:" + rest.split("#", 1)[0]
    return binding_key


SPEC_SCHEMA = "researchos-boundary-spec-v1"
UNRECOMPUTABLE = "spec:previous-unrecomputable"
UNRECOMPUTABLE_ID = digest([UNRECOMPUTABLE])  # one identity; a later loss reopens it as a new generation


def source_versions(snapshot, versions: dict) -> dict:
    """sv: node and commitment versions plus judgment block hashes (node versions exclude judgments)."""
    found = dict(versions)
    found.update({f"judgment:{jid}": j.block_hash for jid, j in snapshot.judgments.items()})
    return found


class Attribution:
    """Report D5: the one cause of a transition that creates work, judged in the order
    initial → miss → scope → src → ver → evid → time against the spec the previous boundary
    froze (rules and versions, which rules ran, scope members, evaluated keys, source versions,
    and the findings it could not attribute).

    `miss` applies only to a first registration: a requirement already registered was not missed.
    It is recomputed from the frozen spec under the model's standing premise that Req is a pure
    function of the spec and that a boundary registers everything it derives in the same step:
      - inputs, rule and scope as they were: rerun the same rule at the previous date over the
        (identical) current inputs; the same occurrence there is a miss;
      - otherwise the previous boundary ran the same rule over the same key and registered nothing,
        which under the premise is the witness that the previous spec did not derive it.
    Without a frozen spec neither witness exists: `initial`, with miss unknown."""

    def __init__(self, previous, *, cold: bool, snapshot, config, rules, derived, sources, frozen, today: date):
        self.prev = previous if isinstance(previous, dict) and previous.get("schema") == SPEC_SCHEMA else None
        self.cold = cold
        self.snapshot, self.config, self.rules, self.derived = snapshot, config, rules, derived
        self.sources, self.frozen, self.today = sources, frozen, today.isoformat()
        self.members = set((self.prev or {}).get("members", []))
        self.covered = set((self.prev or {}).get("covered", []))
        self.dropped_before = set((self.prev or {}).get("unattributed", []))
        self.unknown = 0  # first registrations whose `miss` could not be judged
        self._before: dict = {}

    def _derived_before(self, rule_id: str) -> dict:
        if rule_id not in self._before:
            evaluator = (rule_table.evaluator_for(self.rules[rule_id]) or (None,))[0]
            then = date.fromisoformat(self.prev["at"])
            self._before[rule_id] = {f.issue_id: f for f in (evaluator(self.snapshot, self.config, self.rules[rule_id],
                                                                         self.derived, then) if evaluator else [])}
        return self._before[rule_id]

    def _moved(self, keys) -> bool:
        before = self.prev.get("sources", {})
        return any(before.get(key) != self.sources.get(key) for key in keys)

    def _new_to_scope(self, key: str) -> bool:
        return self.prev.get("scope_node") != self.frozen.node or \
            (key not in self.members and key in self.prev.get("sources", {}))

    def _later(self, finding, state: dict, registered: dict) -> tuple:
        """A new generation or a reopening of a registered requirement: `miss` does not apply."""
        subject = requirement_key(finding.binding_key)
        if self.prev and self._new_to_scope(subject):
            return "scope", "not_applicable"
        keys = {subject} | {key for key in finding.read_set if key in self.sources}
        if state.get("read_digest") != finding.read_digest or (self.prev and self._moved(keys)):
            return "src", "not_applicable"  # its declared read set, or a source it reads, moved
        if registered.get("rule_version", str(finding.rule_version)) != str(finding.rule_version):
            return "ver", "not_applicable"
        if rule_table.time_triggered(self.rules[finding.rule_id]) and (not self.prev or self.prev.get("at") != self.today):
            return "time", "not_applicable"
        return "", "not_applicable"

    def finding(self, finding, state: dict | None, registered: dict) -> tuple:
        """(cause, miss_status) for a finding about to open, reopen or refresh; cause "" = none holds."""
        if state is not None:
            return self._later(finding, state, registered)
        if not self.prev:
            if not self.cold:
                self.unknown += 1
            return "initial", "not_applicable" if self.cold else "unknown"
        rule_id, subject = finding.rule_id, requirement_key(finding.binding_key)
        keys = {subject} | {key for key in finding.read_set if key in self.sources or key in self.prev.get("sources", {})}
        same_rule = self.prev.get("rules", {}).get(rule_id) == str(finding.rule_version) \
            and self.prev.get("purpose_version") == rule_table.PURPOSE_VERSION and rule_id in self.prev.get("evaluated", [])
        before = self._derived_before(rule_id).get(finding.issue_id) if same_rule else None
        moved = self._moved(keys)
        if same_rule and not moved and subject in self.members and subject in self.covered \
                and before is not None and before.read_digest == finding.read_digest \
                and finding.issue_id not in self.dropped_before:
            return "miss", "checked"
        if self._new_to_scope(subject):
            return "scope", "checked"
        if moved or (before is not None and before.read_digest != finding.read_digest):
            return "src", "checked"
        if not same_rule or subject not in self.covered:
            return "ver", "checked"
        if before is None and rule_table.time_triggered(self.rules[rule_id]) and self.prev.get("at") != self.today:
            return "time", "checked"
        return "", "checked"

    def coverage(self, rule_id: str, rule: dict, keys, state: dict | None) -> tuple:
        """(cause, miss_status) for a coverage-unknown requirement over ``keys``."""
        if state is not None:  # registered before: its uncovered set moved
            if self.prev and any(self._new_to_scope(key) for key in keys):
                return "scope", "not_applicable"
            return "src", "not_applicable"
        if not self.prev:
            if not self.cold:
                self.unknown += 1
            return "initial", "not_applicable" if self.cold else "unknown"
        declared_before = self.prev.get("rules", {}).get(rule_id) == str(rule.get("version", ""))
        ran_before = rule_id in self.prev.get("evaluated", [])
        if declared_before and not ran_before and set(keys) <= self.members:
            return "miss", "checked"  # the previous spec already left this domain unevaluated
        if any(self._new_to_scope(key) for key in keys):
            return "scope", "checked"
        if self._moved(keys):
            return "src", "checked"
        return "ver", "checked"


EVIDENCE_KINDS = ("evidence_decidable", "evidence_researcher", EVIDENCE_UNCLASSIFIED)


def completion(states: dict, requirements: dict, frozen, *, today, placements: dict | None = None,
               frozen_rules: dict | None = None, open_at_start: dict | None = None,
               coverage_domains: dict | None = None, open_runs: list | None = None,
               unknowns: dict | None = None) -> dict:
    """Report D4 over a frozen scope. Done iff every in-scope registered requirement is resolved,
    cancelled, held for an answer, or waiting by a researcher decision with a trigger not yet due.
    Unclosed prior-specification, break-glass and in-scope coverage requirements exclude Done.
    No current producer registers waiting on an out-of-scope blocking dependency.
    Without a frozen scope nothing can be judged.

    Requirements outside the scope are split as D0 demands: keys owned by another scope, and keys
    whose ownership is undefined (the record is gone or has no location) — counted separately.

    CC-11: the kinds of unknown are reported apart and none substitutes for another. A run this
    episode dispatched whose observation never came is a run-observation unknown: the work may or
    may not have happened, so the episode is not Done — it is neither a question for the researcher
    nor a coverage unknown, and it is not silently read as "nothing happened"."""
    placements = placements or {}
    unknowns = unknowns or {}
    unfinished, held, waiting, outside, unowned, next_episode = [], [], [], [], [], []
    frozen_ok = frozen is not None and bool(frozen.members)
    for issue_id, state in sorted(states.items()):
        status = state["status"]
        if status not in OPEN_STATUSES:
            continue
        binding_key = requirements.get(issue_id, {}).get("binding", "")
        key = requirement_key(binding_key)
        place = placements.get(key)
        row = {"issue_id": issue_id, "short_id": issue_id[:10], "summary": state.get("summary", "")}
        registered = requirements.get(issue_id, {})
        rule_id = registered.get("rule_id", "")
        # P5: work that appeared during this session from a check it did not start with — a rule or a
        # version adopted meanwhile — belongs to the next episode. Work already open when the session
        # started is always this session's, whatever has happened to its rule since (a disabled or
        # rolled-back rule does not make open work disappear). Without a frozen Ver nothing is moved.
        new_here = open_at_start is not None and issue_id not in open_at_start
        generation_version = state.get("rule_version", "")
        # A confirmation of a judgment block or field written *in this session* is this session's
        # work (HJ-12): it comes from the write, not from a rule adopted meanwhile, so P5 does not move it.
        if frozen_rules and new_here and rule_id and rule_id != "confirm_judgment_change" \
                and not binding_key.startswith(("spec:", "field:")) and (
                rule_id not in frozen_rules or (generation_version and generation_version != frozen_rules[rule_id])):
            next_episode.append(row)
            continue
        # A closure whose receipt this machine cannot verify does not take its open work out of Done.
        narrowed = frozen_ok and bool(getattr(frozen, "narrowed_by", ""))
        unverified = frozen_ok and place is not None and place.closed and not place.verified \
            and scope_axis.contains(frozen.node, place.scope) and (not narrowed or key in frozen)
        coverage_here = binding_key.startswith("coverage:") and (
            not narrowed or (coverage_domains or {}).get(issue_id) is None
            or bool((coverage_domains or {}).get(issue_id, frozenset()) & frozen.members))
        in_scope = coverage_here or binding_key.startswith("spec:") or (frozen_ok and key in frozen) or unverified
        if not in_scope:
            (outside if place is not None and place.scope else unowned).append(row)
            continue
        trigger = state.get("reopen_trigger", "")
        decision = state.get("decision", {})
        researcher_defer = decision.get("permission_state") == "researcher_decision" and (
            (status == "deferred" and decision.get("operation") == "defer"
             and decision.get("detail", {}).get("decision_evidence") == "terminal_confirmation"
             and decision.get("detail", {}).get("until") == state.get("deferred_until"))
            or (status == "waiting" and decision.get("operation") == "ask"
                and decision.get("detail", {}).get("how") in {"answer:defer", "answer:narrow"}))
        if (binding_key.startswith(("spec:", "field:")) or rule_id == "confirm_judgment_change"
                or coverage_here or unknowns.get(issue_id) == "coverage_unevaluated"):
            unfinished.append(row)
        elif status == "open" or (status == "waiting" and not trigger):
            unfinished.append(row)
        elif status == "waiting":
            due = trigger.startswith("date:") and trigger[5:] <= today.isoformat()
            (unfinished if due else held if trigger.startswith("answer:")
             else waiting if researcher_defer else unfinished).append(dict(row, trigger=trigger))
        else:  # deferred: its date is the trigger; a date that has come is work again
            until = state.get("deferred_until", "")
            (waiting if researcher_defer and until and until > today.isoformat() else unfinished).append(
                dict(row, trigger=f"date:{until}"))
    runs_unknown = sorted(open_runs or [])
    # Two axes, counted separately. The evidence kinds do not depend on where the requirement sits: a
    # question about a record whose ownership is undefined is still an evidence unknown, and is also
    # the second kind of coverage unknown. The coverage triple, in contrast, must be a partition (D0):
    # a requirement outside the scope is counted there and not again as unevaluated. Work assigned to
    # the next episode (P5) is not this episode's unknown and is left out of both.
    mine = {row["issue_id"] for row in unfinished + held + waiting}
    elsewhere = {row["issue_id"] for row in outside + unowned}
    kinds = {kind: sum(1 for issue_id in mine | elsewhere if unknowns.get(issue_id) == kind)
             for kind in EVIDENCE_KINDS}
    kinds.update({"coverage_unevaluated": sum(1 for issue_id in mine
                                              if unknowns.get(issue_id) == "coverage_unevaluated"),
                  "run_observation": len(runs_unknown), "own_undefined": len(unowned),
                  "out_of_scope": len(outside)})
    return {"done": frozen_ok and not unfinished and not runs_unknown, "scope_frozen": frozen_ok,
            "unfinished": unfinished, "held": held, "waiting": waiting, "out_of_scope_open": len(outside),
            "unowned_open": len(unowned), "unowned": unowned, "next_episode": next_episode,
            "runs_unknown": runs_unknown, "unknown_kinds": kinds}


DEFAULT_BOUNDARY_BUDGET = 200  # β^bnd is mandatory (report P2): without a declared one, this bounds the episode
BUDGET_COMPONENTS = ("boundaries", "asks", "reopens")
# A requirement that becomes work again: a new generation after closure, a deferral whose date came,
# a question made moot by evidence or a source change. "refreshed" keeps an open requirement open.
REOPEN_REASONS = {"reopened", "reopened:time", "check_decided"}


def declared_budget(config: dict) -> dict:
    """β_ε from config `episode_budget` (boundaries, asks, reopens: positive integers). The boundary
    count is mandatory; when it is not declared the kernel's default bounds the episode and says so.
    A value that is not a positive integer is not used; `budget_problems` reports it."""
    declared = {key: value for key, value in (config.get("episode_budget") or {}).items()
                if key in BUDGET_COMPONENTS and isinstance(value, int) and not isinstance(value, bool) and value > 0}
    if "boundaries" not in declared:
        declared = {"boundaries": DEFAULT_BOUNDARY_BUDGET, **declared, "boundaries_source": "kernel_default"}
    return declared


def budget_problems(config: dict) -> list:
    raw = config.get("episode_budget")
    if raw is None:
        return []
    if not isinstance(raw, dict):
        return ["episode_budget: not an object; ignored"]
    used = declared_budget(config)
    return [f"episode_budget.{key} = {value!r}: ignored ("
            + ("unknown component" if key not in BUDGET_COMPONENTS else "must be a positive integer") + ")"
            for key, value in raw.items() if used.get(key) != value or key == "boundaries_source"]


def frozen_budget(spec: dict | None) -> dict:
    """The budget a session froze in its spec. A session frozen before β^bnd was mandatory still has
    one: the kernel default, marked as such. `today` and `close` both read this, so they cannot disagree."""
    frozen = (spec or {}).get("budget") or {}
    budget = {key: frozen[key] for key in BUDGET_COMPONENTS if isinstance(frozen.get(key), int)}
    if "boundaries" not in budget:
        return {"boundaries": DEFAULT_BOUNDARY_BUDGET, **budget, "boundaries_source": "kernel_default"}
    return dict(budget, **({"boundaries_source": frozen["boundaries_source"]} if frozen.get("boundaries_source") else {}))


def budget_spent(ledger: Ledger, session_id: str, members: set) -> dict:
    """spent_t for one session, from the ledger rows attributed to it, never from wall-clock windows:
    its decision boundaries (rows naming it), and the questions asked and requirements reopened at
    those boundaries. A narrowed session (``members``: its frozen scope) is charged only for
    requirements inside it; an empty set means the whole scope."""
    points = [row for row in ledger.records("decision_points") if row.get("episode_id") == session_id]
    at_points = {row.get("context_id") for row in points if row.get("context_id")}
    requirements = ledger.requirements()

    def charged(issue_ids) -> bool:
        return not members or any(requirement_key(requirements.get(issue, {}).get("binding", "")) in members
                                  for issue in issue_ids)
    asks = reopens = 0
    for row in ledger.trajectory():
        if row.get("point_id") not in at_points:
            continue
        payload = row.get("payload", {})
        if row.get("kind") == "ask" and payload.get("state") == "asked" and charged(payload.get("issue_ids", [])):
            asks += 1
        elif (row.get("kind") == "issue_transition" and payload.get("to") == "open"
              and payload.get("reason") in REOPEN_REASONS and charged([payload.get("issue_id", "")])):
            reopens += 1
    return {"boundaries": len(points), "asks": asks, "reopens": reopens}


def exhausted(budget: dict, spent: dict) -> list:
    """Report P2: Exhausted(β_ε, t) := ∨_i [spent_t^i ≥ β_ε^i]; the components that are spent."""
    return sorted(key for key, limit in (budget or {}).items()
                  if isinstance(limit, int) and not isinstance(limit, bool) and spent.get(key, 0) >= limit)


def outcome(report: dict, *, stopped_by_researcher: bool, exhausted_components: list | None = None) -> str:
    """Out_ε. Done wins; otherwise a spent budget stops the episode before the researcher does."""
    if report["done"]:
        return "complete_with_held" if report["held"] or report["waiting"] else "complete"
    if exhausted_components:
        return "budget_stopped"
    return "human_stopped" if stopped_by_researcher else ""
