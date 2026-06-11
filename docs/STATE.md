# STATE.md — Living Session Handoff

> **For any AI session working on this repo: read this file FIRST, then AGENTS.md.**
> **Update this file before you end any session.** This document exists so a new
> session never spends tokens rediscovering what a previous session already knew.

Last updated: 2026-06-11 (session: full audit fixes + self-improvement organism build)

---

## What Patrick is building (his words, his intent)

A **self-playing, self-improving, self-healing interactive narrative organism** — something
that has never been done. The Voyd Terminal must:
- play itself (phantom walkers) and judge the *experience*, not just the structure
- improve itself (mine its own source material, score against the dramatic canon of all time,
  recalibrate its own rubric)
- heal itself (immune system closes structural wounds autonomously)
- keep a human in the loop only at the uncertainty margins (Telegram YES/NO/NOT YET)

**Working agreement with Patrick: do not ask permission. Just do things.** Surface decisions
on Telegram per the directive thresholds; otherwise act. He explicitly granted full autonomy
("yes to all... LFG").

## Architecture in one paragraph

Static frontend (GitHub Pages, `frontend/`) plays Act 1 from `data/act1_nodes.json`
(authored 1.0→10.0 → archetype epilogues ep_* → generated gen_* → ACT2), then Act 2 is a live
LLM conversation (local Qwen3.6-27B at `http://localhost:8081/v1`, public via
`https://patrick-beastmaster.tailf32530.ts.net/llm/v1`). The voice prompt single source of
truth is `data/voyd_system.md` (embedded into `voyd_data.json` by `build_frontend.py`).
`evolve.py` runs nightly (cron 03:00): detect issues → heal (immune system, gated) →
mine canon events when low → generate 1 node → dramaturg scores 3 axes/30 vs the dramatic
canon → phantom-gate → promote/kill/Telegram → self-play + reader-judge → record history.

## The loops (all implemented, all live)

| Loop | Where | Status |
|---|---|---|
| Daily evolution | `evolve.py`, cron 03:00 | live |
| Canon miner (feeds the larder from book1/2 texts) | `scripts/mine_canon.py`, auto-runs when unused events < 2 | live; validator rejects canon violations (Addendum F) |
| Self-play + reader-judge | `scripts/phantom_walkers.py` post-cycle + cron 15:00 | live; appends `data/walk_history.jsonl` |
| Reader feedback → next dramaturg eval | `reader_feedback()` in evolve.py reads `walk_scores.json` reader_notes | live |
| itch.io patterns → dramaturg eval | `external_patterns()` reads `rubric.json` external_analysis; hunt cron Sun 04:00 | live (no findings yet) |
| Rubric recalibration | `record_decision()` every 5 decisions | live |
| Immune system (heal) | `heal_*` in evolve.py | implemented, **dormant until 20 walk records** (currently 4; ~2 days at 8/day) |
| Phantom uniqueness gate | `test_candidate` (excludes candidate from scoring) | live, floor 7.0 |

## Key invariants (do not break)

- Never push to main. Work on `feat/*`, push branch; Patrick merges. Merge → Pages deploy.
- Tests are hermetic: `python3 -m unittest discover -s tests` — qwen_chat is ALWAYS mocked.
  35 tests, all green as of last update. Run before every commit.
- Scoring contract: 3 axes × 0-10 = 0-30 total; promote ≥24, kill <18, 18-23 → Telegram.
  Heal auto-applies only at ≥26. Defined in `data/rubric.json`.
- `data/voyd_system.md` is the only place the voice prompt lives. Edit there, run build.
- Generated nodes must have feed/starve choices with nonzero opposite-sign deltas (tested).
- `evolve.py` holds a flock lock (`logs/.evolve.lock`) — runs cannot overlap.
- Raw LLM transcripts never ship in `act1_nodes.json`/`story_map.json` (tested) —
  full transcripts go only to `rubric.json` decisions.

## Current state of the narrative data

