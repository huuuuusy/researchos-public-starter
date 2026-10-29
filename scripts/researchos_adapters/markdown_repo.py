"""Read the research graph G from Markdown cards and the commitment portfolio.

A node has a stable reference (repository path, or ``commitment:<id>``), an id
(frontmatter ``id`` or the file stem), a sensitivity, and a *version*: the hash
of its content with judgment blocks removed. Judgment blocks and frontmatter
``relations:`` are parsed here; nothing is written.

Hashes are cached by (mtime_ns, size) so a boundary over thousands of cards stays
fast. The cache lives in the kernel cursor and is safe to delete.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from researchos_kernel.judgments import Judgment, parse_judgments, strip_judgments
from researchos_kernel.messages import t
from researchos_kernel.triage import LIFECYCLE

CACHE_SCHEMA = "researchos-ros-snapshot-cache-v3"  # v2 containment and episode fields; v3 closure receipt
ITEM_FIELD = re.compile(r"^- ([a-z0-9_]+):[ \t]*(.*)$", re.MULTILINE)
RESPONSIBILITIES = ("lead", "support")


@dataclass
class Node:
    ref: str
    path: str
    id: str
    kind: str
    title: str
    sensitivity: str
    version: str
    file_sha: str
    relations: list = field(default_factory=list)
    declared_scope: str = ""     # frontmatter `scope:`; empty means derived from the location
    episode_state: str = ""      # frontmatter `episode_state:`; empty means this is not an episode
    interface: bool = False      # frontmatter `interface: true`: citable from another scope
    closure_receipt: str = ""    # frontmatter `episode_closure_receipt:`; written only by ros admit


@dataclass
class Commitment:
    id: str
    title: str
    fields: dict
    version: str
    line: int
    span: tuple = (-1, -1)  # (start, end) of its block in the whole portfolio text: where a writer edits

    def get(self, key: str, default: str = "") -> str:
        return str(self.fields.get(key, default) or default).strip()

    @property
    def state(self) -> str:
        return self.get("state").lower()

    def due_date(self) -> date | None:
        for key in ("deadline", "target_date"):
            value = self.get(key)
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    continue
        return None

    def judgment_ids(self) -> list:
        return [part for part in re.split(r"[\s,，;；、]+", self.get("judgments")) if part]


@dataclass
class Snapshot:
    root: Path
    nodes: dict
    commitments: dict
    judgments: dict
    problems: list
    portfolio_path: str
    ambiguous_commitments: frozenset = frozenset()  # ids declared more than once: identity unknown

    def resolve(self, ref: str) -> tuple:
        """Return (canonical_ref, version) or ("", "") when unresolved or ambiguous."""
        ref = ref.strip()
        if ref.startswith("commitment:"):
            commitment = self.commitments.get(ref.split(":", 1)[1])
            return (f"commitment:{commitment.id}", commitment.version) if commitment else ("", "")
        if ref in self.nodes:
            return ref, self.nodes[ref].version
        slug = ref.split(":", 1)[1] if ":" in ref and "/" not in ref else ref
        matches = [node for node in self.nodes.values() if node.id == slug or Path(node.path).stem == slug]
        if len(matches) == 1:
            return matches[0].ref, matches[0].version
        return "", ""

    def title_of(self, ref: str) -> str:
        if ref.startswith("commitment:"):
            commitment = self.commitments.get(ref.split(":", 1)[1])
            return commitment.title if commitment else ref
        node = self.nodes.get(ref)
        return node.title if node else ref

    def commitment_for_judgment(self, judgment: Judgment) -> str:
        """A judgment belongs to a commitment by an explicit field, by being listed in the
        commitment's ``judgments`` field, or by sitting inside its portfolio block."""
        if judgment.commitment:
            return judgment.commitment
        for commitment in self.commitments.values():
            if judgment.id in commitment.judgment_ids():
                return commitment.id
        if judgment.path == self.portfolio_path:
            owner = ""
            for commitment in sorted(self.commitments.values(), key=lambda c: c.line):
                if commitment.line <= judgment.line:
                    owner = commitment.id
            return owner
        return ""

    def changed_after(self, source: str, verified: date) -> str:
        """The day ``source`` (a file, or the newest file under a directory) last changed, when that is
        after ``verified``; "" otherwise or when it is absent or not a repository path."""
        if not source or os.path.isabs(source):
            return ""
        path = self.root / source
        if not path.exists():
            return ""
        newest = path.stat().st_mtime
        if path.is_dir():
            newest = max((child.stat().st_mtime for child in path.rglob("*") if child.is_file()), default=newest)
        changed = datetime.fromtimestamp(newest, tz=timezone.utc).date()
        return changed.isoformat() if changed > verified else ""

    def version_map(self) -> dict:
        versions = {ref: node.version for ref, node in self.nodes.items()}
        versions.update({f"commitment:{cid}": c.version for cid, c in self.commitments.items()})
        return versions


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_frontmatter(text: str) -> tuple:
    """Return (scalars, relations, body). Supports the small YAML subset cards use."""
    if not text.startswith("---"):
        return {}, [], text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, [], text
    header = text[3:end].strip("\n").splitlines()
    body = text[end + 4:]
    scalars, relations = {}, []
    index = 0
    while index < len(header):
        line = header[index]
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            index += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key == "relations" and not value:
            index += 1
            current = None
            nested = None
            while index < len(header) and (header[index].startswith(" ") or not header[index].strip()):
                row = header[index]
                item = re.match(r"^\s*-\s+([A-Za-z0-9_]+):\s*(.*)$", row)
                pair = re.match(r"^(\s+)([A-Za-z0-9_]+):\s*(.*)$", row)
                if item:
                    current = {item.group(1): _scalar(item.group(2))}
                    relations.append(current)
                    nested = None
                elif pair and current is not None:
                    if not pair.group(3).strip():
                        nested = {}
                        current[pair.group(2)] = nested
                    elif nested is not None and len(pair.group(1)) > 4:
                        nested[pair.group(2)] = _scalar(pair.group(3))
                    else:
                        current[pair.group(2)] = _scalar(pair.group(3))
                        nested = None
                index += 1
            continue
        scalars[key] = _scalar(value)
        index += 1
    return scalars, relations, body


