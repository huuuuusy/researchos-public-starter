"""Decision triage: needs review inside each commitment, plus attention proposals.

Attention has one owner, the attention schedule (Attention Kernel §6). Triage therefore
does not decide what is "today", "this week" or "backlog". It produces two things only:

needs review : the open requirements of each commitment, in the item they belong to;
proposals    : attention actions the evidence suggests (an external deadline or a due
               requirement is near but the item is not in today; an item keeps being carried
               over). A proposal is applied only by an attention action (``ros attend``).

The regions follow the attention projection with the same rules as the Desk (§4.1):
today    : scheduled for today or carried over, plus a real event — an external deadline
           that is today or already passed;
decision : invested items with no attention policy, a step that needs its next step, or a
           review that is due (a long ``unscheduled`` is not a legal resting state).
Closed projects are in neither. Neither region is truncated; order comes from the owner.
Only the ``deadline`` field is an external date (§3.4); ``target_date`` is not an event.
"""

from __future__ import annotations

from datetime import date

from .messages import t

INVESTED = "mainline"
TODAY_STATES = ("today", "carryover")
DECISION_STATES = ("unscheduled", "needs_next_step", "review_due")
LIFECYCLE = {"closed": "completed", "waiting": "waiting", "paused": "paused"}
STALE_CARRYOVER_DAYS = 7


def _visible(state: dict, today: date) -> bool:
    if state["status"] == "open":
        return True
    if state["status"] == "deferred":
        until = state.get("deferred_until", "")
        return bool(until) and until <= today.isoformat()
    return False


def _row(issue_id: str, state: dict, today: date, commitment, **fields) -> dict:
    due = commitment.due_date() if commitment else None
    due_days = fields.pop("due_days", None)
    if due_days is None and due:
        due_days = (due - today).days
    return {"issue_id": issue_id, "short_id": issue_id[:10], "generation": state["generation"],
            "due_days": due_days, "due_date": due.isoformat() if due else "", **fields}


def _items(result, config: dict, today: date, only_commitment: str) -> dict:
    """Open requirements grouped by the commitment they belong to ("" = the research network)."""
    lang = config.get("language", "zh-CN")
    snapshot = result.snapshot
    grouped: dict = {}
    for issue_id, finding in result.findings.items():
        state = result.states["issues"].get(issue_id)
        if not state or not _visible(state, today):
            continue
        if only_commitment and finding.commitment_id != only_commitment:
            continue
        commitment = snapshot.commitments.get(finding.commitment_id)
        grouped.setdefault(finding.commitment_id, []).append(_row(
            issue_id, state, today, commitment, due_days=finding.due_days, rule_id=finding.rule_id,
            summary=finding.summary, details=finding.details, options=finding.options,
            consequence=finding.consequence, only_you=finding.only_you))
    # A requirement whose finding is gone but whose declared check did not hold stays open
    # (Soul §3); it stays visible in its item rather than vanishing with its finding.
    for issue_id, state in sorted(result.states["issues"].items()):
        if issue_id in result.findings or not _visible(state, today):
            continue
        registration = result.requirements.get(issue_id, {})
        if str(registration.get("binding", "")).startswith("coverage:"):
            continue  # coverage unknown is reported with the scope line, not as a decision
        cid = registration.get("commitment_id", "")
        if only_commitment and cid != only_commitment:
            continue
        commitment = snapshot.commitments.get(cid)
        # HJ-12: a judgment-class field written directly is waiting for the researcher's confirmation,
        # not for a check that stopped holding. Confirming is the first action offered; cancelling it
        # is possible but is a decision to leave the write unconfirmed, and says so.
        field = str(registration.get("binding", "")).startswith("field:")
        options = [{"label": t(lang, "field.opt.confirm"), "action": f"ros decide {issue_id[:10]} confirm"}] if field else []
        options += [{"label": t(lang, "field.opt.cancel") if field else t(lang, "held.opt.cancel"),
                     "action": f"ros decide {issue_id[:10]} cancel --reason {t(lang, 'ph.reason')}"},
                    {"label": t(lang, "opt.defer.short"),
                     "action": f"ros decide {issue_id[:10]} defer --until {t(lang, 'ph.date')}"}]
        grouped.setdefault(cid, []).append(_row(
            issue_id, state, today, commitment, rule_id=registration.get("rule_id", ""),
            summary=state.get("summary", "") or registration.get("binding", ""),
            details=[t(lang, "field.detail" if field else "held.detail")],
            options=options, consequence=0, only_you=True))
    for rows in grouped.values():
        rows.sort(key=lambda r: (r["due_days"] if r["due_days"] is not None else 10**6, -r["consequence"],
                                 r["issue_id"]))
    return grouped


