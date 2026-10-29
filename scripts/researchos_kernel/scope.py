"""Containment (归属), episode state and the frozen scope of one bounded goal.

Canon: Primitive Rule Model 《图的三个轴》. Three facts this module owns, and nothing else:

* **Containment is derived.** A record's scope node comes from its location in the
  repository; the record may override it in its own frontmatter. Nothing here stores a
  registry, and the domain is the whole repository — the scan configuration only decides
  which records are *evaluated*, never which scope a record belongs to.
* **The scope of a bounded goal is frozen extensionally at its start.** `freeze()` evaluates
  the closure once and records its members plus a digest. Afterwards containment changes and
  episode closures do not move this scope; they are attributed to the next episode. Without
  this, a directory move would drop records out of a running goal, closing a sub-episode
  would shrink the scope into "complete", and replay could never recompute the same set.
* **Coverage unknown is counted in two kinds that never absorb each other**: in-scope inputs
  that were not evaluated, and records whose containment is undefined.
* **The source establishes a closure; the ledger can refute it but never establish it.** The
  source says ``episode_state: closed`` and names ``episode_closure_receipt``. The runtime
  ledger is git-ignored, so it may not decide long-term state (Kernel §2 source authority):
  a receipt it does not know is reported as unverifiable here, not treated as absent. It
  refutes a receipt that was rolled back or issued to another episode identity; sources
  refute one that two records claim. A ``closed`` without a receipt is open and reported.
  Identity is the frontmatter ``id`` or the file stem, never the directory, so moving a
  closed episode keeps it closed (report D0).

Interface nodes are declared by the record itself (`interface: true`), so a scope's interface
set is derived too. Cross-scope references to non-interface records are reported, not refused:
most scopes have no interface node yet, and refusing first would fail ordinary work.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .ledger import digest

ROOT_SCOPE = "/"
OPEN, CLOSED = "open", "closed"
DERIVED, DECLARED = "derived", "declared"


def derive(relative: str, declared: str = "") -> tuple:
    """Return (scope_node, source). A record declares its own scope or inherits its folder.

    The scope node of ``01_knowledge/projects/<family>/<card>.md`` is its directory,
    ``01_knowledge/projects/<family>``; a declared value wins and is recorded as such."""
    declared = (declared or "").strip().strip("/")
    if declared:
        return declared, DECLARED
    parent = PurePosixPath(relative).parent.as_posix()
    return (ROOT_SCOPE if parent in {".", ""} else parent), DERIVED


def ancestors(node: str) -> list:
    """The scope node and all of its ancestors, nearest first. The scope graph is a tree."""
    if node in {"", ROOT_SCOPE}:
        return [ROOT_SCOPE]
    parts = PurePosixPath(node).parts
    return [PurePosixPath(*parts[:index]).as_posix() for index in range(len(parts), 0, -1)] + [ROOT_SCOPE]


def contains(node: str, scope_of_key: str) -> bool:
    return node in ancestors(scope_of_key)


@dataclass
class Placement:
    """Where one key sits on the containment and episode axes."""
    key: str
    scope: str = ""
    source: str = DERIVED
    episode_state: str = ""   # "" = not an episode; a non-episode is never closed
    interface: bool = False
    closure_receipt: str = ""  # frontmatter `episode_closure_receipt`
    identity: str = ""         # frontmatter `id` or the file stem: what a receipt is issued to
    refuted: str = ""          # why the receipt does not hold; "" = not refuted
    verified: bool = False     # the local ledger holds the receipt for this identity

    @property
    def closed(self) -> bool:
        return self.episode_state == CLOSED and bool(self.closure_receipt) and not self.refuted


def closure(placements: dict, node: str) -> set:
    """cl(n): keys whose containment is n or below it, excluding closed episodes."""
    return {key for key, place in placements.items()
            if place.scope and not place.closed and contains(node, place.scope)}


def unowned(placements: dict) -> set:
    """Records whose containment could not be determined: coverage unknown, second kind."""
    return {key for key, place in placements.items() if not place.scope}


@dataclass(frozen=True)
class FrozenScope:
    """Sc_ε evaluated once, at the start. Members are the extension; the digest pins it."""
    node: str
    members: frozenset
    cross: tuple = ()
    frozen_at: str = ""
    unowned_count: int = 0
    narrowed_by: str = ""  # an intent that narrowed the extension (e.g. commitment:<id>); "" = the node's closure

    def __contains__(self, key: str) -> bool:
        return key in self.members

    @property
    def member_digest(self) -> str:
        return digest(sorted(self.members))

    def to_dict(self) -> dict:
        return {"scope_node": self.node, "scope_member_digest": self.member_digest,
                "scope_member_count": len(self.members), "scope_frozen_at": self.frozen_at,
                "cross_scope_keys": [dict(row) for row in self.cross],
                "coverage_unknown_unowned": self.unowned_count, "narrowed_by": self.narrowed_by}


def narrow_to_commitment(frozen: FrozenScope, snapshot, commitment_id: str) -> FrozenScope:
    """Sc_ε for a session whose intent is one commitment: that commitment, its judgments, its source
    card and their basis cards, all within the frozen extension (keys outside it stay outside)."""
    commitment = snapshot.commitments.get(commitment_id)
    keys = {f"commitment:{commitment_id}"}
    judgments = [j for j in snapshot.judgments.values() if snapshot.commitment_for_judgment(j) == commitment_id]
    keys |= {f"judgment:{j.id}" for j in judgments}
    refs = [commitment.get("source_path")] if commitment else []
    # A judgment's host card is in scope, but not the portfolio: it hosts every commitment.
    refs += [basis.ref for j in judgments for basis in j.basis] + [j.path for j in judgments
                                                                    if j.path != snapshot.portfolio_path]
    for ref in refs:
        resolved, _ = snapshot.resolve(ref) if ref else ("", "")
        if resolved:
            keys.add(resolved)
    return FrozenScope(node=frozen.node, members=frozenset(keys & set(frozen.members)), cross=frozen.cross,
                       frozen_at=frozen.frozen_at, unowned_count=frozen.unowned_count,
                       narrowed_by=f"commitment:{commitment_id}")


def freeze(placements: dict, node: str, *, frozen_at: str, cross: list | None = None) -> tuple:
    """Return (FrozenScope, problems). Cross-scope keys must name an interface node of another
    scope; one that names an inner record is reported, never silently accepted or dropped."""
    problems, declared = [], []
    members = closure(placements, node)
    for entry in cross or []:
        key = str(entry.get("key", "")).strip()
        place = placements.get(key)
        if place is None or not place.scope:
            problems.append(f"cross-scope key {key or '(empty)'} is not a known record")
            continue
        if contains(node, place.scope):
            problems.append(f"cross-scope key {key} already belongs to {node}")
            continue
        row = {"key": key, "scope": place.scope, "version": str(entry.get("version", "")),
               "interface": place.interface}
        declared.append(row)
        members.add(key)
        if not place.interface:
            problems.append(f"cross-scope key {key} is not an interface node of {place.scope} "
                            f"(reported, not refused: that scope has no interface node yet)")
    rows = tuple(tuple(sorted(row.items())) for row in declared)
    return FrozenScope(node=node, members=frozenset(members), cross=rows, frozen_at=frozen_at,
                       unowned_count=len(unowned(placements))), problems


def restore(payload: dict, members) -> FrozenScope:
    """Rebuild a frozen scope from its serialized form plus the recorded members."""
    frozen = FrozenScope(node=str(payload.get("scope_node", "")), members=frozenset(members),
                         cross=tuple(tuple(sorted(row.items())) for row in payload.get("cross_scope_keys", [])),
                         frozen_at=str(payload.get("scope_frozen_at", "")),
                         unowned_count=int(payload.get("coverage_unknown_unowned", 0) or 0),
                         narrowed_by=str(payload.get("narrowed_by", "") or ""))
    return frozen


def coverage(frozen: FrozenScope, evaluated: set) -> dict:
    """The two counts and their denominator. The kinds never absorb each other: an in-scope
    key that was not evaluated is registered as a requirement; an unowned record is only
    counted here; an out-of-scope key is neither."""
    missing = sorted(frozen.members - set(evaluated))
    return {"in_scope_match_count": len(frozen.members),
            "evaluated_match_count": len(set(evaluated) & frozen.members),
            "coverage_unknown_in_scope": len(missing),
            "coverage_unknown_unowned": frozen.unowned_count,
            "uncovered_keys": missing}


def closure_problems(placements: dict) -> list:
    """Every closure that does not hold, and every one this machine cannot verify."""
    problems = []
    for key, place in sorted(placements.items()):
        if place.episode_state != CLOSED or key.startswith("judgment:"):
            continue
        if not place.closure_receipt:
            problems.append(f"{key}: episode_state closed without episode_closure_receipt; treated as open "
                            f"(close it with ros propose episode-close + ros admit)")
        elif place.refuted:
            problems.append(f"{key}: closure receipt {place.closure_receipt} {place.refuted}; treated as open")
        elif not place.verified:
            problems.append(f"{key}: closure receipt {place.closure_receipt} cannot be verified on this machine "
                            f"(not in the local ledger); the source keeps it closed")
    return problems


def _refutation(receipt: str, identity: str, claims: int, receipts: dict) -> str:
    if claims > 1:
        return f"is claimed by {claims} records"
    known = receipts.get(receipt)
    if known is None:
        return ""
    if known.get("revoked"):
        return "was revoked by a rollback"
    if known.get("identity") != identity:
        return f"was issued to episode {known.get('identity') or '(unknown)'}, not {identity}"
    return ""


def placements_from_snapshot(snapshot, closure_receipts: dict | None = None) -> dict:
    """Read the three axes off the snapshot. Commitments inherit the placement of their source.

    ``closure_receipts`` maps receipt id -> {"identity", "revoked"} from the local ledger. It can
    only refute a closure the source records; an empty map verifies nothing and refutes nothing."""
    receipts = closure_receipts or {}
    claims = {}
    for node in snapshot.nodes.values():
        receipt = getattr(node, "closure_receipt", "")
        if receipt and getattr(node, "episode_state", "") == CLOSED:
            claims[receipt] = claims.get(receipt, 0) + 1
    found = {}
    for ref, node in snapshot.nodes.items():
        scope, source = derive(node.path, getattr(node, "declared_scope", ""))
        receipt, identity = getattr(node, "closure_receipt", ""), str(getattr(node, "id", "") or "")
        refuted = _refutation(receipt, identity, claims.get(receipt, 0), receipts) if receipt else ""
        found[ref] = Placement(key=ref, scope=scope, source=source,
                               episode_state=getattr(node, "episode_state", ""),
                               interface=bool(getattr(node, "interface", False)),
                               closure_receipt=receipt, identity=identity, refuted=refuted,
                               verified=bool(receipt) and not refuted and receipt in receipts)
    for jid, judgment in getattr(snapshot, "judgments", {}).items():
        # A judgment inherits the placement of the file that carries it: it has no location
        # of its own, and leaving it unplaced would drop it out of every scope unnoticed.
        host = found.get(judgment.path)
        found[f"judgment:{jid}"] = Placement(
            key=f"judgment:{jid}", scope=host.scope if host else derive(judgment.path, "")[0],
            source=host.source if host else DERIVED,
            episode_state=host.episode_state if host else "",
            closure_receipt=host.closure_receipt if host else "", identity=host.identity if host else "",
            refuted=host.refuted if host else "", verified=host.verified if host else False)
    for cid, commitment in snapshot.commitments.items():
        source_path = commitment.get("source_path")
        scope, source = derive(source_path, "") if source_path else ("", DERIVED)
        found[f"commitment:{cid}"] = Placement(key=f"commitment:{cid}", scope=scope, source=source)
    return found