def _scalar(value: str) -> str:
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def _title(scalars: dict, body: str, path: str) -> str:
    if scalars.get("title"):
        return str(scalars["title"])
    heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return heading.group(1).strip() if heading else Path(path).stem


def _kind(path: str) -> str:
    parts = path.split("/")
    if parts[0] == "01_knowledge" and len(parts) > 2:
        return {"papers": "paper", "projects": "project", "talks": "talk"}.get(parts[1], "knowledge")
    return {"00_identity": "identity", "02_decisions": "decision", "03_cognition": "cognition",
            "04_people": "person", "06_active_context": "context", "distilled": "distilled"}.get(parts[0], "card")


PORTFOLIO_SECTION = "Responsibility Items"


def _items_section(text: str) -> tuple:
    """(offset, text) of the commitment list: the ``## Responsibility Items`` section when present.
    Examples and templates elsewhere in the file are not commitments."""
    heading = re.search(rf"^## {re.escape(PORTFOLIO_SECTION)}\s*$", text, re.MULTILINE)
    if not heading:
        return 0, text
    rest = re.search(r"^## ", text[heading.end():], re.MULTILINE)
    end = heading.end() + rest.start() if rest else len(text)
    return heading.start(), text[heading.start():end]


def ambiguous_ids(text: str) -> frozenset:
    """Commitment ids whose identity is not unique in the commitment list (declared in two blocks,
    or by a block that declares several ids)."""
    return _parse_portfolio(text, [])[1]


def parse_portfolio(text: str, problems: list | None = None) -> dict:
    return _parse_portfolio(text, problems if problems is not None else [])[0]