def _deadline(commitment) -> date | None:
    value = commitment.get("deadline")
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def triage(result, config: dict, today: date | None = None, only_commitment: str = "",
           attention: dict | None = None) -> dict:
    """``attention`` maps commitment id -> its attention projection (state, dates, order)."""
    today = today or date.today()
    lang = config.get("language", "zh-CN")
    immediate_days = int(config.get("immediate_deadline_days", 3))
    attention = attention or {}
    snapshot = result.snapshot
    grouped = _items(result, config, today, only_commitment)

    today_rows, decision_rows, proposals, elsewhere = [], [], [], []
    for cid, commitment in sorted(snapshot.commitments.items()):
        if only_commitment and cid != only_commitment:
            continue
        projected = dict(attention.get(cid) or {})
        lifecycle = projected.get("lifecycle_state") or LIFECYCLE.get(commitment.state, "open")
        state = projected.get("attention_state", "unscheduled")
        items = grouped.get(cid, [])
        if lifecycle == "completed":
            if items:
                elsewhere.append({"commitment_id": cid, "commitment_title": commitment.title,
                                  "attention_state": "completed", "items": items})
            continue
        deadline = _deadline(commitment)
        days = (deadline - today).days if deadline else None
        group = {"commitment_id": cid, "commitment_title": commitment.title, "attention_state": state,
                 "lifecycle_state": lifecycle, "attention_date": projected.get("attention_date", ""),
                 "deadline": deadline.isoformat() if deadline else "",
                 "today_order": int(projected.get("today_order", 0) or 0),
                 "carryover_days": int(projected.get("carryover_days", 0) or 0), "items": items}
        in_today = (lifecycle == "open" and state in TODAY_STATES) or (days is not None and days <= 0)
        in_decision = not in_today and (
            (commitment.state == INVESTED and lifecycle == "open" and state in DECISION_STATES)
            or (lifecycle in {"waiting", "paused"} and state == "review_due"))
        if in_today:
            today_rows.append(group)
        elif in_decision:
            decision_rows.append(group)
        elif items:
            elsewhere.append(group)
        if not in_today:
            due_items = [row for row in items if row["due_days"] is not None and row["due_days"] <= immediate_days]
            if days is not None and days <= immediate_days:
                reason = t(lang, "proposal.deadline", days=days, date=deadline.isoformat())
            elif due_items:
                reason = t(lang, "proposal.requirement", summary=due_items[0]["summary"], days=due_items[0]["due_days"])
            else:
                reason = ""
            if reason:
                proposals.append({"commitment_id": cid, "commitment_title": commitment.title, "action": "today",
                                  "reason": reason, "command": f"ros attend {cid} today"})
        if state == "carryover" and group["carryover_days"] >= STALE_CARRYOVER_DAYS:
            proposals.append({"commitment_id": cid, "commitment_title": commitment.title, "action": "date_or_park",
                              "reason": t(lang, "proposal.carryover", days=group["carryover_days"]),
                              "command": f"ros attend {cid} date {t(lang, 'ph.date')}  |  ros attend {cid} park"})
    order = lambda g: (g["today_order"] or 10**4, g["deadline"] or "9999", g["commitment_id"])
    today_rows.sort(key=order)
    decision_rows.sort(key=order)
    return {"today": today_rows, "decision": decision_rows, "proposals": proposals, "needs_review": elsewhere,
            "network": grouped.get("", []), "total_open": sum(len(rows) for rows in grouped.values())}
