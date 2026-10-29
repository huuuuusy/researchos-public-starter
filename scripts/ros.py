#!/usr/bin/env python3
"""ros: the ResearchOS session scheduler.

    ros today [--for <commitment>] [--all]   start of a session: what changed, what needs you
    ros close [--for <commitment> | --session <id>]   end of a session: which judgment-class changes to keep
    ros propose judgment --file F --target T [--session <id>]
    ros propose episode-close --target <episode.md> --reason R
    ros propose rule --file <revision.json> [--reason R]   a rule revision, admitted only at the terminal
    ros admit <candidate> | --confirm <judgment> | --reconfirm <judgment> [--commit]
    ros admit --rollback <transaction>  undo one admitted write
    ros receipt <closure receipt id>  look up one episode closure receipt
    ros attend <commitment> today|tomorrow|date YYYY-MM-DD|park [--review D]|complete-step|undo
    ros answer <question> satisfied|unsatisfied|narrow|cancel --reason R|defer --until D|--trigger E
    ros decide <requirement> defer --until YYYY-MM-DD | cancel --reason R | reopen | confirm
    ros run judgment --target T --executor provider:<id>|copy_packet [--instruction I] [--session <id>]
    ros collect <run> --file <answer> | --abandon --reason R
    ros state <commitment>           Q E J B N of one commitment
    ros context <commitment|card>    bounded context pack for the session model
    ros rules [--check]              rule table and open requirements per rule

Most commands first run one boundary; `receipt`, `propose rule`, `admit --rollback`, `collect --abandon`
and the public starter's `attend` do not. Nothing runs in the background.
Two things are called an episode: a session in the ledger (`today` opens one, `close` ends it;
a rule revision's source_episodes name them) and an episode card in Markdown, which
`propose episode-close` closes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import date, datetime
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from researchos_adapters.context_pack import build_context_pack  # noqa: E402
from researchos_adapters.dispatch import (launched_nothing, provider_for, run_ledger, run_lifecycle,  # noqa: E402
                                          run_record)
from researchos_adapters.markdown_repo import build_snapshot, load_config, portfolio_problems  # noqa: E402
from researchos_adapters.writeback import (WritebackError, closed_episode, episode_state_of,  # noqa: E402
                                          landed as landed_block, pin_basis, plan_admit, plan_episode_close, plan_reconfirm)
from researchos_kernel import KERNEL_VERSION  # noqa: E402
from researchos_kernel.boundary import (BUDGET_COMPONENTS, budget_problems, budget_spent,  # noqa: E402
                                       completion, declared_budget, exhausted, frozen_budget, ledger_for,
                                       outcome, run_boundary)
from researchos_kernel.judgments import parse_judgments  # noqa: E402
from researchos_kernel.atomic_files import atomic_write_text  # noqa: E402
from researchos_kernel.ledger import (OPEN_STATUSES, SCOPE_INTENT, binding, digest, landed_or_undone,  # noqa: E402
                                     now_iso, requirement_binding)
from researchos_kernel.messages import language, t  # noqa: E402
from researchos_kernel.admission_state import initial_admission_state, transition_admission_state  # noqa: E402
from researchos_kernel.candidate_envelope import normalize_candidate_envelope  # noqa: E402
from researchos_adapters.filesystem_staging import (FilesystemStagingError, begin_canonical_staging,  # noqa: E402
                                                  rollback_artifact_mutation)
from researchos_kernel.rules import load_rules, write_class  # noqa: E402
from researchos_kernel import scope as scope_axis  # noqa: E402
from researchos_kernel.triage import triage  # noqa: E402

SESSION_KEEP = 20


class Context:
    def __init__(self, root: Path, today: date, lang: str = ""):
        self.root = root
        self.today = today
        self.config = load_config(root)
        self.lang = language(lang or self.config.get("language", "zh-CN"))
        self.config["language"] = self.lang
        # Fail closed (Soul §5): only a config that says "private" gets admission and dispatch; a missing,
        # misspelled or other scope runs as the copy-only public starter.
        self.runtime_scope = "private" if self.config.get("runtime_scope") == "private" else "public_starter"
        self.ledger = ledger_for(root, self.config)
        self.runtime_dir = root / self.config["runtime_dir"]
        self._result = None
        self.opening_budget = None  # set by `today` when its boundary opens a new session

    def boundary(self):
        if self._result is None:
            live = [sid for sid in _open_today(self) if not exhausted(*_session_account(self, sid))]
            self._result = run_boundary(self.root, self.config, snapshot_builder=build_snapshot, today=self.today,
                                        runtime_scope=self.runtime_scope, install_root=ROOT,
                                        ask_room=_ask_room(self, self.opening_budget))
            _record_round(self, self._result, live)  # CC-10: every boundary spends one bnd of each live session
        return self._result

    def refresh(self):
        self._result = None
        return self.boundary()

    def write_class(self) -> dict:
        return write_class(self.root, ROOT)["judgment"]


def emit(args, data: dict, text: str) -> int:
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else text)
    return 0


def find_issue(ctx: Context, prefix: str) -> str:
    matches = [issue for issue in ctx.boundary().states["issues"] if issue.startswith(prefix)]
    if len(matches) != 1:
        raise SystemExit(f"requirement id {prefix!r} matches {len(matches)} requirements")
    return matches[0]


# -- today ---------------------------------------------------------------------------
def session_snapshot(result, scope=None) -> dict:
    """The session's starting point. It also carries Sc_ε by extension, frozen at `today`, so that
    `close` judges completion against the scope the session started with (report D4, (H7))."""
    snapshot = result.snapshot
    return {
        "files": {ref: node.file_sha for ref, node in snapshot.nodes.items()},
        "judgments": {jid: j.block_hash for jid, j in snapshot.judgments.items()},
        "commitments": {cid: dict(c.fields) for cid, c in snapshot.commitments.items()},
        "scope": (scope or result.scope).to_dict() if (scope or result.scope) else {},
        "scope_members": sorted((scope or result.scope).members) if (scope or result.scope) else [],
        "rules": dict(getattr(result, "rule_versions", {}) or {}),  # Ver_ε, frozen with the scope
        # what was already open when the session started (issue -> generation): always this session's
        "open_requirements": {issue: state["generation"] for issue, state in result.states["issues"].items()
                              if state["status"] in OPEN_STATUSES},
    }


def _change_rows(changed: dict, snapshot) -> list:
    """Describe observed membership/version changes, not a body diff or an approval."""
    return [{"ref": ref, "title": snapshot.title_of(ref), "change": change}
            for change in ("added", "modified", "removed") for ref in sorted(changed[change])]


def _boundary_change_details(result) -> dict:
    rows = _change_rows(result.changed, result.snapshot)
    source_commitments = {}
    for cid, commitment in result.snapshot.commitments.items():
        ref, _ = result.snapshot.resolve(commitment.get("source_path"))
        if ref:
            source_commitments.setdefault(ref, set()).add(cid)
    for row in rows:
        # Current related requirements are not necessarily CAUSED by this boundary's change.
        row["related_requirements"] = [
            {"issue_id": issue, "summary": finding.summary, "status": state["status"]}
            for issue, finding in sorted(result.findings.items())
            if (row["ref"] in finding.read_set or
                row["ref"] == f"commitment:{finding.commitment_id}" or
                finding.commitment_id in source_commitments.get(row["ref"], set()))
            and (state := result.states["issues"].get(issue, {})).get("status") in OPEN_STATUSES]
    return {"baseline": "previous_boundary", "scope": "observed_graph", "items": rows}


def _render_changes(lang: str, rows: list) -> list:
    lines = []
    for row in rows:
        label = row["ref"] if row["title"] == row["ref"] else f"{row['title']} ({row['ref']})"
        lines.append("  · " + t(lang, "change.row", change=t(lang, 'change.' + row['change']), label=label))
        lines += ["      " + t(lang, "change.related", id=req["issue_id"][:10],
                              status=req["status"], summary=req["summary"])
                  for req in row.get("related_requirements", [])]
    return lines


def _episode_spec(ctx: "Context", result, intent: str, scope_detail: dict) -> dict:
    """Φ_ε as `today` would freeze it now (CC-6), built by the TaskEnvelope owner."""
    from researchos_kernel.rules import PURPOSE_VERSION, WRITE_CLASS_RELATIVE, _locate
    from researchos_kernel.task_envelope import build_episode_spec
    rules, _ = load_rules(ctx.root, ctx.runtime_scope, ROOT)
    running = getattr(result, "rule_versions", {}) or {rule_id: rule.get("version", "") for rule_id, rule in rules.items()}
    # The raw bytes, not the parsed contract: a running session's frozen digest must stay comparable.
    contract = _locate(ctx.root, ROOT, WRITE_CLASS_RELATIVE)
    write_class_digest = hashlib.sha256(contract.read_bytes()).hexdigest()  # both the fact and judgment classes
    return build_episode_spec(
        purpose={"intent": intent, "purpose_version": PURPOSE_VERSION},
        context=intent, scope=scope_detail,
        rules=running,
        preserve=[item for rule_id, rule in rules.items() if rule_id in running for item in rule.get("preserve", [])],
        authorization={"fact_writes": "direct_and_recorded", "judgment_writes": "candidate_then_admission",
                       "rule_writes": "researcher_terminal_only", "egress": "context_receipt",
                       "write_class_digest": write_class_digest, "runtime_scope": ctx.runtime_scope},
        budget=declared_budget(ctx.config),
        ask_cap={"asks": declared_budget(ctx.config)["asks"]} if "asks" in declared_budget(ctx.config)
        else {"declared": False},
        source_version_digest=getattr(result, "source_digest", "") or hashlib.sha256(json.dumps(
            result.snapshot.version_map(), sort_keys=True).encode("utf-8")).hexdigest(),
        cutoff=now_iso(), decision_point=getattr(result, "point_id", ""))


def _unknowns_line(lang: str, report: dict) -> str:
    """CC-11: the three unknowns side by side, each with its own count; none stands in for another."""
    kinds = report.get("unknown_kinds", {})
    return t(lang, "unknowns.line", decidable=kinds.get("evidence_decidable", 0),
             researcher=kinds.get("evidence_researcher", 0),
             unclassified=kinds.get("evidence_unclassified", 0), run=kinds.get("run_observation", 0),
             uneval=kinds.get("coverage_unevaluated", 0), unowned=kinds.get("own_undefined", 0),
             outside=kinds.get("out_of_scope", 0))


def _budget_line(lang: str, budget: dict, spent: dict, spent_out: list) -> str:
    parts = ", ".join(f"{key} {spent.get(key, 0)}/{budget[key]}" for key in BUDGET_COMPONENTS if key in budget)
    if budget.get("boundaries_source") == "kernel_default":
        parts += " (boundaries: kernel default)"
    tail = t(lang, "budget.exhausted", parts=", ".join(spent_out)) if spent_out else ""
    return t(lang, "budget.line", parts=parts, exhausted=tail)


def _record_round(ctx: "Context", result, session_ids) -> None:
    """One boundary evaluated while a session is open is one of its decision boundaries, whether or
    not anything changed (waiting also spends β^bnd). The row names the session and, as its context,
    the kernel's point, so the questions and reopenings of that boundary are attributed to it."""
    if not session_ids:
        return
    with ctx.ledger.lock():
        for sid in session_ids:
            ctx.ledger.decision_point(cutoff=now_iso(), episode_id=sid, context_id=getattr(result, "point_id", ""))


def _session_account(ctx: "Context", session_id: str) -> tuple:
    """(β_ε, spent_t) of one session: the budget it froze and what the ledger charged to it (a narrowed
    session only for its own scope). `today`, `close`, the ask room and dispatch all read this."""
    spec = ctx.ledger.session_start(session_id).get("detail", {}).get("spec")
    return frozen_budget(spec), budget_spent(ctx.ledger, session_id, _session_members(ctx, session_id))


def _open_today(ctx: "Context", known: dict | None = None) -> list:
    """Sessions opened today and not ended, oldest first (from ``known`` when the caller has read them)."""
    known = ctx.ledger.sessions() if known is None else known
    return [sid for sid, row in known.items() if not row["ended"] and row["day"] == ctx.today.isoformat()]


def _ask_room(ctx: "Context", opening: dict | None = None) -> int | None:
    """How many new questions may still be asked: the smallest room of the sessions open today (an
    exhausted session has none), and of the session `today` is about to open (``opening``, its
    declared budget), since that opening boundary is already the new session's. None: no cap."""
    rooms = []
    for sid in _open_today(ctx):
        budget, spent = _session_account(ctx, sid)
        if exhausted(budget, spent):
            rooms.append(0)
        elif isinstance(budget.get("asks"), int):
            rooms.append(max(0, budget["asks"] - spent["asks"]))
    if opening and isinstance(opening.get("asks"), int):
        rooms.append(opening["asks"])
    return min(rooms) if rooms else None


