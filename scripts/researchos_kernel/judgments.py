"""Judgment blocks: the first-class, evidence-bound judgment object (plan v4 §4.1).

    > [!judgment] j-occlusion-scope
    > 结论：先比较遮挡条件下的迁移，不扩大数据集。
    > 依据：01_knowledge/projects/example-project.md@3f2a91c0 · commitment:example-paper@9c1b44e7
    > 适用条件：返修仍在进行；没有新增外部数据
    > 放弃的选项：同步扩充数据集
    > 确认：2026-09-20

English keys (Conclusion, Basis, Conditions, Rejected, Confirmed, Commitment) are
accepted as well. Blocks inside fenced code are examples and are ignored.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

START = re.compile(r"^>\s*\[!judgment\]\s*([A-Za-z0-9][A-Za-z0-9._-]{0,120})\s*$")
KEY_LINE = re.compile(r"^>\s*([^:：]{1,20})[:：]\s*(.*)$")
REF = re.compile(r"^(?P<ref>[^@\s]+?)(?:@(?P<version>[0-9a-f]{7,64}))?$")
SPLIT = re.compile(r"\s*(?:·|、|，|；|,|;)\s*")
FENCE = re.compile(r"^\s*(```|~~~)")

KEYS = {
    "结论": "conclusion", "conclusion": "conclusion",
    "依据": "basis", "basis": "basis",
    "适用条件": "conditions", "conditions": "conditions",
    "放弃的选项": "rejected", "rejected": "rejected", "rejected options": "rejected",
    "确认": "confirmed", "confirmed": "confirmed",
    "承诺": "commitment", "commitment": "commitment",
}
LABELS_ZH = (("conclusion", "结论"), ("basis", "依据"), ("conditions", "适用条件"),
             ("rejected", "放弃的选项"), ("commitment", "承诺"), ("confirmed", "确认"))
LABELS_EN = (("conclusion", "Conclusion"), ("basis", "Basis"), ("conditions", "Conditions"),
             ("rejected", "Rejected"), ("commitment", "Commitment"), ("confirmed", "Confirmed"))


@dataclass(frozen=True)
class BasisRef:
    ref: str
    version: str = ""

    def text(self) -> str:
        return f"{self.ref}@{self.version}" if self.version else self.ref


@dataclass(frozen=True)
class Judgment:
    id: str
    path: str
    line: int
    fields: dict = field(default_factory=dict)
    basis: tuple = ()
    block_hash: str = ""
    raw: str = ""

    @property
    def conclusion(self) -> str:
        return self.fields.get("conclusion", "")

    @property
    def commitment(self) -> str:
        return self.fields.get("commitment", "")

    def to_dict(self) -> dict:
        return {"id": self.id, "path": self.path, "line": self.line, "fields": dict(self.fields),
                "basis": [[b.ref, b.version] for b in self.basis], "block_hash": self.block_hash, "raw": self.raw}

    @classmethod
    def from_dict(cls, data: dict) -> "Judgment":
        return cls(id=data["id"], path=data["path"], line=int(data["line"]), fields=dict(data["fields"]),
                   basis=tuple(BasisRef(r, v) for r, v in data["basis"]), block_hash=data["block_hash"],
                   raw=data.get("raw", ""))


def parse_basis(value: str) -> tuple:
    refs = []
    for part in SPLIT.split(value.strip()):
        part = part.strip().strip("`")
        if not part:
            continue
        match = REF.match(part)
        if match:
            refs.append(BasisRef(match.group("ref"), match.group("version") or ""))
    return tuple(refs)


def block_hash(lines: list) -> str:
    normalized = "\n".join(line.rstrip() for line in lines).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_judgments(text: str, path: str) -> tuple:
    """Return (judgments, problems). Problems are strings; parsing never raises."""
    judgments, problems = [], []
    lines = text.splitlines()
    in_fence = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if FENCE.match(line):
            in_fence = not in_fence
            index += 1
            continue
        start = None if in_fence else START.match(line)
        if not start:
            index += 1
            continue
        block = [line]
        cursor = index + 1
        while cursor < len(lines) and lines[cursor].lstrip().startswith(">"):
            block.append(lines[cursor])
            cursor += 1
        fields = {}
        for body in block[1:]:
            match = KEY_LINE.match(body.strip())
            if not match:
                continue
            key = KEYS.get(match.group(1).strip().lower()) or KEYS.get(match.group(1).strip())
            if key:
                fields[key] = match.group(2).strip()
        judgment_id = start.group(1)
        if not fields.get("conclusion"):
            problems.append(f"{path}:{index + 1}: judgment {judgment_id} has no conclusion")
        judgments.append(Judgment(
            id=judgment_id, path=path, line=index + 1, fields=fields,
            basis=parse_basis(fields.get("basis", "")), block_hash=block_hash(block), raw="\n".join(block),
        ))
        index = cursor
    return tuple(judgments), tuple(problems)


def strip_judgments(text: str) -> str:
    """Text with judgment blocks removed; used for node versions so admitting a
    judgment into a card does not change the version other judgments depend on."""
    out, lines, in_fence, index = [], text.splitlines(), False, 0
    while index < len(lines):
        line = lines[index]
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and START.match(line):
            index += 1
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                index += 1
            continue
        out.append(line)
        index += 1
    return "\n".join(out)


def render_judgment(judgment_id: str, fields: dict, basis: tuple, lang: str = "zh-CN") -> str:
    rows = [f"> [!judgment] {judgment_id}"]
    separator = ": " if str(lang).lower().startswith("en") else "："
    for key, label in (LABELS_EN if str(lang).lower().startswith("en") else LABELS_ZH):
        if key == "basis":
            if basis:
                rows.append(f"> {label}{separator}" + " · ".join(b.text() for b in basis))
            continue
        value = str(fields.get(key, "")).strip()
        if value:
            rows.append(f"> {label}{separator}{value}")
    return "\n".join(rows)