def _parse_portfolio(text: str, problems: list) -> tuple:
    """Commitments are ``### Title`` blocks carrying ``- id:`` fields.

    One commitment has one current disposition and one next step (CC-5), so nothing is guessed:
    two blocks with one id are both left out, and a field given twice in a block has no value
    until one is removed. Each case is reported in ``problems``."""
    commitments, seen = {}, {}
    text_all = text
    offset, text = _items_section(text_all)
    positions = [m for m in re.finditer(r"^### (.+)$", text, re.MULTILINE)]
    for index, match in enumerate(positions):
        end = positions[index + 1].start() if index + 1 < len(positions) else len(text)
        next_section = re.search(r"^## ", text[match.end():end], re.MULTILINE)
        if next_section:
            end = match.end() + next_section.start()
        block = text[match.start():end]
        line = text_all.count("\n", 0, offset + match.start()) + 1
        fields, repeated = {}, []
        for m in ITEM_FIELD.finditer(block):
            if m.group(1) in fields:
                repeated.append(m.group(1))
            fields[m.group(1)] = _scalar(m.group(2))
        commitment_id = fields.get("id", "").strip()
        if "id" in repeated:
            ids = sorted({m.group(2).strip() for m in ITEM_FIELD.finditer(block) if m.group(1) == "id"})
            problems.append(f"portfolio:{line}: one block declares id more than once ({', '.join(ids)}); "
                            "it is not read until it has one id")
            for each in ids:
                seen.setdefault(each, []).append(line)  # its ids are ambiguous wherever else they appear
            continue
        if not commitment_id:
            continue
        for key in sorted(set(repeated)):
            fields[key] = ""
            problems.append(f"portfolio:{line}: {commitment_id} gives {key} more than once; it has no value until one is removed")
        seen.setdefault(commitment_id, []).append(line)
        commitments[commitment_id] = Commitment(
            id=commitment_id, title=match.group(1).strip(), fields=fields,
            version=sha256_text(re.sub(r"^- judgments:.*\n?", "", strip_judgments(block), flags=re.MULTILINE).strip()), line=line,
            span=(offset + match.start(), offset + end),
        )
    ambiguous = set()
    for commitment_id, lines in seen.items():
        if len(lines) > 1 or commitment_id not in commitments:
            ambiguous.add(commitment_id)
            commitments.pop(commitment_id, None)
            if len(lines) == 1:
                continue  # only the self-contradicting block itself: already reported
            problems.append(f"portfolio: commitment id {commitment_id} is declared {len(lines)} times (lines "
                            f"{', '.join(map(str, lines))}); none is read until the identity is unique")
    return commitments, frozenset(ambiguous)


def portfolio_problems(root: Path, config: dict, commitments: dict) -> list:
    """Fields the checks cannot use, which would otherwise drop a commitment from `today` without a word.

    A state outside ``active_states`` and the lifecycle states is skipped by every rule; a responsibility
    other than lead or support is never asked for its question; a ``last_verified`` or ``stale_after_days``
    the status check cannot read is never found stale; a ``source_path`` that does not exist is never found
    changed. A missing portfolio file is one row. Each row carries its data and its text in the configured
    language."""
    lang, portfolio = config.get("language", "zh-CN"), config.get("portfolio", "")
    if portfolio and not (root / portfolio).is_file():
        return [{"id": "", "line": 0, "field": "portfolio", "value": portfolio, "valid": [],
                 "text": t(lang, "portfolio.portfolio", value=portfolio)}]
    states = list(dict.fromkeys([*config.get("active_states", []), *LIFECYCLE]))
    rows = []
    for commitment in sorted(commitments.values(), key=lambda c: c.line):
        unusable = []
        if commitment.state not in states:
            unusable.append(("state", states))
        if commitment.get("responsibility") and commitment.get("responsibility") not in RESPONSIBILITIES:
            unusable.append(("responsibility", RESPONSIBILITIES))
        for name, read in (("last_verified", date.fromisoformat), ("stale_after_days", int)):
            try:
                if commitment.get(name):
                    read(commitment.get(name))
            except ValueError:
                unusable.append((name, ()))
        if commitment.get("source_path") and not (root / commitment.get("source_path")).exists():
            unusable.append(("source_path", ()))
        rows += [{"id": commitment.id, "line": commitment.line, "field": name, "value": commitment.get(name),
                  "valid": list(valid), "text": t(lang, f"portfolio.{name}", id=commitment.id, line=commitment.line,
                                                  value=commitment.get(name) or t(lang, "portfolio.missing"),
                                                  valid=", ".join(valid))} for name, valid in unusable]
    return rows


def _iter_markdown(root: Path, roots: list, exclude: list):
    for top in roots:
        base = root / top
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            if any(relative.startswith(prefix) for prefix in exclude) or path.is_symlink():
                continue
            yield path, relative