def _session_start(ctx: "Context", session_id: str) -> dict | None:
    """The start snapshot `today` cached for a session; None when that cache is gone or unreadable."""
    try:
        return json.loads((ctx.runtime_dir / "sessions" / f"{session_id}.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _session_members(ctx: "Context", session_id: str) -> set:
    cached = _session_start(ctx, session_id) or {}
    return set(cached.get("scope_members", [])) if cached.get("scope", {}).get("narrowed_by") else set()


FIELD_CONFIRMATION = "field_confirmation"


def _register_field_confirmations(ctx: "Context", field_changes: list) -> list:
    """HJ-12: a judgment-class commitment field written directly leaves a requirement that stays open
    until the researcher confirms it. Listing the change once at close is not confirmation — the same
    rule as a judgment block written without admission (HJ-8); only the object differs. The record
    carries the value that was written, so a later edit is a new generation and opens it again."""
    from researchos_kernel.rules import PURPOSE_VERSION
    registered = []
    states = ctx.boundary().states["issues"]
    registry = ctx.boundary().requirements
    with ctx.ledger.lock():
        for row in field_changes:
            subject = f"field:{row['commitment_id']}#{row['field']}"
            issue_id = digest([subject, PURPOSE_VERSION])
            # The read set names the object this requirement is about and the value that was written,
            # so a later edit is a new generation and the row says what was confirmed.
            read_set = {f"commitment:{row['commitment_id']}": digest(row["after"]), "field": row["field"]}
            state = states.get(issue_id)
            if state and state["status"] in OPEN_STATUSES and state["read_digest"] == digest(read_set):
                continue  # the same unconfirmed value: one requirement, not one per session
            bound = binding(issue_id, (state or {}).get("generation", 0) + 1,
                            purpose_version=PURPOSE_VERSION, source_version_vector=digest(read_set))
            ctx.ledger.transition(
                bound, "open", "opened" if state is None else "refreshed", requirement=None if issue_id in registry else {
                    "rule_id": FIELD_CONFIRMATION, "rule_version": KERNEL_VERSION, "purpose_version": PURPOSE_VERSION,
                    "binding": subject, "commitment_id": row["commitment_id"], "kind": "maintenance",
                    "executor": "human", "resolver": "human"},
                summary=t(ctx.lang, "field.unconfirmed" if row["before"] else "field.written",
                          commitment=row["commitment_id"], field=row["field"],
                          after=str(row["after"])[:80] or t(ctx.lang, "empty")),
                read_set=read_set, cause="src", miss_status="not_applicable")
            registered.append(issue_id)
    return registered


def session_completion(ctx: "Context", result, started: dict, session_id: str) -> dict:
    """Report D4 for one session, from what it froze at `today` (H7, P5). `today` and `close` use
    this one function, so they cannot disagree about what counts."""
    frozen = scope_axis.restore(started.get("scope", {}), started.get("scope_members", [])) \
        if started.get("scope_members") is not None and "scope" in started else None
    return completion(result.states["issues"], result.requirements, frozen, today=ctx.today,
                      placements=result.placements, frozen_rules=started.get("rules"),
                      open_at_start=started.get("open_requirements"),
                      coverage_domains=getattr(result, "coverage_domains", {}),
                      open_runs=ctx.ledger.unresolved_runs(session_id),
                      unknowns=getattr(result, "unknowns", {}))


PROVIDER = "research_portfolio"
ATTENTION_OWNER = ROOT / "scripts" / "researchos_server" / "attention_schedule_store.py"


def _attention(ctx: Context, snapshot) -> dict:
    """commitment id -> its attention projection, read from the attention owner (Attention Kernel §6).

    The public starter ships no attention owner (the schedule never enters the public package), so
    there every commitment reads as unscheduled — invested ones still surface as today judgments."""
    if ctx.runtime_scope == "public_starter" or not ATTENTION_OWNER.is_file():
        return {}  # this installation ships no attention owner; a broken one below still fails loudly
    from researchos_server.attention_schedule_store import project_items
    return project_items(ctx.root, PROVIDER, {cid: dict(c.fields) for cid, c in snapshot.commitments.items()},
                         today=ctx.today)


def _intent(for_commitment: str | None) -> str:
    """A session's one bounded intent: a commitment, or the whole frozen scope."""
    return f"commitment:{for_commitment}" if for_commitment else SCOPE_INTENT


def _intent_of_target(ctx: Context, target: str) -> str:
    """A card that is a commitment's source stands for that commitment when matching intents."""
    if target.startswith("commitment:"):
        return target
    from researchos_adapters.markdown_repo import parse_portfolio
    portfolio = ctx.root / ctx.config.get("portfolio", "")
    try:
        commitments = parse_portfolio(portfolio.read_text(encoding="utf-8")) if portfolio.is_file() else {}
    except OSError:
        commitments = {}
    owners = [cid for cid, c in commitments.items() if c.get("source_path") == target]
    return f"commitment:{owners[0]}" if len(owners) == 1 else target


def _session_for(ctx: Context, target: str, explicit: str = "", *, required: bool = True) -> str:
    """The open session of today that a command belongs to. An explicit --session must be one of them;
    otherwise the session whose intent is exactly the target, else the one whole-scope session.
    Two candidates are refused rather than guessed: guessing is how one session overwrites another."""
    known = ctx.ledger.sessions()
    today = {sid: known[sid] for sid in _open_today(ctx, known)}
    if explicit:
        if explicit not in today:
            raise SystemExit(f"{explicit} is not a session open today")
        return explicit
    intent = _intent_of_target(ctx, target)
    exact = [sid for sid, row in today.items() if row["intent"] == intent]
    inside = [sid for sid in today if sid not in exact and target and target in _session_members(ctx, sid)]
    whole = [sid for sid, row in today.items() if row["intent"] == SCOPE_INTENT]
    for group in (exact, inside, whole):
        if len(group) == 1:
            return group[0]
        if len(group) > 1:
            raise SystemExit("several sessions are open for this; name one with --session: " + ", ".join(group))
    if required:
        earlier = [sid for sid, row in known.items() if not row["ended"] and row["day"] != ctx.today.isoformat()]
        hint = f" (sessions from earlier days are still open: {', '.join(earlier[-3:])}; close them with " \
               "`ros close --session <id>`)" if earlier else ""
        raise SystemExit("a run needs a session opened today for this target: run `ros today`"
                         + (f" or `ros today --for {intent.split(':', 1)[1]}`" if intent.startswith("commitment:") else "")
                         + hint)
    return ""


def _session_to_close(ctx: Context, args) -> str:
    """Only a session opened today is closed by default; an earlier day's must be named, and a session
    ends once. Nothing is closed by guessing."""
    known = ctx.ledger.sessions()
    if args.session:
        if args.for_commitment:
            raise SystemExit("name the session with --session or --for, not both")
        if args.session not in known:
            raise SystemExit(f"no session {args.session}")
        if known[args.session]["ended"]:
            raise SystemExit(f"session {args.session} has already ended")
        return args.session
    pool = _open_today(ctx, known)
    if args.for_commitment:
        pool = [sid for sid in pool if known[sid]["intent"] == _intent(args.for_commitment)]
    if not pool:
        earlier = [sid for sid, row in known.items() if not row["ended"]]
        raise SystemExit("no session open today" + (
            "; sessions from earlier days must be named: " + ", ".join(
                f"ros close --session {sid}" for sid in earlier[-3:]) if earlier else "; run `ros today` first"))
    if len(pool) > 1:
        raise SystemExit("several sessions are open; name one with --session or --for: " + ", ".join(
            f"{sid} ({known[sid]['intent']})" for sid in pool))
    return pool[0]


def cmd_today(ctx: Context, args) -> int:
    intent = _intent(args.for_commitment)
    known = ctx.ledger.sessions()
    if not any(known[sid]["intent"] == intent for sid in _open_today(ctx, known)):
        ctx.opening_budget = declared_budget(ctx.config)  # this boundary is the new session's first (CC-10)
    result = ctx.boundary()
    view = triage(result, ctx.config, ctx.today, only_commitment=args.for_commitment or "",
                  attention=_attention(ctx, result.snapshot))
    view["questions"] = _open_questions(ctx, result, args.for_commitment or "")
    # The date part is the session's day (the real date unless --today pins one), so the id and its day agree.
    session_id = f"{ctx.today:%Y%m%d}T{datetime.now():%H%M%S}-{uuid.uuid4().hex[:4]}"
    sessions = ctx.runtime_dir / "sessions"
    # The Session axis is owned by the ledger's episodes. One session holds one intent (Attention §4.3):
    # a later `today` the same day with the same intent continues it and keeps its starting point and
    # frozen scope (H7); a different intent opens its own session and leaves the other untouched.
    if args.for_commitment and args.for_commitment not in result.snapshot.commitments:
        if args.for_commitment in getattr(result.snapshot, "ambiguous_commitments", frozenset()):
            raise SystemExit(f"commitment {args.for_commitment} is declared more than once in the portfolio; "
                             "make its id unique before focusing a session on it")
        raise SystemExit(f"unknown commitment: {args.for_commitment}")
    # Sc_ε for this session's intent: the frozen scope, or the part of it that belongs to one commitment.
    scope = result.scope
    if scope and args.for_commitment:
        scope = scope_axis.narrow_to_commitment(scope, result.snapshot, args.for_commitment)
    scope_detail = scope.to_dict() if scope else {}
    spec = _episode_spec(ctx, result, intent, scope_detail)
    coverage = {key: value for key, value in result.coverage.items() if key != "uncovered_keys"}
    with ctx.ledger.lock():  # look up and open under one lock: two `today` calls cannot both open one intent
        known = ctx.ledger.sessions()
        same = [sid for sid in _open_today(ctx, known) if known[sid]["intent"] == intent]
        continuing = bool(same)
        if continuing:
            session_id = same[-1]
        else:
            atomic_write_text(sessions / f"{session_id}.json",
                         json.dumps(dict(session_snapshot(result, scope), scope=scope_detail), ensure_ascii=False))
            ctx.ledger.episode(session_id, start=now_iso(), object_ids=[intent] if intent != SCOPE_INTENT else [],
                               detail={"open": view["total_open"], "scope": scope_detail, "coverage": coverage,
                                       "day": ctx.today.isoformat(), "spec": spec})
    if not continuing:
        _record_round(ctx, result, [session_id])  # the opening boundary is this session's first
    start = ctx.ledger.session_start(session_id).get("detail", {})
    frozen_spec = start.get("spec") or {}
    from researchos_kernel.task_envelope import episode_spec_changes
    spec_changes = episode_spec_changes(frozen_spec, spec) if frozen_spec else []
    known = ctx.ledger.sessions()
    stale = [sid for sid, row in known.items() if not row["ended"] and row["day"] != ctx.today.isoformat()]
    live = {sid for sid, row in known.items() if not row["ended"]} | {session_id}
    cached = sorted(sessions.glob("*.json"), key=lambda p: (p.stat().st_mtime_ns, p.name))
    for old in [p for p in cached if p.stem not in live][:-SESSION_KEEP or None]:
        old.unlink()  # the start snapshots are a cache; an open session's is never pruned
    view["completion"] = session_completion(ctx, result, _session_start(ctx, session_id) or {}, session_id)
    view["waiting_on_trigger"] = _waiting_on_triggers(result, args.for_commitment or "")
    budget_now, spent_now = _session_account(ctx, session_id)
    data = {"session_id": session_id, "kernel_version": KERNEL_VERSION,
            "changed": {k: len(v) for k, v in result.changed.items()},
            "change_details": _boundary_change_details(result),
            "transitions": len(result.transitions), "stale_sessions": stale,
            "budget": {"limits": budget_now, "spent": spent_now, "exhausted": exhausted(budget_now, spent_now),
                       "problems": budget_problems(ctx.config)},
            "spec": frozen_spec or None, "spec_proposed": spec,
            "spec_changes_pending": spec_changes if continuing else [],
            "portfolio_problems": portfolio_problems(ctx.root, ctx.config, result.snapshot.commitments), **view}
    shown = frozen_spec.get("scope_declaration") and start.get("scope") or scope_detail
    return emit(args, data, _render_today(ctx, data, shown=shown, coverage=coverage, continuing=continuing,
                                          problems=len(result.problems), show_all=args.all))


def _render_today(ctx: Context, data: dict, *, shown: dict, coverage: dict, continuing: bool, problems: int,
                  show_all: bool) -> str:
    """The text of `today`, from the same data its --json prints (one boundary, one emit)."""
    L = ctx.lang
    changed, status, budget = data["changed"], data["completion"], data["budget"]
    lines = [t(L, "today.header", date=ctx.today.isoformat(), session=data["session_id"]),
             t(L, "today.since", added=changed["added"], modified=changed["modified"],
               removed=changed["removed"], transitions=data["transitions"], open=data["total_open"]), ""]
    change_rows = data["change_details"]["items"]
    lines.append(t(L, "today.changes"))
    lines += _render_changes(L, change_rows if show_all else change_rows[:10])
    if not change_rows:
        lines.append("  " + t(L, "none"))
    if not show_all and len(change_rows) > 10:
        lines.append("  " + t(L, "change.omitted", n=len(change_rows) - 10))
    lines.append("")
    if shown:
        # 完成报告要能核对范围：归属节点、跨范围键数、两类覆盖未知及其分母（覆盖计数是全范围的当前值）。
        lines.append(t(L, "today.scope", node=shown["scope_node"], members=shown["scope_member_count"],
                       cross=len(shown["cross_scope_keys"]),
                       uncovered=coverage.get("coverage_unknown_in_scope", 0),
                       unowned=coverage.get("coverage_unknown_unowned", 0),
                       evaluated=coverage.get("evaluated_match_count", 0),
                       domain=coverage.get("in_scope_match_count", 0)))
        lines.append("")
    if not status.get("scope_frozen"):
        lines.append("  ! " + t(L, "close.unfrozen"))
    if continuing and not data["spec"]:
        lines.append("  ! " + t(L, "today.spec_none"))
    elif data["spec_changes_pending"]:
        # CC-6: the running episode keeps the spec it froze; a changed spec is the next episode's.
        lines.append("  ! " + t(L, "today.spec_changed", parts=", ".join(data["spec_changes_pending"])))
    lines.append(t(L, "today.completion", unfinished=len(status["unfinished"]), held=len(status["held"]),
                   waiting=len(status["waiting"]), outside=status["out_of_scope_open"], unowned=status["unowned_open"]))
    lines.append("  " + _unknowns_line(L, status))
    lines += ["  ↻ " + t(L, "unknowns.run", run=run_id) for run_id in status["runs_unknown"]]
    if (shown or {}).get("narrowed_by"):
        lines.append("  " + t(L, "today.narrowed", intent=shown["narrowed_by"]))
    lines.append("  " + _budget_line(L, budget["limits"], budget["spent"], budget["exhausted"]))
    if budget["exhausted"]:
        # CC-10: the episode has stopped. It asks nothing more, dispatches nothing, and closes as budget_stopped.
        lines.append("  ! " + t(L, "budget.stopped", session=data["session_id"]))
    lines += ["  ! " + problem for problem in budget["problems"]]
    lines.append("")
    if rows := data["portfolio_problems"]:  # a missing portfolio file is one line, without the header
        head = [] if rows[0]["field"] == "portfolio" else [
            t(L, "today.portfolio_problems", n=len(rows), path=ctx.config["portfolio"])]
        lines += head + ["  ! " + row["text"] for row in rows] + [""]

    def group(row: dict) -> list:
        return _render_group(L, row, marker=t(L, f"attention.{row['attention_state']}"))

    def question(row: dict) -> list:
        return [f"  ? [{row['short_id']}] {row['summary']}", "      " + t(L, "question.why", why=row["why"])] + [
            f"      {chr(65 + i)} {t(L, 'answer.' + option)} → ros answer {row['short_id']} {option}"
            + {"cancel": " --reason " + t(L, "ph.reason"), "defer": " --until " + t(L, "ph.date")}.get(option, "")
            for i, option in enumerate(row["options"])]

    def section(key: str, render) -> list:
        rows = data[key]
        return ([t(L, f"today.{key}", n=len(rows))] + (["  " + t(L, "none")] if not rows else [])
                + [line for row in rows for line in render(row)] + [""])
    # Today comes from the attention owner and is never truncated; triage only adds its proposals.
    lines += section("today", group) + section("decision", group) + section("questions", question)
    if data["waiting_on_trigger"]:
        lines.append(t(L, "today.waiting", n=len(data["waiting_on_trigger"])))
        lines += [f"  … [{row['short_id']}] {row['summary']} — {row['trigger']}" for row in data["waiting_on_trigger"]]
        lines.append("")
    colon = ": " if L == "en" else "："
    lines += section("proposals", lambda row: [f"  · {row['commitment_title']}{colon}{row['reason']} → {row['command']}"])
    elsewhere = sum(len(row["items"]) for row in data["needs_review"]) + len(data["network"])
    if show_all:
        lines.append(t(L, "today.elsewhere.title", n=elsewhere))
        for row in data["needs_review"]:
            lines += group(row)
        if data["network"]:
            lines += _render_group(L, {"commitment_title": t(L, "network"), "items": data["network"]}, marker="")
    else:
        lines.append(t(L, "today.elsewhere.count", n=elsewhere))
    if problems:
        lines.append(t(L, "today.problems", n=problems))
    if data["stale_sessions"]:
        lines.append(t(L, "today.stale_sessions", n=len(data["stale_sessions"]), ids=", ".join(data["stale_sessions"][-3:])))
    return "\n".join(lines)


def _fill(lang: str, action: str, row: dict) -> str:
    action = action.replace(t(lang, "ph.requirement"), row["short_id"])
    if row.get("due_date"):
        action = action.replace(t(lang, "ph.due"), row["due_date"])
    return action


def _render_group(lang: str, group: dict, *, marker: str) -> list:
    bracket = "[{}]" if lang == "en" else "［{}］"
    lines = [f"  ■ {group['commitment_title']}" + ("  " + bracket.format(marker) if marker else "")]
    if not group["items"]:
        lines.append("    " + t(lang, "today.no_items"))
    for row in group["items"]:
        lines.append(f"    · [{row['short_id']}] {row['summary']}")
        lines += [f"        {detail}" for detail in row["details"][:3]]
        lines += [f"        {chr(65 + i)} {option['label']} → {_fill(lang, option['action'], row)}"
                  for i, option in enumerate(row["options"])]
    return lines


def _date_arg(value: str | None, flag: str, *, today: date, after_today: bool) -> date:
    """A YYYY-MM-DD argument that names a real day: after today (a deferral) or not in the past (a
    schedule). Every date ros takes passes here, so `2026-02-30` or a past day is refused everywhere."""
    try:
        day = date.fromisoformat(value) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") else None
    except ValueError:
        day = None
    if day is None:
        raise SystemExit(f"{flag} must be a real date YYYY-MM-DD")
    if day < today or (after_today and day == today):
        raise SystemExit(f"{flag} {day.isoformat()} " + ("must be after today" if after_today
                                                         else "is in the past; it must be today or later"))
    return day


# -- answer: the exit of a bounded question (report D3) ------------------------------------
def _open_questions(ctx: Context, result, only_commitment: str = "") -> list:
    rows = []
    for ask_id, question in sorted(ctx.ledger.asks().items()):
        if question.get("state") != "asked":
            continue
        issue_id = (question.get("issue_ids") or [""])[0]
        if result.states["issues"].get(issue_id, {}).get("status") != "waiting":
            continue
        commitment = result.requirements.get(issue_id, {}).get("commitment_id", "")
        if only_commitment and commitment != only_commitment:
            continue
        detail = question.get("detail", {})
        rows.append({"ask_id": ask_id, "short_id": ask_id[:10], "issue_id": issue_id, "commitment_id": commitment,
                     "summary": detail.get("summary", ""), "why": detail.get("why", ""),
                     "options": question.get("options", [])})
    return rows


def _waiting_on_triggers(result, only_commitment: str = "") -> list:
    """Report D4: every held or waiting requirement is listed with its trigger, never hidden."""
    rows = []
    for issue_id, state in sorted(result.states["issues"].items()):
        trigger = state.get("reopen_trigger", "")
        if state["status"] != "waiting" or not trigger or trigger.startswith("answer:"):
            continue
        if only_commitment and result.requirements.get(issue_id, {}).get("commitment_id", "") != only_commitment:
            continue
        rows.append({"issue_id": issue_id, "short_id": issue_id[:10], "summary": state.get("summary", ""),
                     "trigger": trigger})
    return rows


def cmd_answer(ctx: Context, args) -> int:
    """One answer to one bounded question; every option has its own destination (report D3)."""
    result = ctx.boundary()
    asks = ctx.ledger.asks()
    matches = [ask_id for ask_id, question in asks.items() if ask_id.startswith(args.question)
               and question.get("state") == "asked"]
    if len(matches) != 1:
        raise SystemExit(f"question id {args.question!r} matches {len(matches)} open questions")
    ask_id = matches[0]
    question = asks[ask_id]
    issue_id = (question.get("issue_ids") or [""])[0]
    state = result.states["issues"].get(issue_id)
    if not state or state["status"] != "waiting":
        raise SystemExit(f"the requirement behind {ask_id[:10]} is no longer waiting on this question")
    option = args.option
    if option not in question.get("options", []):
        raise SystemExit(f"{option} is not offered for this question (a decision stands in for a check "
                         f"only where the check's basis is researcher judgment); offered: {', '.join(question.get('options', []))}")
    if option in {"cancel", "satisfied"} and not args.reason:
        raise SystemExit(f"answer {option} needs --reason")
    if option == "defer":
        until = _date_arg(args.until, "--until", today=ctx.today, after_today=True) if args.until else None
        if until:
            trigger = f"date:{until.isoformat()}"
        elif args.trigger:
            trigger = f"event:{args.trigger}"
        else:
            raise SystemExit("answer defer needs --until YYYY-MM-DD or --trigger <event>")
    else:
        trigger = "next_specification" if option == "narrow" else ""
    registration = result.requirements.get(issue_id, {})
    bound = requirement_binding(issue_id, state, registration)
    channel = _decision_channel(ctx.lang, f"answer:{option}", ask_id[:10])
    summary = state.get("summary", "")
    if option in {"cancel", "satisfied"} and channel[0] != "researcher_decision":
        # Closing the requirement by answering is the researcher's alone, as with ros decide cancel:
        # relayed, the answer is recorded as asserted and the question stays open.
        with ctx.ledger.lock():
            _record_decision(ctx, f"answer:{option}", issue_id, channel, operation="ask", bound=bound,
                             ask_id=ask_id, reason=args.reason or "", action=f"{option}_not_applied")
        emit(args, {"ask_id": ask_id, "answer": option, "applied": False, "permission_state": channel[0]},
             t(ctx.lang, "answer.needs_terminal", id=ask_id[:10], option=option))
        return 1
    with ctx.ledger.lock():
        decision = _record_decision(ctx, f"answer:{option}", issue_id, channel, operation="ask", bound=bound,
                                    ask_id=ask_id, reason=args.reason or "")
        reason = f"researcher_answer:{option}"
        if option == "satisfied":
            check = ctx.ledger.check("met", requirement_id=registration.get("rule_id", ""), bound=bound,
                                     checked_state_ids=[registration.get("binding", "")],
                                     basis=f"established by the researcher's answer to bounded question {ask_id[:10]} "
                                           f"(decision {decision['id'][:10]}, {channel[0]})")
            ctx.ledger.transition(bound, "resolved", reason, summary=summary, check_ids=[check["id"]])
        elif option == "unsatisfied":
            check = ctx.ledger.check("unmet", requirement_id=registration.get("rule_id", ""), bound=bound,
                                     checked_state_ids=[registration.get("binding", "")],
                                     basis=f"established unmet by the researcher's answer to {ask_id[:10]}")
            ctx.ledger.transition(bound, "open", reason, summary=summary, check_ids=[check["id"]])
        elif option == "cancel":
            ctx.ledger.transition(bound, "cancelled", reason, summary=summary)
        else:  # narrow, defer: still an unclosed requirement, waiting on a registered trigger
            ctx.ledger.transition(bound, "waiting", reason, summary=summary, reopen_trigger=trigger)
        ctx.ledger.restate_ask(ask_id, question, issue_id, "answered", answer=option, reopen_trigger=trigger,
                               detail={**question.get("detail", {}), "decision_id": decision["id"],
                                       "reason": args.reason or ""})
    return emit(args, {"ask_id": ask_id, "answer": option, "reopen_trigger": trigger,
                       "permission_state": channel[0]}, t(ctx.lang, "answer.done", id=ask_id[:10], option=option))


# -- attend: the only way ros changes attention ------------------------------------------
def cmd_attend(ctx: Context, args) -> int:
    """Apply one attention action through the attention owner (Attention Kernel §5–§6).

    A clearly named action is itself the researcher's confirmation (§5); it writes only the
    attention schedule, never the portfolio, and every action can be undone."""
    from datetime import timedelta
    # The public starter stays read-only (Soul §5): read the snapshot without running a boundary.
    snapshot = build_snapshot(ctx.root, ctx.config, None)[0] if ctx.runtime_scope == "public_starter" \
        else ctx.boundary().snapshot
    cid = args.commitment.split(":", 1)[-1]
    commitment = snapshot.commitments.get(cid)
    if not commitment:
        raise SystemExit(f"unknown commitment: {args.commitment}")
    if commitment.state == "closed" and args.action != "undo":
        raise SystemExit(f"{cid} is closed; reopen the project before scheduling it")
    if args.action == "undo":
        trajectory = ctx.ledger.trajectory()
        undone = {row["payload"].get("detail", {}).get("undoes") for row in trajectory if row.get("kind") == "effect"
                  and any(c.get("change") == "attention_undone" for c in row["payload"].get("changes", []))}
        last = next((row for row in reversed(trajectory) if row.get("kind") == "effect" and row["id"] not in undone
                     and any(c.get("change") == "attention_set" and c.get("object_id") == f"commitment:{cid}"
                             for c in row["payload"].get("changes", []))), None)
        if not last:
            raise SystemExit(f"no attention action to undo for {cid}")
        plan = {"action": "restore", "previous": last["payload"]["detail"]["previous"],
                "expected": last["payload"]["detail"]["record"]}
    else:
        kwargs = {"provider_id": PROVIDER, "item_id": cid}
        if args.action in {"today", "tomorrow", "date"}:
            day = ctx.today if args.action == "today" else ctx.today + timedelta(days=1) if args.action == "tomorrow" \
                else None
            if args.action == "date":
                day = _date_arg(args.value, "attend <commitment> date", today=ctx.today, after_today=False)
            kwargs.update(action="schedule", attention_date=day.isoformat(), today_order=args.order or 0)
        elif args.action == "park":
            if args.review:
                _date_arg(args.review, "--review", today=ctx.today, after_today=False)
            kwargs.update(action="paused", review_date=args.review or "")
        elif args.action == "complete-step":
            kwargs.update(action="complete_step", next_step=commitment.get("next_step"))
        plan = kwargs
    if ctx.runtime_scope == "public_starter":
        # Soul §5: the public starter stays read-only on this machine; show the action instead.
        return emit(args, {"promoted": False, "commitment": cid, "planned": plan},
                    t(ctx.lang, "attend.copy_fallback", id=cid, plan=json.dumps(plan, ensure_ascii=False)))
    if not ATTENTION_OWNER.is_file():
        raise SystemExit("ros attend needs the attention schedule owner, which this installation does not ship; "
                         "nothing was scheduled")
    from researchos_server.attention_schedule_store import AttentionScheduleError, AttentionScheduleStore
    store = AttentionScheduleStore.create(ctx.root)
    try:
        if plan.get("action") == "restore":
            outcome = store.restore(provider_id=PROVIDER, item_id=cid, previous=plan["previous"],
                                    expected_current=plan["expected"])
            outcome["previous"] = plan["previous"]
        else:
            outcome = store.apply(**plan)
    except AttentionScheduleError as error:
        raise SystemExit(f"attention action refused: {error}")
    with ctx.ledger.lock():
        if args.action == "undo":
            ctx.ledger.effect("", [{"object_id": f"commitment:{cid}", "change": "attention_undone",
                                    "path": outcome.get("path", "")}], detail={"undoes": last["id"]})
        else:
            ctx.ledger.effect("", [{"object_id": f"commitment:{cid}", "change": "attention_set",
                                    "path": outcome["path"], "content_id": str((outcome.get("record") or {}).get("status", ""))}],
                              detail={"action": args.action, "record": outcome.get("record"),
                                      "previous": outcome.get("previous")})
    return emit(args, {"commitment": cid, "action": args.action, "record": outcome.get("record")},
                t(ctx.lang, "attend.done", id=cid, action=args.action))


# -- close ---------------------------------------------------------------------------
def cmd_close(ctx: Context, args) -> int:
    session_id = _session_to_close(ctx, args)
    started = _session_start(ctx, session_id)
    # The ledger says the session exists; when only its start snapshot (a cache) is gone, changes since
    # the start and the frozen scope cannot be recomputed, so nothing is reported as unchanged or complete.
    cache_note = "" if started is not None else t(ctx.lang, "close.cache_missing")
    result = ctx.boundary()
    if cache_note:
        # No baseline. Field and file changes cannot be recomputed (the note says so), but a judgment
        # block that was never admitted still needs confirmation: it is listed as if new.
        snap = session_snapshot(result)
        accepted = {jid: result.states["admitted_judgments"].get(jid, set())
                    | result.states.get("confirmed_judgments", {}).get(jid, set()) for jid in snap["judgments"]}
        started = {"judgments": {jid: h for jid, h in snap["judgments"].items() if h in accepted[jid]},
                   "commitments": snap["commitments"], "files": snap["files"]}
    now = session_snapshot(result)
    write_class = ctx.write_class()
    judgment_changes = []
    admitted = result.states["admitted_judgments"]
    confirmed = result.states.get("confirmed_judgments", {})
    for jid, block_hash in sorted(now["judgments"].items()):
        before = started["judgments"].get(jid)
        if before != block_hash:
            judgment = result.snapshot.judgments[jid]
            judgment_changes.append({"judgment_id": jid, "change": "added" if before is None else "modified",
                                     "path": judgment.path, "conclusion": judgment.conclusion,
                                     "admitted": block_hash in admitted.get(jid, set()),
                                     "confirmed_post_hoc": block_hash in confirmed.get(jid, set())})
    judgment_changes += [{"judgment_id": jid, "change": "removed"} for jid in sorted(set(started["judgments"]) - set(now["judgments"]))]
    field_changes, fact_fields = [], []
    for cid, fields in sorted(now["commitments"].items()):
        before = started["commitments"].get(cid, {})
        for key in sorted(set(fields) | set(before)):
            if fields.get(key) != before.get(key):
                row = {"commitment_id": cid, "field": key, "before": before.get(key, ""), "after": fields.get(key, "")}
                (field_changes if key in write_class["commitment_fields"] else fact_fields).append(row)
    field_changes = ctx.ledger.unadmitted_field_changes(field_changes, session_id)
    if _register_field_confirmations(ctx, field_changes):
        result = ctx.refresh()  # the confirmations just registered are this session's own open work
    # Out_ε against the scope frozen when the session started, not a scope recomputed now (H7).
    report = session_completion(ctx, result, started, session_id)
    session_budget, spent = _session_account(ctx, session_id)
    spent_out = exhausted(session_budget, spent)
    out = outcome(report, stopped_by_researcher=True, exhausted_components=spent_out)
    asked = spent["asks"]  # the questions attributed to this session, the same count its budget spends
    pending_questions = [{"ask_id": ask_id[:10], "summary": q.get("detail", {}).get("summary", ""),
                          "trigger": f"answer:{ask_id}"} for ask_id, q in sorted(ctx.ledger.asks().items())
                         if q.get("state") == "asked"]
    changed_files = sorted(ref for ref, sha in now["files"].items() if started["files"].get(ref) != sha)
    from researchos_kernel.boundary import diff_versions
    file_changes = _change_rows(diff_versions(started["files"], now["files"]), result.snapshot)
    removed_commitments = sorted(set(started["commitments"]) - set(now["commitments"]))
    # Candidates the researcher declined at her terminal since this session started, read off the
    # ledger order (as unadmitted_field_changes does), never off wall-clock time.
    records = ctx.ledger.records()
    start = next((i for i, row in enumerate(records) if row.get("collection") == "episodes"
                  and row.get("episode_id") == session_id and row.get("start")), len(records))
    declined = [{"candidate_id": (row["payload"]["candidate_ids"] or [""])[0],
                 "how": row["payload"]["detail"].get("how", ""), "object_id": row["payload"]["detail"].get("object_id", ""),
                 "decision_id": row["id"]}
                for row in records[start + 1:] if row.get("collection") == "trajectory" and row.get("kind") == "decision"
                and row["payload"].get("detail", {}).get("action") == "candidate_rejected"]
    # Candidates returned since this session started that the researcher has not decided yet, by the same order.
    candidates = ctx.ledger.candidates()
    returned = dict.fromkeys(cid for row in records[start + 1:] if row.get("collection") == "trajectory"
                             and row.get("kind") == "attempt" for cid in row["payload"].get("output_ids", []))
    pending = [{"candidate_id": cid, "target": candidates[cid]["payload"].get("target", "")} for cid in returned
               if cid in candidates and not landed_or_undone(candidates[cid]["payload"])
               and (candidates[cid]["payload"].get("admission_state") or {}).get("decision_state") != "rejected"]
    change_details = {"baseline": "session_start", "baseline_available": not bool(cache_note),
                      "scope": "observed_graph", "files": None if cache_note else file_changes,
                      "removed_commitments": None if cache_note else removed_commitments}
    judgment_paths = [ref for ref in changed_files if ref.startswith(tuple(write_class["path_prefixes"]))]
    fact_files = [ref for ref in changed_files if ref not in judgment_paths]
    scope_detail = started.get("scope", {})
    coverage = {key: value for key, value in result.coverage.items() if key != "uncovered_keys"}
    held = [dict(row, kind="question") for row in report["held"]] + [dict(row, kind="trigger") for row in report["waiting"]]
    held_note = "" if report["scope_frozen"] else t(ctx.lang, "close.unfrozen")
    if cache_note:
        held_note = cache_note
    with ctx.ledger.lock():
        ctx.ledger.episode(session_id, end=now_iso(), outcome=out, held=held, asked=asked, detail={
            "judgment_changes": len(judgment_changes), "judgment_fields": len(field_changes),
            "judgment_paths": judgment_paths, "fact_files": len(fact_files), "fact_fields": len(fact_fields),
            "scope": scope_detail, "coverage": coverage, "unfinished": len(report["unfinished"]),
            "out_of_scope_open": report["out_of_scope_open"], "unowned_open": report["unowned_open"],
            "pending_questions": len(pending_questions), "note": held_note,
            "runs_unknown": report["runs_unknown"], "unknown_kinds": report["unknown_kinds"],
            "budget": session_budget, "budget_spent": spent,
            "budget_exhausted": spent_out})
    data = {"session_id": session_id, "outcome": out, "completion": report, "held": held, "asked": asked,
            "change_details": change_details,
            "pending_questions": pending_questions, "open_runs": report["runs_unknown"], "note": held_note,
            "scope": scope_detail, "coverage": coverage, "fact_files": fact_files, "fact_fields": fact_fields,
            "judgment_changes": judgment_changes, "judgment_fields": field_changes, "judgment_paths": judgment_paths,
            "declined_candidates": declined, "pending_candidates": pending}
    return emit(args, data, _render_close(ctx, data, _budget_line(ctx.lang, session_budget, spent, spent_out)))


def _render_close(ctx: Context, data: dict, budget_line: str) -> str:
    """The text of `close`, from the same data its --json prints."""
    L = ctx.lang
    report, scope, coverage, details = data["completion"], data["scope"], data["coverage"], data["change_details"]
    lines = [t(L, "close.header", session=data["session_id"]), "",
             t(L, "close.outcome", outcome=data["outcome"], unfinished=len(report["unfinished"]), held=len(data["held"])),
             t(L, "close.scope", node=scope.get("scope_node", "?"), members=scope.get("scope_member_count", "?"),
               cross=len(scope.get("cross_scope_keys", [])),
               uncovered=coverage.get("coverage_unknown_in_scope", 0), unowned=coverage.get("coverage_unknown_unowned", 0),
               evaluated=coverage.get("evaluated_match_count", 0), domain=coverage.get("in_scope_match_count", 0),
               outside=report["out_of_scope_open"], undefined=report["unowned_open"]),
             _unknowns_line(L, report), budget_line]
    if data["note"]:
        lines.append("  ! " + data["note"])
    if report.get("next_episode"):
        lines.append("  » " + t(L, "close.next_episode", n=len(report["next_episode"])))
    lines += [f"  ⏸ [{row['short_id']}] {row['summary']} — {row['trigger']}" for row in data["held"]]
    lines += [f"  ? [{row['ask_id']}] {row['summary']} — {t(L, 'close.pending_question')}" for row in data["pending_questions"]]
    # Kernel §2.1: ending the session does not end its runs; each keeps its own tracking.
    lines += ["  ↻ " + t(L, "unknowns.run", run=run_id) for run_id in data["open_runs"]]
    lines += [f"  ○ [{row['short_id']}] {row['summary']}" for row in report["unfinished"][:10]]
    lines += ["", t(L, "close.changes")]
    if not details["baseline_available"]:
        lines.append("  ! " + data["note"])  # the note is why there is no baseline
    else:
        lines += _render_changes(L, details["files"])
        lines += ["  · " + t(L, "close.commitment_removed", id=cid) for cid in details["removed_commitments"]]
        if not details["files"] and not details["removed_commitments"]:
            lines.append("  " + t(L, "none"))
    lines += ["", t(L, "close.facts", files=len(data["fact_files"]), fields=len(data["fact_fields"]))]
    for row in data["fact_fields"]:
        lines.append("  · " + t(L, "close.field", id=row["commitment_id"], field=row["field"],
                                 before=row["before"] if row["before"] != "" else t(L, "empty"),
                                 after=row["after"] if row["after"] != "" else t(L, "empty")))
    lines += ["", t(L, "close.judgments")]
    if not (data["judgment_changes"] or data["judgment_fields"] or data["judgment_paths"]):
        lines.append("  " + t(L, "none"))
    for row in data["judgment_changes"]:
        if row.get("admitted"):
            hint = t(L, "close.admitted")
        elif row.get("confirmed_post_hoc"):
            hint = t(L, "close.confirmed_post_hoc")
        elif row["change"] == "removed":
            hint = t(L, "close.removed")
        else:
            hint = f"ros admit --confirm {row['judgment_id']}"
        lines.append("  · " + t(L, "close.block", id=row["judgment_id"], change=row["change"],
                                 conclusion=row.get("conclusion", ""), hint=hint))
    for row in data["judgment_fields"]:
        lines.append("  · " + t(L, "close.field", id=row["commitment_id"], field=row["field"],
                                 before=row["before"] or t(L, "empty"), after=row["after"] or t(L, "empty")))
    for ref in data["judgment_paths"]:
        lines.append("  · " + t(L, "close.path", path=ref))
    if data["declined_candidates"]:
        lines += ["", t(L, "close.declined")]
        lines += ["  · " + t(L, "close.declined_row", candidate=row["candidate_id"], how=row["how"], object=row["object_id"])
                  for row in data["declined_candidates"]]
    if data["pending_candidates"]:
        lines += ["", t(L, "close.pending")]
        lines += ["  · " + t(L, "close.pending_row", candidate=row["candidate_id"], target=row["target"])
                  for row in data["pending_candidates"]]
    lines += ["", t(L, "close.template")]
    return "\n".join(lines)


# -- propose / admit / decide ------------------------------------------------------------------
def cmd_propose(ctx: Context, args) -> int:
    if args.kind == "rule":
        return _propose_rule(ctx, args)
    if not args.target:
        raise SystemExit(f"propose {args.kind} needs --target")
    if args.kind == "episode-close":
        return _propose_episode_close(ctx, args)
    if not args.file:
        raise SystemExit("propose judgment needs --file")
    if args.executor not in PROPOSE_EXECUTORS:
        raise SystemExit("a provider or copy-packet result enters through `ros run` / `ros collect`, not propose")
    created = _propose_judgments(ctx, Path(args.file).read_text(encoding="utf-8"), args.file, args.target,
                                 executor=args.executor,
                                 session_id=_session_for(ctx, args.target, args.session or "", required=False))
    lines = [t(ctx.lang, "propose.done", n=len(created))] + [f"  ros admit {cid}" for cid in created]
    bound = ctx.ledger.candidates()[created[0]]["payload"].get("session_id", "") if created else ""
    if created and not bound:
        lines.append("  ! " + t(ctx.lang, "propose.unbound"))
    return emit(args, {"candidates": created, "session_id": bound}, "\n".join(lines))


PROPOSE_EXECUTORS = ("session_agent", "script")


def _propose_judgments(ctx: Context, text: str, origin: str, target: str, *, executor: str, run_id: str = "",
                       session_id: str = "") -> list:
    """One entry for every executor's judgment drafts: parsed, checked, and recorded as candidates.
    Nothing here writes a card; admission is a separate decision (Soul §3)."""
    found, problems = parse_judgments(text, origin)
    if problems or not found:
        raise SystemExit("\n".join(problems) or "no judgment block found in file")
    if len(found) > 3:
        raise SystemExit("at most 3 judgment blocks per proposal")
    result = ctx.boundary()
    if target.startswith("commitment:"):
        if target.split(":", 1)[1] not in result.snapshot.commitments:
            raise SystemExit(f"unknown commitment: {target}")
    elif not (ctx.root / target).is_file():
        raise SystemExit(f"target card not found: {target}")
    ids = [judgment.id for judgment in found]
    for judgment in found:  # every block is checked before any is recorded: all or none
        if judgment.id in result.snapshot.judgments or ids.count(judgment.id) > 1:
            raise SystemExit(f"judgment id already exists: {judgment.id}")
        for basis in judgment.basis:
            if not result.snapshot.resolve(basis.ref)[0]:
                raise SystemExit(f"basis cannot be resolved: {basis.ref}")
    # Freeze even unversioned references at proposal time; collect and session-agent
    # proposals share this path. A later admit may not bless a different basis.
    from researchos_kernel.judgments import BasisRef
    try:
        found = tuple(replace(judgment, basis=tuple(
            BasisRef(item.ref, result.snapshot.resolve(item.ref)[1])
            for item in pin_basis(result.snapshot, judgment.basis, refresh=False))) for judgment in found)
    except WritebackError as error:
        raise SystemExit(str(error))
    rows = []
    for judgment in found:
        envelope = _new_candidate("judgment", judgment.conclusion,
                                  [{"kind": "basis", "value": basis.ref} for basis in judgment.basis], {
            "save_target": target,
            "object_type": "judgment",
            "object_id": judgment.id,
            "object_path": target if not target.startswith("commitment:") else result.snapshot.portfolio_path,
            "proposed_state": judgment.conclusion,
            "decision_rationale": judgment.fields.get("basis", ""),
        })
        rows.append((envelope["candidate_id"], judgment, envelope))
    with ctx.ledger.lock():
        for candidate_id, judgment, envelope in rows:
            ctx.ledger.record_candidate(envelope, {"target": target, "judgment": judgment.to_dict(),
                                                   "admission_state": _proposed_state(),
                                                   "created_at": now_iso(), "executor": executor, "run_id": run_id,
                                                   "session_id": session_id})
        if not run_id:  # a run records its own single attempt, linked to its dispatch decision
            ctx.ledger.attempt("", "returned", [cid for cid, _, _ in rows],
                               detail={"judgment_ids": [j.id for _, j, _ in rows], "target": target,
                                       "executor": executor})
    created = [cid for cid, _, _ in rows]
    return created


def _new_candidate(candidate_type: str, summary: str, source_refs: list, writeback: dict) -> dict:
    """A fresh CandidateEnvelope for anything ros proposes: the researcher must confirm it, and it is
    proposed, not admitted (HJ-2). Every proposal path builds its envelope here."""
    return normalize_candidate_envelope({
        "candidate_id": f"c-{uuid.uuid4().hex[:8]}", "plugin_id": "researchos_core",
        "candidate_type": candidate_type, "summary": summary, "source_refs": source_refs,
        "proposed_writeback": writeback, "required_confirmation": "researcher",
        "validation": {"workflow_status": "proposed", "evidence_state": "candidate"},
        "admission_state": _proposed_state(),
    })


def _rule_file(ctx: Context, rule_id: str) -> str:
    """The descriptor file that declares ``rule_id``, or the path a new one would take."""
    from researchos_kernel.rules import RULES_RELATIVE
    directory = ctx.root / RULES_RELATIVE
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("id") == rule_id:
                return str(path.relative_to(ctx.root))
        except (OSError, json.JSONDecodeError):
            continue
    return f"{RULES_RELATIVE}/{rule_id.replace('_', '-')}.json"


def _semver(value: str) -> tuple:
    try:
        return tuple(int(part) for part in str(value).split("."))
    except ValueError:
        return ()


def _propose_rule(ctx: Context, args) -> int:
    """A rule revision is a candidate like any other (Soul §6, HJ-5b): the revised descriptor plus its
    scope, the sessions it comes from, counterexamples, version, review date, retirement condition and
    rollback target. Nothing here changes a rule; the current rules keep running until admission."""
    from researchos_kernel.rules import _violations, load_contract, load_registry
    from researchos_kernel.rule_evolution import RuleEvolutionError, build_rule_candidate
    if not args.file:
        raise SystemExit("propose rule needs --file <revision.json> with a descriptor and a revision record")
    try:
        body = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read {args.file}: {error}")
    descriptor, revision = body.get("descriptor"), body.get("revision")
    if not isinstance(descriptor, dict) or not isinstance(revision, dict):
        raise SystemExit("the file needs {\"descriptor\": {...}, \"revision\": {...}}")
    contract, problems = load_contract(ctx.root, ROOT)
    if not contract:
        raise SystemExit("no rule contract to validate against: " + "; ".join(problems))
    found = _violations(descriptor, contract)
    if found:
        raise SystemExit("the revised descriptor does not meet the current contract: " + "; ".join(found[:5]))
    from researchos_kernel.rules import delegation_problems
    reasons = delegation_problems(descriptor, write_class(ctx.root, ROOT))
    if reasons:
        raise SystemExit("resolver=script is only for bounded, reversible fact maintenance: " + "; ".join(reasons))
    current, _ = load_registry(ctx.root, ROOT)
    before = current.get(descriptor["id"])
    if before and _semver(descriptor["version"]) <= _semver(before["version"]):
        raise SystemExit(f"a revision must raise the version above {before['version']}")
    rollback = f"{descriptor['id']}@{before['version']}" if before else f"{descriptor['id']}@none"
    if not before and (ctx.root / _rule_file(ctx, descriptor["id"])).exists():
        raise SystemExit(f"{_rule_file(ctx, descriptor['id'])} already exists and declares another rule; "
                         "a new rule cannot take its file")
    if revision.get("rollback_target", rollback) != rollback:
        raise SystemExit(f"rollback_target must be the version this revision replaces: {rollback}")
    known = ctx.ledger.sessions()
    unknown = [sid for sid in revision.get("source_episodes", []) if sid not in known]
    if unknown:
        raise SystemExit("source_episodes must be sessions recorded here: " + ", ".join(unknown))
    major, minor, patch = (list(_semver(descriptor["version"])) + [0, 0, 0])[:3]
    if max(minor, patch) >= 1000 or len(_semver(descriptor["version"])) > 3:
        raise SystemExit("rule versions are MAJOR.MINOR.PATCH with MINOR and PATCH below 1000")
    try:
        record = build_rule_candidate({
            "statement": f"{descriptor['id']} {descriptor['version']}: {descriptor.get('summary_en') or descriptor.get('summary_zh', '')}",
            "scope": revision.get("scope"), "source_episodes": revision.get("source_episodes"),
            "counterevidence": revision.get("counterevidence"), "version": major * 1_000_000 + minor * 1_000 + patch,
            "review_date": revision.get("review_date"), "retire_trigger": revision.get("retire_trigger"),
            "rollback_target": rollback, "created_at": datetime.now().astimezone().isoformat(timespec="seconds")})
    except RuleEvolutionError as error:
        raise SystemExit(f"revision record incomplete: {error}")
    relative = _rule_file(ctx, descriptor["id"])
    base = hashlib.sha256((ctx.root / relative).read_bytes()).hexdigest() if (ctx.root / relative).is_file() else ""
    envelope = _new_candidate(
        "rule_revision", record["statement"][:240],
        [{"kind": "episode", "value": sid} for sid in record["source_episodes"]],
        {"save_target": relative, "object_type": "rule", "object_id": descriptor["id"],
         "object_path": relative, "current_state": before["version"] if before else "absent",
         "proposed_state": descriptor["version"], "decision_rationale": args.reason or ""})
    candidate_id = envelope["candidate_id"]
    with ctx.ledger.lock():
        attempt = ctx.ledger.attempt("", "returned", [candidate_id], detail={"rule_id": descriptor["id"], "action": "rule_revision"})
        ctx.ledger.record_candidate(envelope, {"target": relative, "descriptor": descriptor, "revision": record,
                                               "base_file_sha": base, "attempt_id": attempt["id"],
                                               "admission_state": _proposed_state(), "created_at": now_iso()})
    lines = [t(ctx.lang, "propose.done", n=1), f"  ros admit {candidate_id}"]
    return emit(args, {"candidates": [candidate_id], "rule_id": descriptor["id"], "target": relative}, "\n".join(lines))


def _admit_rule_revision(ctx: Context, args, candidate_id: str) -> int:
    """Land a rule revision through staging (CA-8, P5). The adoption is judged against the rules
    that are running now: the candidate's descriptor is validated by the current contract, it must
    still revise the file it was proposed against, and no check it introduces takes part in its
    own adoption. The new version applies from the next session (Ver_{ε+1})."""
    from researchos_kernel.rules import _violations, load_contract
    from researchos_kernel.rule_evolution import normalize_rule_version
    payload = ctx.ledger.candidates()[candidate_id]["payload"]  # cmd_admit has refused a landed one
    relative, descriptor = payload["target"], payload["descriptor"]
    if ctx.runtime_scope != "public_starter":
        # A rule reshapes every later completion judgment: only the researcher's own answer on this
        # machine's terminal admits it. An agent may propose a revision, never admit one.
        channel = _decision_channel(ctx.lang, "rule_revision", descriptor["id"], declinable=True)
        if channel[1] == "terminal_declined":
            return _decline_candidate(ctx, args, candidate_id, "rule_revision", descriptor["id"], channel)
        if channel[0] != "researcher_decision":
            raise SystemExit(f"a rule revision is admitted only at the researcher's terminal: run "
                             f"`ros admit {candidate_id}` there yourself")
    with ctx.ledger.lock():
        stored = _pending_candidate(ctx, candidate_id)
        path = ctx.root / relative
        now_sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        if now_sha != payload.get("base_file_sha", ""):
            raise SystemExit(f"the rule changed since this revision was proposed; propose again: {relative}")
        contract, problems = load_contract(ctx.root, ROOT)
        found = _violations(descriptor, contract) if contract else problems or ["no contract"]
        if found:
            raise SystemExit("the revision does not meet the current contract: " + "; ".join(found[:5]))
        new_text = json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n"
        fallback = _copy_fallback(ctx, args, "rule_revision", relative, new_text)
        if fallback is not None:
            return fallback
        decision = _record_decision(ctx, "rule_revision", descriptor["id"], channel, candidate_id)
        revision = payload["revision"]
        version = normalize_rule_version({
            "schema_id": revision["schema_id"], "object_kind": "rule_version",
            "rule_version_ref": f"{descriptor['id']}@{descriptor['version']}", "rule_id": revision["rule_id"],
            "version": revision["version"], "statement": revision["statement"], "scope": revision["scope"],
            "source_episodes": revision["source_episodes"], "counterevidence": revision["counterevidence"],
            "review_date": revision["review_date"], "retire_trigger": revision["retire_trigger"],
            "rollback_target": revision["rollback_target"], "stability": "stable",
            "supersedes": [revision["rollback_target"]], "human_disposition_ref": decision["id"],
            "claim_boundary": revision["claim_boundary"]})  # built before anything is written
        admission = _admit_axes(stored["payload"].get("admission_state"))

        def record(receipt: dict) -> None:
            transaction = receipt.get("transaction_id", "")
            attempt = _attempt(ctx, decision, "applied", [relative], transaction_id=transaction)
            effect = ctx.ledger.effect(attempt["id"], [{"object_id": descriptor["id"], "change": "rule_revised",
                                                        "path": relative, "content_id": descriptor["version"]}],
                                       detail={"how": "admit_candidate", "candidate_id": candidate_id,
                                               "decision_id": decision["id"], "rule_version": version,
                                               "receipt_id": receipt.get("receipt_id", ""), "transaction_id": transaction,
                                               "changes": receipt.get("changes", []), "admission_state": admission,
                                               "applies_from": "next_session"})
            # CA-8: the adoption rests on the contract and the decision in force, never on the candidate's checks.
            ctx.ledger.check("met", requirement_id="rule_revision_admission", checked_state_ids=[descriptor["id"]],
                             supports_effect_ids=[effect["id"]],
                             basis=f"descriptor valid under the contract in force; base file unchanged since proposal; "
                                   f"decision channel {channel[0]} ({channel[1]}); "
                                   f"the candidate's own checks were not evaluated")
            _record_candidate_state(ctx, stored, admission, receipt_id=receipt.get("receipt_id", ""))
        receipt, _ = _land(ctx, decision, relative, new_text, now_sha or None, record,
                           what=f"rule revision {descriptor['id']}")
    ctx.refresh()
    text = t(ctx.lang, "admit.rule", id=descriptor["id"], version=descriptor["version"], path=relative) + \
        t(ctx.lang, "admit.receipt", transaction=receipt.get("transaction_id", ""))
    return emit(args, {"rule_id": descriptor["id"], "version": descriptor["version"], "path": relative,
                       "transaction_id": receipt.get("transaction_id", ""), "admission_state": admission,
                       "applies_from": "next_session"}, text)


def _propose_episode_close(ctx: Context, args) -> int:
    """Closing an episode is a decision: it becomes a candidate first and lands only on admission."""
    if not args.reason:
        raise SystemExit("propose episode-close needs --reason")
    result = ctx.boundary()
    target = args.target
    node = result.snapshot.nodes.get(target)
    if not node:
        raise SystemExit(f"episode not found in the scanned graph: {target}")
    try:
        episode_state_of(ctx.root, target)  # the same reader admit writes with
    except WritebackError as error:
        raise SystemExit(f"{target}: {error}")
    place = scope_axis.placements_from_snapshot(result.snapshot, ctx.ledger.closure_receipts())[target]
    if place.closed:
        raise SystemExit(f"episode already closed by receipt {place.closure_receipt}: {target}")
    envelope = _new_candidate("episode_close", f"close episode {target}",
                              [{"kind": "episode", "path": target, "value": node.file_sha}], {
        "save_target": target, "object_type": "episode", "object_id": node.id, "object_path": target,
        "current_state": place.episode_state, "proposed_state": "closed",
        "decision_rationale": args.reason,
        "impact_scope": f"leaves cl({place.scope}); the file stays and remains citable",
    })
    candidate_id = envelope["candidate_id"]
    with ctx.ledger.lock():
        attempt = ctx.ledger.attempt("", "returned", [candidate_id], detail={"episode": target, "action": "episode_close"})
        ctx.ledger.record_candidate(envelope, {"target": target, "episode_close": {
            "path": target, "identity": node.id, "file_sha": node.file_sha, "reason": args.reason,
            "scope": place.scope, "attempt_id": attempt["id"]},
            "admission_state": _proposed_state(), "created_at": now_iso()})
    lines = [t(ctx.lang, "propose.done", n=1), f"  ros admit {candidate_id}"]
    return emit(args, {"candidates": [candidate_id]}, "\n".join(lines))


def _admit_episode_close(ctx: Context, args, candidate_id: str) -> int:
    """Land one closure through staging. The closure receipt id is the id of the effect recorded
    for it, minted before the write so the source can name it (the staging receipt cannot be
    named inside the file its digest covers; the effect binds the two). Check, plan, write and
    record happen under the ledger lock, so two admissions cannot both land."""
    snapshot = ctx.boundary().snapshot
    episode = ctx.ledger.candidates()[candidate_id]["payload"]["episode_close"]["path"]
    # As for a judgment candidate, the public starter only shows the planned change, so it asks nothing first.
    channel = ("invoker_asserted", "copy_fallback") if ctx.runtime_scope == "public_starter" else \
        _decision_channel(ctx.lang, "episode_close", episode, declinable=True)
    if channel[1] == "terminal_declined":
        return _decline_candidate(ctx, args, candidate_id, "episode_close", episode, channel)
    with ctx.ledger.lock():
        stored = _pending_candidate(ctx, candidate_id)
        close = stored["payload"]["episode_close"]
        relative = close["path"]
        path = ctx.root / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != close["file_sha"]:
            raise SystemExit(f"episode changed since it was proposed; propose again: {relative}")
        place = scope_axis.placements_from_snapshot(snapshot, ctx.ledger.closure_receipts()).get(relative)
        if place and place.closed:
            raise SystemExit(f"episode already closed by receipt {place.closure_receipt}: {relative}")
        closure_id = f"episode-close-{uuid.uuid4().hex[:16]}"
        try:
            relative, new_text, before_sha = plan_episode_close(ctx.root, relative, closure_id)
        except WritebackError as error:
            raise SystemExit(str(error))  # nothing decided: the episode cannot be written
        fallback = _copy_fallback(ctx, args, "episode_close", relative, new_text)
        if fallback is not None:
            return fallback
        decision = _record_decision(ctx, "episode_close", relative, channel, candidate_id)
        admission = _admit_axes(stored["payload"].get("admission_state"))

        def record(receipt: dict) -> None:
            transaction = receipt.get("transaction_id", "")
            closed_episode(ctx.root, relative, closure_id)
            after_sha = next((str(c.get("new_digest") or "") for c in receipt.get("changes", [])
                              if c.get("path") == relative), "")
            bound = binding(attempt_id=close.get("attempt_id", ""), source_version_vector=close["file_sha"])
            attempt = _attempt(ctx, decision, "applied", [relative], transaction_id=transaction,
                               proposal_attempt_id=close.get("attempt_id", ""))
            effect = ctx.ledger.effect(attempt["id"], [{
                "object_id": relative, "episode_identity": close["identity"], "content_id": after_sha,
                "change": "episode_closed", "path": relative, "prior_file_sha": close["file_sha"]}],
                detail={"how": "admit_candidate", "candidate_id": candidate_id, "binding": bound,
                        "decision_id": decision["id"],
                        "reason": close.get("reason", ""), "scope": close.get("scope", ""),
                        "receipt_id": receipt.get("receipt_id", ""), "transaction_id": transaction,
                        "changes": receipt.get("changes", []), "admission_state": admission},
                record_id=closure_id)
            ctx.ledger.check("met", requirement_id="episode_closure", bound=bound, checked_state_ids=[relative],
                             supports_effect_ids=[effect["id"]],
                             basis="frontmatter_parsed_back,closure_receipt_named_in_source,staging_receipt_committed")
            _record_candidate_state(ctx, stored, admission, receipt_id=receipt.get("receipt_id", ""),
                                    closure_receipt=closure_id)
        receipt, _ = _land(ctx, decision, relative, new_text, before_sha, record, what=f"closure of {relative}")
        transaction = receipt.get("transaction_id", "")
    commit = _commit(ctx, relative, f"ros admit: close episode {relative}") if args.commit else ""
    ctx.refresh()
    text = t(ctx.lang, "admit.episode_closed", path=relative, receipt=closure_id) + \
        (t(ctx.lang, "admit.commit", commit=commit) if commit else "") + \
        t(ctx.lang, "admit.receipt", transaction=transaction)
    return emit(args, {"episode": relative, "closure_receipt": closure_id, "commit": commit,
                       "receipt_id": receipt.get("receipt_id", ""), "transaction_id": transaction,
                       "admission_state": admission}, text)


def cmd_receipt(ctx: Context, args) -> int:
    """Look up one closure receipt: the effect, the checks that support it, the candidate, and
    whether a rollback has revoked it."""
    trajectory = ctx.ledger.trajectory()
    found = ctx.ledger.closure_receipts(trajectory).get(args.receipt_id)
    if not found:
        raise SystemExit(f"closure receipt not found in the local ledger: {args.receipt_id}")
    effect = found["record"]
    checks = [row for row in trajectory if row.get("kind") == "check"
              and args.receipt_id in row.get("payload", {}).get("supports_effect_ids", [])]
    detail = effect["payload"].get("detail", {})
    candidate = ctx.ledger.candidates().get(detail.get("candidate_id", ""), {})
    change = next(c for c in effect["payload"]["changes"] if c.get("change") == "episode_closed")
    data = {"closure_receipt": args.receipt_id, "at": effect.get("at", ""), "episode": change.get("path", ""),
            "identity": found["identity"], "revoked": found["revoked"],
            "reason": detail.get("reason", ""), "candidate_id": detail.get("candidate_id", ""),
            "attempt_id": effect["payload"].get("attempt_id", ""),
            "admission_state": detail.get("admission_state", {}), "staging_receipt_id": detail.get("receipt_id", ""),
            "transaction_id": detail.get("transaction_id", ""), "checks": [row["payload"]["result"] for row in checks],
            "candidate_type": candidate.get("envelope", {}).get("candidate_type", "")}
    text = t(ctx.lang, "receipt.row", **{k: data[k] for k in ("closure_receipt", "episode", "at", "reason",
                                                               "candidate_id", "transaction_id")})
    if found["revoked"]:
        text += t(ctx.lang, "receipt.revoked")
    return emit(args, data, text)


def _commit(ctx: Context, path: str, message: str) -> str:
    subprocess.run(["git", "add", "--", path], cwd=ctx.root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message, "--", path], cwd=ctx.root, check=True)
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ctx.root, capture_output=True, text=True).stdout.strip()


