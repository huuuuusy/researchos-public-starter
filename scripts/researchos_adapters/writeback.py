"""Admission write plans: the only code that composes judgment blocks and episode closures.

Nothing here writes. Each ``plan_*`` returns (path, new text, preimage digest) for one file;
the caller lands it through the staging owner (``ros._land``), which writes atomically and
checks the preimage. ``landed`` and ``closed_episode`` then re-read the file and parse it
back, so the caller records an effect bound to the exact block hash (or closure) that landed.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

from researchos_kernel.judgments import BasisRef, parse_judgments, render_judgment

from .markdown_repo import split_frontmatter, commitment_block_span

SECTION = "## Judgments"


class WritebackError(ValueError):
    pass


def pin_basis(snapshot, basis: tuple, *, refresh: bool) -> tuple:
    """Pin a basis, rejecting stale pins unless this is an explicit reconfirmation."""
    pinned, unresolved = [], []
    for item in basis:
        ref, version = snapshot.resolve(item.ref)
        if not ref:
            unresolved.append(item.ref)
            continue
        if item.version and not version.startswith(item.version) and not refresh:
            raise WritebackError(f"basis version changed: {item.ref}; review the current evidence and propose again")
        keep = item.version and not refresh
        pinned.append(BasisRef(ref, item.version if keep else version[:8]))
    if unresolved:
        raise WritebackError("unresolved basis: " + ", ".join(unresolved))
    return tuple(pinned)


def _insert_into_card(text: str, block: str) -> str:
    match = re.search(rf"^{re.escape(SECTION)}\s*$", text, re.MULTILINE)
    if not match:
        return text.rstrip("\n") + f"\n\n{SECTION}\n\n{block}\n"
    rest = text[match.end():]
    next_heading = re.search(r"^#{1,2} ", rest, re.MULTILINE)
    cut = match.end() + (next_heading.start() if next_heading else len(rest))
    head, tail = text[:cut].rstrip("\n"), text[cut:]
    return f"{head}\n\n{block}\n" + (f"\n{tail.lstrip(chr(10))}" if tail.strip() else "")


def _insert_into_commitment(text: str, commitment_id: str, judgment_id: str, block: str) -> str:
    start, end = commitment_block_span(text, commitment_id)
    if start < 0:
        raise WritebackError(f"commitment not found: {commitment_id}")
    item = text[start:end]
    field = re.search(r"^- judgments:[ \t]*(.*)$", item, re.MULTILINE)
    if field:
        ids = [part for part in re.split(r"[\s,，;；、]+", field.group(1)) if part]
        if judgment_id not in ids:
            ids.append(judgment_id)
        item = item[:field.start()] + "- judgments: " + ", ".join(ids) + item[field.end():]
    else:
        fields = list(re.finditer(r"^- [a-z0-9_]+:.*$", item, re.MULTILINE))
        if not fields:
            raise WritebackError(f"commitment block has no fields: {commitment_id}")
        cut = fields[-1].end()
        item = item[:cut] + f"\n- judgments: {judgment_id}" + item[cut:]
    item = item.rstrip("\n") + f"\n\n{block}\n\n"
    return text[:start] + item + text[end:]


def plan_admit(root: Path, snapshot, *, target: str, judgment_id: str, fields: dict, basis: tuple,
               today: date, lang: str = "zh-CN") -> tuple:
    """Return (path, new text, preimage digest); only the staging owner writes."""
    fields = dict(fields)
    fields["confirmed"] = fields.get("confirmed") or today.isoformat()
    if judgment_id in snapshot.judgments:
        raise WritebackError(f"judgment id already exists: {judgment_id}")
    pinned = pin_basis(snapshot, basis, refresh=False)
    block = render_judgment(judgment_id, fields, pinned, lang)
    if target.startswith("commitment:"):
        path = root / snapshot.portfolio_path
        commitment_id = target.split(":", 1)[1]
        before = path.read_bytes()
        new_text = _insert_into_commitment(before.decode("utf-8"), commitment_id, judgment_id, block)
    else:
        path = root / target
        if not path.is_file() or path.suffix != ".md":
            raise WritebackError(f"target card not found: {target}")
        before = path.read_bytes()
        new_text = _insert_into_card(before.decode("utf-8"), block)
    return path.relative_to(root).as_posix(), new_text, hashlib.sha256(before).hexdigest()


def plan_reconfirm(root: Path, snapshot, judgment_id: str, today: date, lang: str = "zh-CN") -> tuple:
    """Return (path, new text, preimage digest) for an explicit re-confirmation."""
    judgment = snapshot.judgments.get(judgment_id)
    if not judgment:
        raise WritebackError(f"judgment not found: {judgment_id}")
    path = root / judgment.path
    before = path.read_bytes()
    text = before.decode("utf-8")
    fields = dict(judgment.fields)
    fields["confirmed"] = today.isoformat()
    # The rewritten block keeps the labels it was written with; only its basis pins and date change.
    if re.search(r"^>\s*结论\s*[:：]", judgment.raw, re.MULTILINE):
        lang = "zh-CN"
    elif re.search(r"^>\s*conclusion\s*[:：]", judgment.raw, re.MULTILINE | re.IGNORECASE):
        lang = "en"
    block = render_judgment(judgment_id, fields, pin_basis(snapshot, judgment.basis, refresh=True), lang)
    raw = judgment.raw if judgment.raw in text else judgment.raw.replace("\n", "\r\n")
    if text.count(raw) != 1:
        raise WritebackError(f"judgment block changed on disk; run ros today first: {judgment_id}")
    if "\r\n" in raw:
        block = block.replace("\n", "\r\n")
    return judgment.path, text.replace(raw, block, 1), hashlib.sha256(before).hexdigest()


def landed(root: Path, relative: str, judgment_id: str) -> dict:
    """Parse a written block back from disk; the effect is recorded only for what actually landed."""
    found, _ = parse_judgments((root / relative).read_text(encoding="utf-8"), relative)
    for judgment in found:
        if judgment.id == judgment_id:
            return {"path": relative, "block_hash": judgment.block_hash, "line": judgment.line}
    raise WritebackError(f"written block could not be parsed back: {judgment_id}")


def _episode_header(text: str) -> tuple:
    """Return (lines, start, end, state_index, value) of an episode's frontmatter, or raise.

    Propose and admit use this one reader, so what one accepts the other can write."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise WritebackError("not an episode (no frontmatter)")
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), -1)
    if end < 0:
        raise WritebackError("not an episode (unterminated frontmatter)")
    states = [i for i in range(1, end) if re.match(r"episode_state\s*:", lines[i])]
    if len(states) != 1:
        raise WritebackError(f"not an episode (expected one episode_state field, found {len(states)})")
    value = lines[states[0]].split(":", 1)[1].split(" #", 1)[0].strip().strip("\"'").lower()
    if value not in {"open", "closed"}:
        raise WritebackError(f"episode_state must be open or closed, not {value!r}")
    return lines, end, states[0], value