def build_snapshot(root: Path, config: dict, cache: dict | None = None) -> tuple:
    """Return (snapshot, new_cache). ``cache`` maps path -> cached parse keyed by stat."""
    cache = cache if isinstance(cache, dict) and cache.get("schema_id") == CACHE_SCHEMA else {}
    old_files = cache.get("files", {})
    files, nodes, judgments, problems = {}, {}, {}, []
    portfolio_path = config.get("portfolio", "")
    for path, relative in _iter_markdown(root, config.get("graph_roots", []), config.get("exclude", [])):
        stat = path.stat()
        key = [stat.st_mtime_ns, stat.st_size]
        entry = old_files.get(relative)
        if not entry or entry.get("stat") != key:
            raw = path.read_bytes()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                problems.append(f"{relative}: not UTF-8")
                continue
            scalars, relations, body = split_frontmatter(text)
            found, found_problems = parse_judgments(text, relative)
            entry = {
                "stat": key, "file_sha": hashlib.sha256(raw).hexdigest(),
                "version": sha256_text(_strip_relations(strip_judgments(text))),
                "id": str(scalars.get("id") or Path(relative).stem), "title": _title(scalars, body, relative),
                "sensitivity": str(scalars.get("sensitivity") or "internal").lower(),
                "declared_scope": str(scalars.get("scope") or "").strip(),
                "episode_state": str(scalars.get("episode_state") or "").strip().lower(),
                "closure_receipt": str(scalars.get("episode_closure_receipt") or "").strip(),
                "interface": str(scalars.get("interface") or "").strip().lower() in {"true", "yes"},
                "relations": relations, "judgments": [j.to_dict() for j in found], "problems": list(found_problems),
                "portfolio_text": text if relative == portfolio_path else None,
            }
        files[relative] = entry
        problems.extend(entry.get("problems", []))
        nodes[relative] = Node(
            ref=relative, path=relative, id=entry["id"], kind=_kind(relative), title=entry["title"],
            sensitivity=entry["sensitivity"], version=entry["version"], file_sha=entry["file_sha"],
            relations=entry["relations"], declared_scope=entry.get("declared_scope", ""),
            episode_state=entry.get("episode_state", ""), interface=bool(entry.get("interface", False)),
            closure_receipt=entry.get("closure_receipt", ""),
        )
        for data in entry["judgments"]:
            judgment = Judgment.from_dict(data)
            if judgment.id in judgments:
                problems.append(f"{relative}:{judgment.line}: duplicate judgment id {judgment.id}")
                continue
            judgments[judgment.id] = judgment
    commitments = {}
    portfolio_entry = files.get(portfolio_path)
    if portfolio_entry:
        text = portfolio_entry.get("portfolio_text")
        if text is None:
            text = (root / portfolio_path).read_text(encoding="utf-8")
        commitments = parse_portfolio(text, problems)
        nodes.pop(portfolio_path, None)  # the portfolio is represented by its commitments
    snapshot = Snapshot(root=root, nodes=nodes, commitments=commitments, judgments=judgments,
                        problems=problems, portfolio_path=portfolio_path,
                        ambiguous_commitments=ambiguous_ids(text) if portfolio_entry else frozenset())
    for entry in files.values():
        entry["portfolio_text"] = None
    return snapshot, {"schema_id": CACHE_SCHEMA, "files": files}


def _strip_relations(text: str) -> str:
    """Confirmed edge versions are excluded from node versions (plan v4 appendix §2.1)."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    header, rest = text[:end], text[end:]
    header = re.sub(r"^relations:\s*\n(?:(?:[ \t]+.*|)\n)*", "", header + "\n", flags=re.MULTILINE)
    return header.rstrip("\n") + rest


def commitment_block_span(text: str, commitment_id: str) -> tuple:
    """(start, end) character span of the one commitment block with this id, or (-1, -1) when there
    is none — or more than one: a writer must not pick one of two blocks the reader refuses (CC-5).
    The span is the one the reader parsed, so a writer edits exactly the block that was read."""
    commitment = parse_portfolio(text).get(commitment_id)
    return commitment.span if commitment else (-1, -1)


def load_config(root: Path) -> dict:
    path = root / "config" / "ros.json"
    return json.loads(path.read_text(encoding="utf-8"))