def _write_through_staging(ctx: Context, relative: str, new_text: str, *, run_id: str,
                           expected_digest: str | None) -> dict:
    """The mutation owner is filesystem_staging: pre-image, digests, receipt and rollback."""
    policy = {"operation": "canonical_writeback", "network_access": "disabled", "credential_access": "denied",
              "allowed_write_targets": [{"path": relative, "mode": "file"}]}
    staging = begin_canonical_staging(root=ctx.root, runtime_scope=ctx.runtime_scope, run_id=run_id, authority_policy=policy)
    working = staging.verify_for_launch(root=ctx.root, authority_policy=policy)
    target = working / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(new_text.encode("utf-8"))  # keep the caller's line endings exactly
    try:
        return staging.promote(expected_preimages={relative: expected_digest})
    except FilesystemStagingError as error:
        if error.code == "filesystem_staging_preimage_conflict":
            staging.abort()  # conflict is detected before any source mutation or receipt
        raise


def _copy_fallback(ctx: Context, args, how: str, relative: str, new_text: str) -> int | None:
    """Soul §5: the public starter keeps canonical promotion off and offers a copy fallback.
    A write that would land in a source is shown as the planned change and not made; nothing
    is decided or recorded. Returns None where promotion is allowed."""
    if ctx.runtime_scope != "public_starter":
        return None
    import difflib
    path = ctx.root / relative
    before = path.read_text(encoding="utf-8").splitlines(keepends=True) if path.is_file() else []
    diff = "".join(difflib.unified_diff(before, new_text.splitlines(keepends=True),
                                        fromfile=f"a/{relative}", tofile=f"b/{relative}"))
    reason = "public_starter: copy fallback only; nothing was written to or admitted into the durable sources"
    return emit(args, {"promoted": False, "how": how, "path": relative, "reason": reason, "planned_diff": diff},
                t(ctx.lang, "admit.copy_fallback", how=how, path=relative) + "\n" + diff)