def episode_state_of(root: Path, relative: str) -> str:
    """The episode_state an admission would act on; raises if the frontmatter is not writable."""
    path = root / relative
    if not path.is_file() or path.suffix != ".md":
        raise WritebackError(f"episode not found: {relative}")
    with open(path, encoding="utf-8", newline="") as handle:
        return _episode_header(handle.read())[3]


def plan_episode_close(root: Path, relative: str, receipt_id: str) -> tuple:
    """Return (path, new text, preimage digest) closing one episode, without writing.

    Only frontmatter lines change: ``episode_state`` becomes ``closed``, ``episode_closure_receipt``
    names the receipt (a stale one is replaced). Line endings and the body are kept byte for byte,
    and the planned text must parse back before anything is written."""
    path = root / relative
    if not path.is_file() or path.suffix != ".md":
        raise WritebackError(f"episode not found: {relative}")
    before = path.read_bytes()
    text = before.decode("utf-8")
    lines, end, state_index, _ = _episode_header(text)
    eol = "\r\n" if lines[state_index].endswith("\r\n") else "\n"
    header = []
    for index in range(1, end):
        if index == state_index:
            header += [f"episode_state: closed{eol}", f"episode_closure_receipt: {receipt_id}{eol}"]
        elif not re.match(r"episode_closure_receipt\s*:", lines[index]):
            header.append(lines[index])
    new_text = "".join([lines[0]] + header + lines[end:])
    scalars, _, _ = split_frontmatter(new_text.replace("\r\n", "\n"))
    if (str(scalars.get("episode_state") or "").strip().lower() != "closed"
            or str(scalars.get("episode_closure_receipt") or "").strip() != receipt_id):
        raise WritebackError(f"planned closure would not parse back; nothing written: {relative}")
    return relative, new_text, hashlib.sha256(before).hexdigest()


def closed_episode(root: Path, relative: str, receipt_id: str) -> dict:
    """Parse a closure back from disk; the effect is recorded only for what actually landed."""
    with open(root / relative, encoding="utf-8", newline="") as handle:
        scalars, _, _ = split_frontmatter(handle.read().replace("\r\n", "\n"))
    if (str(scalars.get("episode_state") or "").strip().lower() != "closed"
            or str(scalars.get("episode_closure_receipt") or "").strip() != receipt_id):
        raise WritebackError(f"written closure could not be parsed back: {relative}")
    return {"path": relative, "episode_state": "closed", "closure_receipt": receipt_id}
