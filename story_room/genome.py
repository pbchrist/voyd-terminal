from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
VALID_KINDS = {"require", "prefer", "avoid"}
VALID_STATUSES = {"candidate", "active", "retired"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def law_id(statement: str, kind: str, scopes: list[str]) -> str:
    raw = "|".join([kind, statement.strip().lower(), *sorted(scopes)])
    return "law_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def empty_genome() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "laws": [],
        "decisions": [],
    }


class GenomeStore:
    """Persistent, auditable memory of Patrick-derived storytelling judgment.

    Explicit laws become active immediately. Inferred laws must be observed in
    at least two separate human decisions before they become active. This keeps
    one ambiguous choice from silently hardening into doctrine.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return empty_genome()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported genome schema: {data.get(schema_version)}")
        data.setdefault("laws", [])
        data.setdefault("decisions", [])
        return data

    def save(self, data: dict[str, Any]) -> None:
        data = deepcopy(data)
        data["schema_version"] = SCHEMA_VERSION
        data["updated_at"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def active_laws(self, scopes: list[str] | None = None) -> list[dict[str, Any]]:
        data = self.load()
        laws = [law for law in data["laws"] if law.get("status") == "active"]
        if not scopes:
            return laws
        wanted = set(scopes)
        return [law for law in laws if wanted.intersection(law.get("scopes", []))]

    def observe_law(
        self,
        *,
        statement: str,
        kind: str,
        scopes: list[str],
        decision_id: str,
        rationale: str = "",
        explicit: bool = False,
    ) -> dict[str, Any]:
        if kind not in VALID_KINDS:
            raise ValueError(f"invalid law kind: {kind}")
        scopes = sorted({s.strip() for s in scopes if s.strip()})
        if not statement.strip() or not scopes:
            raise ValueError("law requires statement and at least one scope")

        data = self.load()
        lid = law_id(statement, kind, scopes)
        existing = next((x for x in data["laws"] if x.get("id") == lid), None)
        timestamp = now_iso()

        if existing is None:
            existing = {
                "id": lid,
                "statement": statement.strip(),
                "kind": kind,
                "scopes": scopes,
                "status": "active" if explicit else "candidate",
                "origin": "explicit" if explicit else "inferred",
                "confirmations": 1,
                "contradictions": 0,
                "decision_ids": [decision_id],
                "rationales": [rationale] if rationale else [],
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            data["laws"].append(existing)
        else:
            if decision_id not in existing.setdefault("decision_ids", []):
                existing["decision_ids"].append(decision_id)
                existing["confirmations"] = int(existing.get("confirmations", 0)) + 1
            if rationale and rationale not in existing.setdefault("rationales", []):
                existing["rationales"].append(rationale)
            if explicit:
                existing["origin"] = "explicit"
                existing["status"] = "active"
            elif existing.get("status") != "retired" and existing.get("confirmations", 0) >= 2:
                existing["status"] = "active"
            existing["updated_at"] = timestamp

        self.save(data)
        return deepcopy(existing)

    def contradict_law(self, law_id_value: str, decision_id: str, rationale: str = "") -> dict[str, Any]:
        data = self.load()
        law = next((x for x in data["laws"] if x.get("id") == law_id_value), None)
        if law is None:
            raise KeyError(law_id_value)
        law["contradictions"] = int(law.get("contradictions", 0)) + 1
        law.setdefault("contradiction_decision_ids", []).append(decision_id)
        if rationale:
            law.setdefault("contradiction_rationales", []).append(rationale)
        if law.get("origin") != "explicit" and law["contradictions"] >= law.get("confirmations", 0):
            law["status"] = "candidate"
        law["updated_at"] = now_iso()
        self.save(data)
        return deepcopy(law)

    def record_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        required = {"id", "fork_id", "selected", "rationale"}
        missing = required.difference(decision)
        if missing:
            raise ValueError(f"decision missing: {sorted(missing)}")
        data = self.load()
        if any(d.get("id") == decision["id"] for d in data["decisions"]):
            raise ValueError(f"duplicate decision id: {decision[id]}")
        entry = deepcopy(decision)
        entry.setdefault("recorded_at", now_iso())
        entry.setdefault("candidates", [])
        entry.setdefault("law_ids", [])
        data["decisions"].append(entry)
        self.save(data)
        return entry