def _decision_channel(lang: str, how: str, object_id: str, declinable: bool = False) -> tuple:
    """(permission_state, evidence) for a decision ros records (admission, rollback, answer, decide).
    Soul §1: only the researcher decides, so
    `researcher_decision` is recorded only when the researcher answered on this machine's
    terminal. Anything else — an agent relaying a chat confirmation, a script — is what it is:
    a decision asserted by whoever ran ros, with the channel written down. A "no" at the terminal
    stops the command, except where a candidate awaits her answer (``declinable``): there the
    refusal is her decision too, returned as `terminal_declined` for the caller to record."""
    import os
    if sys.stdin.isatty() and sys.stderr.isatty():
        kind, _, action = how.partition(":")  # answer:<option> and decide:<action> share one question each
        sys.stderr.write(t(lang, f"prompt.{kind}", id=object_id, action=action) + t(lang, "prompt.yes_no"))
        sys.stderr.flush()
        if sys.stdin.readline().strip().lower() not in {"y", "yes"}:
            if declinable:
                return "researcher_decision", "terminal_declined"
            raise SystemExit(f"not done: declined at the terminal ({how} {object_id})")
        return "researcher_decision", "terminal_confirmation"
    return "invoker_asserted", "channel:non_tty" + (",claude_code" if os.environ.get("CLAUDECODE") else "")


