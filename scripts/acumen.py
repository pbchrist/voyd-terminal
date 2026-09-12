#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from story_room.genome import GenomeStore
from story_room.speciation import decide_speciation

GENOME = ROOT / "story_room" / "genome.json"


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_show(_: argparse.Namespace) -> int:
    data = GenomeStore(GENOME).load()
    print(json.dumps(data, indent=2))
    return 0


def cmd_speciate(args: argparse.Namespace) -> int:
    payload = read_json(args.file)
    candidates = payload.get("candidates", payload if isinstance(payload, list) else [])
    laws = GenomeStore(GENOME).active_laws()
    print(json.dumps(decide_speciation(candidates, laws), indent=2))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    payload = read_json(args.file)
    store = GenomeStore(GENOME)
    decision = payload["decision"]
    recorded = store.record_decision(decision)
    law_ids = []
    for proposal in payload.get("laws", []):
        law = store.observe_law(
            statement=proposal["statement"],
            kind=proposal["kind"],
            scopes=proposal["scopes"],
            decision_id=decision["id"],
            rationale=proposal.get("rationale", decision.get("rationale", "")),
            explicit=bool(proposal.get("explicit", False)),
        )
        law_ids.append(law["id"])

    # Backfill the law ids onto the just-recorded decision so the audit trail
    # points both directions.
    data = store.load()
    for entry in data["decisions"]:
        if entry["id"] == recorded["id"]:
            entry["law_ids"] = law_ids
            break
    store.save(data)
    print(json.dumps({"decision": recorded["id"], "law_ids": law_ids}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Voyd Story Genome / Acumen tools")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="print the current Story Genome")
    show.set_defaults(func=cmd_show)

    speciate = sub.add_parser("speciate", help="decide whether a mutation fork needs Patrick")
    speciate.add_argument("file", help="JSON containing candidates")
    speciate.set_defaults(func=cmd_speciate)

    record = sub.add_parser("record", help="record Patrick's fork decision and law proposals")
    record.add_argument("file", help="JSON containing decision + optional laws")
    record.set_defaults(func=cmd_record)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
