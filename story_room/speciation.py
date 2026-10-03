from __future__ import annotations

from typing import Any


def _viable(candidate: dict[str, Any]) -> bool:
    if candidate.get("steward_verdict") == "BLOCK":
        return False
    if candidate.get("structural_verdict") in {"REBUILD", "FAIL"}:
        return False
    return bool(candidate.get("structurally_viable", True))


def decide_speciation(candidates: list[dict[str, Any]], active_laws: list[dict[str, Any]]) -> dict[str, Any]:
    """Decide whether the system already knows enough to choose without Patrick.

    This never numerically ranks story quality. It can auto-select only when a
    surviving candidate is uniquely compelled by already-active hard laws. If
    two structurally viable candidates imply different stories and neither is
    ruled out by inherited law, the fork belongs to Patrick.
    """
    viable = [c for c in candidates if _viable(c)]
    if not viable:
        return {"mode": "rebuild", "reason": "no structurally viable mutation survived", "candidates": []}
    if len(viable) == 1:
        return {"mode": "auto", "selected": viable[0]["id"], "reason": "only one mutation survived structural prosecution"}

    hard_ids = {law["id"] for law in active_laws if law.get("kind") in {"require", "avoid"}}
    compliant = []
    for candidate in viable:
        violations = set(candidate.get("violates_law_ids", [])) & hard_ids
        if not violations:
            compliant.append(candidate)

    if len(compliant) == 1:
        return {
            "mode": "auto",
            "selected": compliant[0]["id"],
            "reason": "active Story Genome law eliminates every other viable mutation",
        }

    pool = compliant if compliant else viable
    return {
        "mode": "human",
        "reason": "multiple structurally viable futures remain and inherited acumen does not decide between them",
        "fork": [
            {
                "id": c["id"],
                "title": c.get("title", c["id"]),
                "structural_change": c.get("structural_change", ""),
                "story_consequence": c.get("story_consequence", ""),
                "cost": c.get("cost", ""),
                "inherits": c.get("inherits", []),
            }
            for c in pool
        ],
    }