def _record_decision(ctx: Context, how: str, object_id: str, channel: tuple, candidate_id: str = "",
                     operation: str = "admit", bound: dict | None = None, **detail) -> dict:
    """HJ-1: the admission is a recorded decision, written after the target is validated and
    before anything lands. Caller holds the lock."""
    permission, evidence = channel
    return ctx.ledger.decision(operation, bound=bound, read_set=[object_id],
                               candidate_ids=[candidate_id] if candidate_id else [], permission_state=permission,
                               detail={"how": how, "object_id": object_id, "decided_at": now_iso(),
                                       "decision_evidence": evidence, **detail})


def _attempt(ctx: Context, decision: dict, status: str, outputs: list, **detail) -> dict:
    """decision -> attempt -> effect: a refused or failed write is recorded, not left implicit."""
    return ctx.ledger.attempt(decision["id"], status, outputs, detail=detail)


def _land(ctx: Context, decision: dict, relative: str, new_text: str, before_sha: str | None, record, *,
          what: str) -> tuple:
    """Land one admitted write and record it: (staging receipt, what ``record(receipt)`` returned).

    The one copy of the landing protocol for every admission. A write the staging owner refuses is
    recorded as refused. A write that landed but could not be recorded is rolled back, and the
    journal says so with a failed attempt and a `writeback_rolled_back` effect on its transaction,
    so `derive_states` and the closure receipts never count it as landed. Caller holds the lock."""
    try:
        receipt = _write_through_staging(ctx, relative, new_text, expected_digest=before_sha,
                                         run_id=f"ros-admit-{uuid.uuid4().hex[:8]}")
    except FilesystemStagingError as error:
        _attempt(ctx, decision, "refused", [], reason=str(error))
        raise SystemExit(f"write refused by the staging owner: {error}")
    transaction = receipt.get("transaction_id", "")
    try:
        return receipt, record(receipt)
    except Exception as error:  # written but not fully recorded: undo it, say where
        try:
            rollback_artifact_mutation(root=ctx.root, receipt=receipt)
            undone = "rolled back"
        except FilesystemStagingError as rollback_error:
            undone = f"NOT rolled back ({rollback_error}); run: ros admit --rollback {transaction}"
        try:  # best effort: the journal must not keep claiming a write that was undone
            failed = _attempt(ctx, decision, "failed", [], transaction_id=transaction, reason=str(error))
            if undone == "rolled back":
                ctx.ledger.effect(failed["id"], [{"object_id": decision["payload"]["detail"]["object_id"],
                                                  "change": "writeback_rolled_back", "path": relative}],
                                  detail={"transaction_id": transaction, "reason": "recording failed"})
        except Exception:  # noqa: BLE001 - the message below still says what happened
            undone += " (and the journal could not record the undo)"
        raise SystemExit(f"{what} was written but could not be recorded ({error}); transaction {transaction} {undone}")