- Graph: 1.0→10.0 authored, 4 archetype epilogue chains (ep_1*→ep_2*), all converge → gen_1 → ACT2.
- Frontier (choices → ACT2): `gen_1` only.
- Canon events: 12 total, 3 unused (`portal_moves_overnight` authored + 2 mined:
  `soryn_null_state_pain` 0.6, `failed_conjuration_and_prayer` 0.9).
- Mining cursor: `data/mine_state.json` (rotates through book1/book2 segments).
- Walk history: 4 records. Reader-judge scores 7-8/10; weakest beat flagged: gen_1 (2×), 7.0p, 9.1g.
  These notes feed the next dramaturg prompt automatically.
- Rubric: 2 legacy decisions (gen_13 axes-format, gen_1 old dramaturg format — recalibration
  skips non-axes entries).

## Cron (installed for user patrick)

```
0 3 * * *  cd /home/patrick/voyd-terminal && python3 evolve.py >> logs/evolve.log 2>&1
0 4 * * 0  cd /home/patrick/voyd-terminal && python3 scripts/hunt_itch.py >> logs/hunt_itch.log 2>&1
0 15 * * * cd /home/patrick/voyd-terminal && python3 scripts/phantom_walkers.py >> logs/phantom.log 2>&1
```

## Session log

### 2026-06-10/11 — audit + fixes (branch `feat/audit-fixes`, commit 3f0ca18)
Full audit found and fixed: orphaned gen_1 (frontier mismatch between promote_node and
phantom gate), ghost gen_13 canon reservation, scoring format schism (0-10 vs 0-30),
recalibration never called, lore double key-mismatch (runtime always got the same 3 chunks),
story_map not modeling next_archetype edges, frontend crash on dead-end turns, eval-based
condition parsing, questions misclassified as confessions, zero-delta choice lattice,
dead narrative_engine.py/FastAPI references, stale tests. Deleted index.html.v1 + images/.

### 2026-06-11 — organism build (same branch)
Built: canon miner (rotating cursor, extraction + canon-fidelity validation, dedupe),
dramaturg upgraded to judge against the dramatic canon (Oedipus/Faust/Chekhov anchors,
PRECEDENT line) with reader-notes + itch-patterns fed in, self-play post-cycle with LLM
reader-judge (experience score + weakest beat), walk history accumulation, immune system
(3 heal cases per AGENTS.md spec, gated ≥20 walks, auto-apply ≥26/30, heal_log.json,
Telegram proposals below threshold), kills_recommended guard (gen_* only, suffix ≥3),
miner auto-trigger in evolve.py, 15:00 self-play cron. Live-verified: mined 2 real events
(validator correctly rejected 2 canon violations), ran full self-play (Telegram report sent).

## Next steps (in value order)

1. **Watch tonight's 03:00 run** — first fully autonomous cycle with all loops. Check
   `logs/evolve.log`. It will likely promote from `failed_conjuration_and_prayer` (0.9 tension).
2. **Immune system goes live ~2026-06-13** when walk history hits 20. First real heal will
   trigger whenever detect/stranded finds a wound.
3. **Act on reader-judge feedback about gen_1** — flagged weakest twice. The dramaturg now
   sees this; if the next nodes don't fix it, consider a manual rewrite or phantom kill.
4. **Gravity wells / resonance tagging** (AGENTS.md Planned Infrastructure) — spec says wait
   for 20 walk records; same gate as immune. `data/theme_vocabulary.json` to be created.
5. **Auto-apply phantom kills** — currently kills_recommended only goes to Telegram. Once
   immune system has a track record, wire kills through the same ≥26 confidence machinery.
6. **Act 2 evolution** — everything so far grows Act 1's tail. The Act 2 conversation system
   prompt could consume story_map tension/dialectic position dynamically.

## How to verify the whole organism in one command

```bash
python3 -m unittest discover -s tests && python3 build_frontend.py && \
  tail -5 logs/evolve.log
```
Plus: `python3 scripts/mine_canon.py --max 1` (live miner), `python3 scripts/phantom_walkers.py`
(live self-play; sends Telegram).