def _pending_candidate(ctx: Context, candidate_id: str) -> dict:
    """The stored candidate, refused when it is unknown, already went through admission, or was
    declined by the researcher (a declined candidate stays declined; admitting it needs a new proposal)."""
    stored = ctx.ledger.candidates().get(candidate_id)
    if not stored:
        raise SystemExit(f"candidate not found: {candidate_id}")
    done = landed_or_undone(stored.get("payload", {}))
    if done:
        raise SystemExit(f"candidate already admitted ({done}): {candidate_id}")
    if (stored["payload"].get("admission_state") or {}).get("decision_state") == "rejected":
        raise SystemExit(f"candidate declined by the researcher (decision {stored['payload'].get('declined_by', '')}); "
                         f"propose again to admit it: {candidate_id}")
    return stored


def _decline_candidate(ctx: Context, args, candidate_id: str, how: str, object_id: str, channel: tuple) -> int:
    """Soul §1: the researcher's "no" at her terminal is her decision. It is recorded, the candidate
    ends rejected, and nothing is written to any source. Caller has not taken the lock."""
    with ctx.ledger.lock():
        stored = _pending_candidate(ctx, candidate_id)
        state = stored["payload"].get("admission_state") or initial_admission_state(authority_role="normative")
        if state.get("decision_state") == "unproposed":  # legacy candidates predate _proposed_state
            state = _advance(state, ("decision_state", "proposed"))
        rejected = _advance(state, ("decision_state", "rejected"))
        decision = _record_decision(ctx, how, object_id, channel, candidate_id, operation="retire",
                                    action="candidate_rejected")
        _record_candidate_state(ctx, stored, rejected, declined_by=decision["id"])
    return emit(args, {"candidate_id": candidate_id, "how": how, "object_id": object_id, "declined": True,
                       "decision_id": decision["id"], "admission_state": rejected},
                t(ctx.lang, "admit.declined", candidate=candidate_id, how=how, object=object_id))


POST_HOC = frozenset({"confirm_existing_block", "reconfirm_confirmed"})  # break-glass lineage (HJ-8)


def _record_admission(ctx: Context, judgment_id: str, landed: dict, how: str, *,
                      receipt: dict, admission: dict, candidate_id: str = "", decision_id: str = "",
                      attempt_id: str = "", commitment_field_change: dict | None = None) -> None:
    """Record the effect and its check. The caller holds the ledger lock.

    A block that reached the card without prior authorization and is confirmed afterwards is
    break-glass (Soul §3, HJ-8): the record says so, it closes only the confirmation requirement,
    and it is never counted as an admission."""
    post_hoc = how in POST_HOC
    effect = ctx.ledger.effect(attempt_id, [{"object_id": judgment_id, "content_id": landed["block_hash"],
                                     "change": "direct_change_confirmed" if post_hoc else "judgment_admitted",
                                     "path": landed["path"]}],
                               detail={"how": how, "decision_id": decision_id, "receipt_id": receipt.get("receipt_id", ""),
                                       "transaction_id": receipt.get("transaction_id", ""),
                                       "changes": receipt.get("changes", []),
                                       "authorization": "post_hoc_break_glass" if post_hoc else "prior_decision",
                                       "commitment_field_change": commitment_field_change or {},
                                       "admission_state": admission, "candidate_id": candidate_id})
    if post_hoc:
        ctx.ledger.check("met", requirement_id="change_confirmation", checked_state_ids=[judgment_id],
                         supports_effect_ids=[effect["id"]],
                         basis="researcher confirmed a change made without prior authorization; "
                               "closes the confirmation requirement only, not an admission")
        return
    ctx.ledger.check("met", requirement_id="judgment_admission", checked_state_ids=[judgment_id],
                     supports_effect_ids=[effect["id"]],
                     basis="block_parsed_back,basis_pinned_to_current_versions,staging_receipt_committed")


def _advance(state: dict, *steps) -> dict:
    for axis, target in steps:
        state = transition_admission_state(state, axis=axis, target=target)
    return state


def _proposed_state() -> dict:
    """A candidate is proposed when it is proposed, not when it is admitted."""
    return _advance(initial_admission_state(authority_role="normative"), ("decision_state", "proposed"))


def _admit_axes(state: dict | None) -> dict:
    """The researcher's admission from wherever the candidate stands. Validation passes only
    after the landed write parsed back, which every caller checks before recording this."""
    state = state or initial_admission_state(authority_role="normative")
    if state.get("decision_state") == "unproposed":  # legacy candidates predate _proposed_state
        state = _advance(state, ("decision_state", "proposed"))
    return _advance(state, ("decision_state", "accepted"), ("mutation_state", "staged"), ("validation_state", "pending"),
                    ("mutation_state", "applied"), ("validation_state", "passed"))


def _record_candidate_state(ctx: Context, stored: dict, state: dict, **extra) -> None:
    """One admission state per candidate: the envelope carries the same axes as the payload
    (its owner strips authority_role to none; the payload keeps the role). Caller holds the lock."""
    envelope = normalize_candidate_envelope({**stored["envelope"], "admission_state": state})
    ctx.ledger.record_candidate(envelope, dict(stored.get("payload", {}), admission_state=state, **extra))


def _admit_judgment_candidate(ctx: Context, args, candidate_id: str, snapshot) -> tuple:
    """Check, plan, write and record under the ledger lock, so two admissions cannot both land."""
    from researchos_kernel.judgments import Judgment
    stored = ctx.ledger.candidates().get(candidate_id) or {}
    object_id = stored.get("payload", {}).get("judgment", {}).get("id", candidate_id)
    # The public starter only shows the planned change (copy fallback below), so it asks nothing first.
    channel = ("invoker_asserted", "copy_fallback") if ctx.runtime_scope == "public_starter" else \
        _decision_channel(ctx.lang, "admit_candidate", object_id, declinable=True)
    if channel[1] == "terminal_declined":
        return _decline_candidate(ctx, args, candidate_id, "admit_candidate", object_id, channel)
    with ctx.ledger.lock():
        stored = _pending_candidate(ctx, candidate_id)
        payload = stored.get("payload", {})
        judgment = Judgment.from_dict(payload["judgment"])
        if any(not item.version for item in judgment.basis):
            raise SystemExit("candidate has an unversioned basis; review current evidence and propose again")
        field_change = {}
        if payload["target"].startswith("commitment:"):
            from researchos_adapters.markdown_repo import parse_portfolio
            cid = payload["target"].split(":", 1)[1]
            before = parse_portfolio((ctx.root / snapshot.portfolio_path).read_text(encoding="utf-8"))
        try:
            relative, new_text, before_sha = plan_admit(ctx.root, snapshot, target=payload["target"], judgment_id=judgment.id,
                                            fields=judgment.fields, basis=judgment.basis, today=ctx.today,
                                            lang=ctx.lang)
        except WritebackError as error:
            raise SystemExit(str(error))  # nothing decided: the target cannot be written
        if payload["target"].startswith("commitment:"):
            after = parse_portfolio(new_text)
            if cid in before and cid in after and before[cid].get("judgments") != after[cid].get("judgments"):
                field_change = {"commitment_id": cid, "field": "judgments",
                                "before_digest": digest(before[cid].get("judgments")),
                                "after_digest": digest(after[cid].get("judgments"))}
        fallback = _copy_fallback(ctx, args, "admit_candidate", relative, new_text)
        if fallback is not None:
            return fallback
        decision = _record_decision(ctx, "admit_candidate", judgment.id, channel, candidate_id)
        admission = _admit_axes(payload.get("admission_state"))

        def record(receipt: dict) -> dict:
            landed = landed_block(ctx.root, relative, judgment.id)
            attempt = _attempt(ctx, decision, "applied", [judgment.id], transaction_id=receipt.get("transaction_id", ""))
            _record_admission(ctx, judgment.id, landed, "admit_candidate", receipt=receipt, admission=admission,
                              candidate_id=candidate_id, decision_id=decision["id"], attempt_id=attempt["id"],
                              commitment_field_change=field_change)
            _record_candidate_state(ctx, stored, admission, receipt_id=receipt.get("receipt_id", ""), landed=landed)
            return landed
        receipt, landed = _land(ctx, decision, relative, new_text, before_sha, record,
                                what=f"admission of {judgment.id}")
    return judgment.id, landed, receipt, admission


def cmd_admit(ctx: Context, args) -> int:
    if getattr(args, "rollback", ""):
        return _cmd_rollback(ctx, args)
    result = ctx.boundary()
    snapshot = result.snapshot
    receipt: dict = {}
    if args.candidate:
        candidate = _pending_candidate(ctx, args.candidate)  # nothing to ask about; each path checks again under its lock
        if candidate.get("envelope", {}).get("candidate_type") == "rule_revision":
            return _admit_rule_revision(ctx, args, args.candidate)
        if candidate.get("envelope", {}).get("candidate_type") == "episode_close":
            return _admit_episode_close(ctx, args, args.candidate)
        admitted = _admit_judgment_candidate(ctx, args, args.candidate, snapshot)
        if isinstance(admitted, int):
            return admitted  # copy fallback or the researcher's refusal: nothing written
        judgment_id, landed, receipt, admission = admitted
        how = "admit_candidate"
    else:
        how = "confirm_existing_block" if args.confirm else "reconfirm_basis"
        judgment_id = args.confirm or args.reconfirm
        if args.reconfirm:
            # A reconfirm re-pins the basis of what was already accepted; it cannot promote a block.
            # An admitted judgment stays admitted; one only confirmed after the fact stays that; one
            # never confirmed has nothing to reconfirm (HJ-8).
            # Classified by the block as it stands: a hand edit since the acceptance is not re-pinned
            # into an admission (a basis change elsewhere does not change the block's own hash).
            current = snapshot.judgments.get(judgment_id)
            block = current.block_hash if current else ""
            if block in result.states["admitted_judgments"].get(judgment_id, set()):
                how = "reconfirm_basis"
            elif block in result.states.get("confirmed_judgments", {}).get(judgment_id, set()):
                how = "reconfirm_confirmed"
            else:
                raise SystemExit(f"this version of {judgment_id} was never admitted or confirmed (it may have been "
                                 f"edited since): confirm it first (ros admit --confirm {judgment_id}) or propose it")
        try:
            if args.confirm:
                judgment = snapshot.judgments.get(args.confirm)
                if not judgment:
                    raise SystemExit(f"judgment not found: {args.confirm}")
                if judgment.block_hash in result.states.get("confirmed_judgments", {}).get(judgment.id, set()) \
                        | result.states["admitted_judgments"].get(judgment.id, set()):
                    raise SystemExit(f"this version of {judgment.id} is already confirmed or admitted")
                landed = {"path": judgment.path, "block_hash": judgment.block_hash, "line": judgment.line}
            else:
                relative, new_text, before_sha = plan_reconfirm(ctx.root, snapshot, judgment_id, ctx.today, lang=ctx.lang)
        except WritebackError as error:
            raise SystemExit(str(error))  # nothing decided: the target is not there or cannot be written
        if args.reconfirm:
            fallback = _copy_fallback(ctx, args, how, relative, new_text)
            if fallback is not None:
                return fallback
        channel = _decision_channel(ctx.lang, how, judgment_id)
        if args.confirm and channel[0] != "researcher_decision":
            # Confirming a block written without admission closes a requirement, which is the researcher's
            # alone, as with ros decide confirm: relayed, it is recorded as asserted and stays open.
            with ctx.ledger.lock():
                _record_decision(ctx, how, judgment_id, channel, operation="retain_if_consistent",
                                 action="confirm_not_applied")
            emit(args, {"judgment_id": judgment_id, "applied": False, "permission_state": channel[0]},
                 t(ctx.lang, "admit.confirm_needs_terminal", id=judgment_id))
            return 1
        post_hoc = how in POST_HOC
        with ctx.ledger.lock():
            decision = _record_decision(ctx, how, judgment_id, channel,
                                        operation="retain_if_consistent" if post_hoc else "admit")
            if args.confirm:
                admission = initial_admission_state()  # not an admission: no decision axis is claimed
                attempt = _attempt(ctx, decision, "confirmed_without_write", [judgment_id], transaction_id="")
                _record_admission(ctx, judgment_id, landed, how, receipt=receipt, admission=admission,
                                  decision_id=decision["id"], attempt_id=attempt["id"])
            else:
                admission = initial_admission_state() if post_hoc else _admit_axes(None)

                def record(receipt: dict) -> dict:
                    landed = landed_block(ctx.root, relative, judgment_id)
                    attempt = _attempt(ctx, decision, "applied", [judgment_id],
                                       transaction_id=receipt.get("transaction_id", ""))
                    _record_admission(ctx, judgment_id, landed, how, receipt=receipt, admission=admission,
                                      decision_id=decision["id"], attempt_id=attempt["id"])
                    return landed
                receipt, landed = _land(ctx, decision, relative, new_text, before_sha, record,
                                        what=f"reconfirmation of {judgment_id}")
    commit = _commit(ctx, landed["path"], f"ros admit: {judgment_id}") if args.commit and how != "confirm_existing_block" else ""
    ctx.refresh()  # local boundary: chained effects are recorded in the same round
    text = t(ctx.lang, "admit.confirmed" if how in POST_HOC else "admit.done",
             id=judgment_id, path=landed["path"], line=landed["line"]) + \
        (t(ctx.lang, "admit.commit", commit=commit) if commit else "")
    if receipt:
        text += t(ctx.lang, "admit.receipt", transaction=receipt.get("transaction_id", ""))
    return emit(args, {"judgment_id": judgment_id, **landed, "commit": commit,
                       "receipt_id": receipt.get("receipt_id", ""),
                       "transaction_id": receipt.get("transaction_id", ""),
                       "admission_state": admission}, text)


def _cmd_rollback(ctx: Context, args) -> int:
    """Undo one admitted write through the same owner that made it."""
    if ctx.runtime_scope != "private":
        # The copy-only starter writes no source, so it may not undo one either, even if an earlier
        # private run left a rollback receipt under the same root.
        raise SystemExit("the public starter is copy-only: it writes no source and rolls none back")
    stored = ctx.root / "06_active_context/work_state/.artifact-rollbacks" / args.rollback / "receipt.json"
    if not stored.is_file():
        raise SystemExit(f"receipt not found: {args.rollback}")
    receipt = json.loads(stored.read_text(encoding="utf-8"))
    channel = _decision_channel(ctx.lang, "rollback", args.rollback)
    with ctx.ledger.lock():
        decision = _record_decision(ctx, "rollback", args.rollback, channel, operation="rollback")
    try:
        result = rollback_artifact_mutation(root=ctx.root, receipt=receipt)
    except FilesystemStagingError as error:
        with ctx.ledger.lock():
            _attempt(ctx, decision, "refused", [], reason=str(error))
        raise SystemExit(f"rollback refused: {error}")
    with ctx.ledger.lock():
        attempt = _attempt(ctx, decision, "applied", [args.rollback], transaction_id=args.rollback)
        # The candidate keeps its history: its mutation axis moves to rolled_back, nothing is
        # deleted. It is found through the effect this transaction recorded, not its latest receipt.
        candidates = ctx.ledger.candidates()
        owners = {row["payload"]["detail"].get("candidate_id") for row in ctx.ledger.trajectory()
                  if row.get("kind") == "effect" and row["payload"].get("detail", {}).get("transaction_id") == args.rollback}
        for candidate_id in sorted(owner for owner in owners if owner in candidates):
            stored = candidates[candidate_id]
            if (stored["payload"].get("admission_state") or {}).get("mutation_state") == "applied":
                _record_candidate_state(ctx, stored, _advance(stored["payload"]["admission_state"],
                                                              ("mutation_state", "rolled_back")),
                                        rolled_back_by=args.rollback)
        effect = ctx.ledger.effect(attempt["id"], [{"object_id": str(change.get("path", "")), "content_id": str(change.get("prior_digest") or ""),
                                         "change": "writeback_rolled_back", "path": str(change.get("path", ""))}
                                        for change in receipt.get("changes", [])],
                                   detail={"transaction_id": args.rollback, "result": result})
        ctx.ledger.check("met", requirement_id="writeback_rollback", supports_effect_ids=[effect["id"]],
                         basis="rollback_receipt_verified")
    return emit(args, {"rolled_back": args.rollback, **result},
                t(ctx.lang, "admit.rolled_back", transaction=args.rollback))


def cmd_decide(ctx: Context, args) -> int:
    issue_id = find_issue(ctx, args.requirement)
    state = ctx.boundary().states["issues"][issue_id]
    payload = {"action": args.action, "reason": args.reason or ""}
    until = ""
    if args.action == "defer":
        payload["until"] = until = _date_arg(args.until, "--until", today=ctx.today, after_today=True).isoformat()
    if args.action == "cancel" and not args.reason:
        raise SystemExit("cancel needs --reason")
    registry = ctx.boundary().requirements.get(issue_id, {})
    if args.action == "confirm" and state["status"] not in OPEN_STATUSES:
        raise SystemExit(f"{issue_id[:10]} is {state['status']}: there is nothing open to confirm")
    if args.action == "confirm" and not str(registry.get("binding", "")).startswith("field:"):
        # HJ-12: confirming is for a judgment-class field written directly. A requirement that needs
        # a check to hold is not closed by saying so (Soul §3); a judgment block is confirmed with
        # `ros admit --confirm`, which records what block version was confirmed.
        raise SystemExit("confirm is for a judgment-class field change (ros admit --confirm <judgment> "
                         "confirms a judgment block; other requirements close on their declared check)")
    bound = requirement_binding(issue_id, state, registry)
    # Soul §1: every decision here is the researcher's only when answered at this machine's terminal;
    # an agent relaying a confirmation is recorded as invoker_asserted, whatever the action.
    channel = _decision_channel(ctx.lang, f"decide:{args.action}", issue_id[:10])
    if args.action in {"cancel", "confirm"} and channel[0] != "researcher_decision":
        # Closing a requirement by saying so is the researcher's alone: relayed, the request is recorded
        # as asserted and nothing moves. The requirement keeps its state until she answers at the terminal.
        with ctx.ledger.lock():
            ctx.ledger.decision("admit" if args.action == "confirm" else "retire", bound=bound,
                                permission_state=channel[0],
                                detail={"action": f"{args.action}_not_applied", "binding": registry.get("binding", ""),
                                        "reason": payload["reason"], "decision_evidence": channel[1]})
        emit(args, {"issue_id": issue_id, **payload, "applied": False, "status": state["status"],
                    "permission_state": channel[0]},
             t(ctx.lang, "decide.needs_terminal", id=issue_id[:10], action=args.action))
        return 1
    with ctx.ledger.lock():
        trigger = state.get("reopen_trigger", "")
        if state["status"] == "waiting" and trigger.startswith("answer:"):
            question = ctx.ledger.asks().get(trigger[7:])
            if question and question.get("state") == "asked":
                ctx.ledger.restate_ask(trigger[7:], question, issue_id, "withdrawn",
                                       detail={"reason": f"decided directly with ros decide {args.action}"})
        if args.action == "defer":
            ctx.ledger.decision("defer", bound=bound, detail={"reason": payload["reason"], "until": until,
                                                               "decision_evidence": channel[1]},
                                permission_state=channel[0])
        if args.action == "confirm":
            ctx.ledger.decision("admit", bound=bound, permission_state=channel[0],
                                detail={"action": "field_confirmed", "binding": registry.get("binding", ""),
                                        "value": state["read_digest"], "reason": payload["reason"],
                                        "decision_evidence": channel[1]})
        to = {"defer": "deferred", "cancel": "cancelled", "reopen": "open", "confirm": "resolved"}[args.action]
        ctx.ledger.transition(bound, to, f"{channel[0]}:{args.action}", summary=state.get("summary", ""),
                              until=until)
    return emit(args, {"issue_id": issue_id, **payload}, t(ctx.lang, "decide.done", id=issue_id[:10], action=args.action))


# -- state / context / rules ---------------------------------------------------------------------
def cmd_state(ctx: Context, args) -> int:
    result = ctx.boundary()
    snapshot = result.snapshot
    commitment = snapshot.commitments.get(args.commitment)
    if not commitment:
        raise SystemExit(f"unknown commitment: {args.commitment}")
    judgments = [j for j in snapshot.judgments.values() if snapshot.commitment_for_judgment(j) == commitment.id]
    evidence = []
    for ref in [commitment.get("source_path")] + [b.ref for j in judgments for b in j.basis]:
        resolved, _ = snapshot.resolve(ref) if ref else ("", "")
        if resolved and resolved not in evidence:
            evidence.append(resolved)
    view = triage(result, ctx.config, ctx.today, only_commitment=commitment.id, attention=_attention(ctx, snapshot))
    open_rows = [row for group in view["today"] + view["decision"] + view["needs_review"] for row in group["items"]]
    data = {"commitment_id": commitment.id, "title": commitment.title, "Q": commitment.get("question"),
            "E": evidence,
            "J": [{"id": j.id, "conclusion": j.conclusion, "path": j.path,
                   "admitted": j.block_hash in result.states["admitted_judgments"].get(j.id, set()),
                   "confirmed_post_hoc": j.block_hash in result.states.get("confirmed_judgments", {}).get(j.id, set())}
                  for j in judgments],
            "B": [{"id": r["short_id"], "summary": r["summary"]} for r in open_rows], "N": commitment.get("next_step")}
    L = ctx.lang
    lines = [t(L, "state.header", title=commitment.title, id=commitment.id, state=commitment.state),
             t(L, "state.q", value=data["Q"] or t(L, "not_written")), t(L, "state.e")]
    lines += [f"  · {ref}" for ref in evidence or [t(L, "none")]]
    lines += [t(L, "state.j")] + [f"  · {j['id']}: {j['conclusion']}" + (
        "" if j["admitted"] else t(L, "state.confirmed_post_hoc") if j["confirmed_post_hoc"] else t(L, "state.unadmitted"))
                               for j in data["J"]] + (["  " + t(L, "none")] if not data["J"] else [])
    lines += [t(L, "state.b")] + [f"  · [{b['id']}] {b['summary']}" for b in data["B"]] \
        + (["  " + t(L, "none")] if not data["B"] else [])
    lines += [t(L, "state.n", value=data["N"] or t(L, "not_written"))]
    return emit(args, data, "\n".join(lines))


SERVICE_NAME = re.compile(r"[A-Za-z0-9_.-]{1,40}")


def _session_service(args) -> tuple:
    """(service, claim source) of where a pack goes. Every source here is a claim, not proof:
    an explicit flag, an environment variable, or the agent host's own marker. None → unknown."""
    import os
    for value, source in ((getattr(args, "service", ""), "flag:--service"),
                          (os.environ.get("RESEARCHOS_SESSION_SERVICE", ""), "env:RESEARCHOS_SESSION_SERVICE"),
                          ("claude_code" if os.environ.get("CLAUDECODE") else "", "env:CLAUDECODE")):
        if value:
            if not SERVICE_NAME.fullmatch(value):
                raise SystemExit("--service must be a short name: letters, digits, _ . - (at most 40)")
            return f"session_agent:{value}", source
    return "", "none"


def cmd_context(ctx: Context, args) -> int:
    """Deliver a bounded context pack to the session Agent and record what left (Soul §4).

    Only public and internal sources are delivered; sensitive ones need the researcher's own
    terminal confirmation; private and unrecognised labels are excluded. Whole sources are
    delivered or excluded, never cut mid-text. Observation and citation stay unknown, and so
    does egress when the destination service cannot be named. The session Agent's own direct
    reads of the repository do not pass through here and are not covered by this receipt."""
    service, service_source = _session_service(args)
    data = build_context_pack(ctx.boundary(), ctx.ledger, ctx.root, ctx.config, ctx.runtime_scope, args.target,
                              service=service, service_source=service_source, surface="cli:ros context",
                              delivery="ros_context:stdout")
    footer = "\n\n" + t(ctx.lang, "context.footer", delivered=len(data["delivered"]), excluded=len(data["excluded"]),
                         truncated=t(ctx.lang, "context.capacity", n=data["dropped"]) if data["dropped"] else "") + \
        t(ctx.lang, "context.receipt", receipt=data["receipt_id"], service=service or t(ctx.lang, "context.no_service"))
    return emit(args, {key: value for key, value in data.items() if key != "dropped"}, data["pack"] + footer)


def _session_state(ctx: Context, session_id: str) -> str:
    row = ctx.ledger.sessions().get(session_id)
    return "none" if row is None else "ended" if row["ended"] else "open"


def cmd_run(ctx: Context, args) -> int:
    """Hand one bounded task to a provider or a copy packet. The executor receives context only via
    the context builder, its output enters only as candidates, and every step lands on the Run and
    Observation axes of the one run-state owner (Kernel §2.1). Nothing is admitted here."""
    from researchos_adapters.provider_adapter import ExecutionRequest, ProviderAdapterError, parse_executor_ref
    try:
        kind, provider_id = parse_executor_ref(args.executor)
    except ProviderAdapterError:
        raise SystemExit("--executor must be provider:<id> or copy_packet")
    if kind not in {"provider", "copy_packet"}:
        raise SystemExit("the session Agent runs `ros context` and `ros propose` itself; `ros run` is for "
                         "provider:<id> or copy_packet")
    if kind == "provider" and ctx.runtime_scope == "public_starter":
        raise SystemExit("the public starter is copy-only: use --executor copy_packet")
    session = _session_for(ctx, args.target, args.session)  # run_requires_session
    if exhausted(*_session_account(ctx, session)):
        raise SystemExit(t(ctx.lang, "budget.stopped", session=session))  # CC-10: a stopped episode dispatches nothing
    adapter = provider_for(ctx.config, ctx.runtime_scope, provider_id) if kind == "provider" else None
    if kind == "provider" and adapter is None:
        # Refused before anything is recorded: no context has left, no run exists.
        raise SystemExit(f"provider:{provider_id} is not dispatchable from ros in this version")
    run_id = f"ros-run-{uuid.uuid4().hex[:12]}"
    task_id = "task:" + hashlib.sha256(f"ros-run:{args.task}:{args.target}".encode("utf-8")).hexdigest()
    # A copy packet is a local file; where it goes next is unknown, so its egress stays unknown (Soul §4).
    service = args.executor if kind == "provider" else ""
    context = build_context_pack(ctx.boundary(), ctx.ledger, ctx.root, ctx.config, ctx.runtime_scope, args.target,
                                 service=service, service_source="executor" if service else "none",
                                 surface=f"cli:ros run {args.executor}", delivery=f"ros_run:{args.executor}",
                                 destination=args.executor, run_id=run_id, task_id=task_id, episode_id=session)
    prompt = t(ctx.lang, "run.prompt", target=args.target, instruction=args.instruction or t(ctx.lang, "run.default")) \
        + "\n\n" + context["pack"]
    ledger = run_ledger(ctx.root, ctx.config, ctx.runtime_scope)
    if ledger is not None:
        ledger.reserve(run_record(run_id, "submitted", task_id))
    with ctx.ledger.lock():
        decision = ctx.ledger.decision("compose", read_set=context["delivered"], episode_id=session, detail={
            "action": "run_dispatched", "task": args.task, "target": args.target, "executor": args.executor,
            "run_id": run_id, "task_id": task_id, "context_receipt_id": context["receipt_id"]})
    if kind == "copy_packet":
        packet = ctx.runtime_dir / "packets" / f"{run_id}.md"
        atomic_write_text(packet, prompt)
        if ledger is not None:
            ledger.claim_dispatch(run_id)  # the packet has left this process: running, effects unknown
        data = {"run_id": run_id, "executor": args.executor, "packet": str(packet), "next": f"ros collect {run_id}",
                "lifecycle": run_lifecycle("open", "running", "delivery_unknown", "none", "unproposed", "unknown")}
        return emit(args, data, t(ctx.lang, "run.packet", path=packet, run=run_id))
    if ledger is not None and not ledger.claim_dispatch(run_id):
        raise SystemExit(f"{run_id} was already dispatched; it is reconciled, never sent twice")
    try:
        execution = adapter.execute(ExecutionRequest(
            prompt=prompt, timeout=int(ctx.config.get("run_timeout", 600)), work_session_id=session, run_id=run_id))
        error = "" if execution.ok else (execution.error_type or "provider_failed")
    except ProviderAdapterError as exc:
        error = exc.code
    except KeyboardInterrupt:
        error = "provider_interrupted"  # launched work may have happened; never silently retry it
    except Exception as exc:  # noqa: BLE001 - any backend failure is recorded, never left running
        error = f"provider_exception:{type(exc).__name__}"
    if error:
        # A failure before launch sent nothing and may be retried; otherwise what the backend did is unknown.
        effects = "none" if launched_nothing(error) else "unknown"
        if ledger is not None:
            ledger.observe(run_record(run_id, "failed", task_id, side_effects=effects))
        with ctx.ledger.lock():
            ctx.ledger.attempt(decision["id"], "failed", [], detail={"executor": args.executor, "run_id": run_id,
                                                                   "error": error, "side_effects": effects})
        data = {"run_id": run_id, "executor": args.executor, "error": error,
                "lifecycle": run_lifecycle("open", "failed", "fresh", "none", "unproposed", effects)}
        emit(args, data, t(ctx.lang, "run.failed", run=run_id, error=error))
        return 1
    return _finish_run(ctx, args, run_id, execution.stdout, decision, ledger, final_if_invalid=True)


def _finish_run(ctx: Context, args, run_id: str, output: str, decision: dict, ledger, *, final_if_invalid: bool) -> int:
    """A returned output is a result, not a change: judgment drafts become candidates through the same
    path as the session Agent's, all or none; anything else is an invalid result, recorded as such."""
    detail = decision["payload"]["detail"]
    executor, target, task_id = detail["executor"], detail["target"], detail.get("task_id", "")
    try:
        created = _propose_judgments(ctx, output, run_id, target, executor=executor, run_id=run_id,
                                     session_id=decision.get("episode_id", ""))
        result, problem = "writeback", ""
    except SystemExit as exc:
        created, result, problem = [], "invalid", str(exc)
    final = bool(created) or final_if_invalid
    if ledger is not None and final:
        # Returned is not harmless: what the executor did besides answering is not ours to certify.
        ledger.observe(run_record(run_id, "completed", task_id, side_effects="unknown"))
    with ctx.ledger.lock():
        ctx.ledger.attempt(decision["id"], "returned" if created else "invalid", created,
                           detail={"executor": executor, "run_id": run_id, "problem": problem,
                                   "retryable": not final})
    session = _session_state(ctx, decision.get("episode_id", ""))
    if session == "none":
        session = "ended"  # its session record is gone: the run is tracked on its own, as after a session ends
    if final:
        lifecycle = run_lifecycle(session, "completed", "fresh", result, "proposed" if created else "unproposed", "unknown")
    else:  # a copy packet whose answer could not be read stays open for a corrected answer
        lifecycle = run_lifecycle(session, "running", "delivery_unknown", "none", "unproposed", "unknown")
    data = {"run_id": run_id, "executor": executor, "candidates": created, "result": result, "problem": problem,
            "lifecycle": lifecycle}
    lines = [t(ctx.lang, "run.done", run=run_id, n=len(created))] + [f"  ros admit {cid}" for cid in created]
    if problem:
        lines.append("  ! " + problem)
    emit(args, data, "\n".join(lines))
    return 0 if created else 1


def cmd_collect(ctx: Context, args) -> int:
    """Bring a copy packet's answer back: only a run this machine dispatched as a copy packet, and
    only until one usable answer has been collected. The label records the route, not who wrote it.
    ``--abandon`` also applies to unresolved provider runs: the researcher states that this run's
    observation stays unknown. That is recorded as the unknown it is (CC-11), not as a result, and
    the episode may then close — a run nobody will collect must not block completion forever."""
    if bool(args.abandon) == bool(args.file):
        raise SystemExit("give either --file <answer> or --abandon --reason <why>")
    with ctx.ledger.lock():
        runs, _ = ctx.ledger.dispatches()
    decision = runs.get(args.run_id)
    if not decision:
        kind = "run" if args.abandon else "copy-packet run"
        raise SystemExit(f"no {kind} {args.run_id} was dispatched here")
    if not args.abandon and decision["payload"]["detail"].get("executor") != "copy_packet":
        raise SystemExit(f"no copy-packet run {args.run_id} was dispatched here")
    # Giving up is possible for as long as the run's observation is unknown; collecting an answer
    # only for as long as none has been collected.
    if args.run_id not in (ctx.ledger.unresolved_runs("") if args.abandon else ctx.ledger.open_runs()):
        raise SystemExit(f"{args.run_id} was already {'resolved' if args.abandon else 'collected'}")
    if args.abandon:
        if not args.reason:
            raise SystemExit("--abandon needs --reason: the record must say why no answer will come")
        return _abandon_run(ctx, args, decision)
    answer = Path(args.file).read_text(encoding="utf-8")
    return _finish_run(ctx, args, args.run_id, answer, decision, run_ledger(ctx.root, ctx.config, ctx.runtime_scope),
                       final_if_invalid=False)


def _abandon_run(ctx: Context, args, decision: dict) -> int:
    """The researcher gives up on a dispatched run. What the executor did stays unknown and is written
    down as unknown; the run stops being an open question for the kernel."""
    detail = decision["payload"]["detail"]
    ledger = run_ledger(ctx.root, ctx.config, ctx.runtime_scope)
    if ledger is not None:
        ledger.observe(run_record(args.run_id, "interrupted", detail.get("task_id", ""), side_effects="unknown"))
    with ctx.ledger.lock():
        ctx.ledger.attempt(decision["id"], "abandoned", [],
                           detail={"executor": detail.get("executor", ""), "run_id": args.run_id,
                                   "reason": args.reason, "side_effects": "unknown", "retryable": False})
    data = {"run_id": args.run_id, "result": "abandoned", "reason": args.reason, "side_effects": "unknown"}
    return emit(args, data, t(ctx.lang, "run.abandoned", run=args.run_id, reason=args.reason))


def cmd_rules(ctx: Context, args) -> int:
    rules, problems = load_rules(ctx.root, ctx.runtime_scope, ROOT)
    result = ctx.boundary()
    counts = {}
    for issue_id, state in result.states["issues"].items():
        if state["status"] in OPEN_STATUSES:
            rule_id = result.requirements.get(issue_id, {}).get("rule_id", "?")
            counts[rule_id] = counts.get(rule_id, 0) + 1
    lines = [t(ctx.lang, "rules.row", id=r["id"], version=r["version"], family=r["family"], executor=r["executor"],
               resolver=r["resolver"], open=counts.get(r["id"], 0)) for r in rules.values()]
    all_problems = problems + result.problems + [row["text"] for row in portfolio_problems(ctx.root, ctx.config,
                                                                                            result.snapshot.commitments)]
    if args.check:
        lines += ["", t(ctx.lang, "rules.problems", n=len(all_problems))] + [f"  · {p}" for p in all_problems]
    data = {"rules": list(rules), "open_by_rule": counts, "problems": all_problems}
    emit(args, data, "\n".join(lines))
    return 1 if args.check and problems else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ros", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", type=date.fromisoformat, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--lang", choices=["zh-CN", "en"], default="")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, parents=[common])  # every command also takes --json

    p = command("today")
    p.add_argument("--for", dest="for_commitment")
    p.add_argument("--all", action="store_true")
    p = command("close")
    p.add_argument("--session")
    p.add_argument("--for", dest="for_commitment")
    p = command("propose")
    p.add_argument("kind", choices=["judgment", "episode-close", "rule"])
    p.add_argument("--file")
    p.add_argument("--target", default="")
    p.add_argument("--reason")
    p.add_argument("--executor", default="session_agent", help="session_agent (default) or script")
    p.add_argument("--session", default="", help="the open session this draft belongs to")
    p = command("run")
    p.add_argument("task", choices=["judgment"])
    p.add_argument("--target", required=True)
    p.add_argument("--executor", required=True, help="provider:<id> or copy_packet")
    p.add_argument("--instruction", default="", help="what the executor should examine")
    p.add_argument("--session", default="", help="the open session this run belongs to")
    p = command("collect")
    p.add_argument("run_id")
    p.add_argument("--file")
    p.add_argument("--abandon", action="store_true", help="give up on this run; its observation stays unknown")
    p.add_argument("--reason", default="")
    p = command("admit")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("candidate", nargs="?")
    group.add_argument("--confirm")
    group.add_argument("--reconfirm")
    p.add_argument("--commit", action="store_true", help="make one small Git commit of the written file")
    group.add_argument("--rollback", metavar="TRANSACTION", help="undo one admitted write by its staging transaction")
    p = command("decide")
    p.add_argument("requirement")
    p.add_argument("action", choices=["defer", "cancel", "reopen", "confirm"])
    p.add_argument("--until")
    p.add_argument("--reason")
    p = command("state")
    p.add_argument("commitment")
    p = command("context")
    p.add_argument("target")
    p.add_argument("--service", default="", help="the service the session Agent runs on (recorded as egress)")
    p = command("rules")
    p.add_argument("--check", action="store_true")
    p = command("receipt")
    p.add_argument("receipt_id")
    p = command("answer")
    p.add_argument("question")
    p.add_argument("option", choices=["satisfied", "unsatisfied", "narrow", "cancel", "defer"])
    p.add_argument("--until", default="")
    p.add_argument("--trigger", default="")
    p.add_argument("--reason", default="")
    p = command("attend")
    p.add_argument("commitment")
    p.add_argument("action", choices=["today", "tomorrow", "date", "park", "complete-step", "undo"])
    p.add_argument("value", nargs="?", default="")
    p.add_argument("--review", default="")
    p.add_argument("--order", type=int, default=0)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not (root / "config" / "ros.json").is_file():
        # Before a config there is no language setting; English unless --lang says otherwise.
        lang = language(args.lang or "en")
        hint = t(lang, "root.missing.demo") if (ROOT / "examples" / "scheduler-demo").is_dir() else ""
        print(t(lang, "root.missing", root=root) + hint, file=sys.stderr)
        return 2
    ctx = Context(root, args.today or date.today(), args.lang)
    handler = {"today": cmd_today, "close": cmd_close, "propose": cmd_propose, "admit": cmd_admit,
               "decide": cmd_decide, "state": cmd_state, "context": cmd_context, "rules": cmd_rules,
               "run": cmd_run, "collect": cmd_collect,
               "receipt": cmd_receipt, "attend": cmd_attend, "answer": cmd_answer}[args.command]
    return handler(ctx, args)


if __name__ == "__main__":
    raise SystemExit(main())
