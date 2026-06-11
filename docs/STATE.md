# STATE.md — Living Session Handoff

> **For any AI session working on this repo: read this file FIRST, then AGENTS.md.**
> **Update this file before you end any session.** This document exists so a new
> session never spends tokens rediscovering what a previous session already knew.

Last updated: 2026-06-11 afternoon (session: organism auto-commits its data; LIVE ACT 2 IS DOWN — funnel /llm mount lost, fix needs Patrick)

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

- Graph: 1.0→10.0 authored, 4 archetype epilogue chains (ep_1*→ep_2*), all converge →
  gen_1 → gen_2 → ACT2.
- Frontier (choices → ACT2): `gen_2` only.
- Canon events: 12 total, 2 unused (`portal_moves_overnight`, `failed_conjuration_and_prayer`
  0.9). Tonight's cycle will drop unused to 1 → miner auto-triggers the night after.
- Mining cursor: `data/mine_state.json` (rotates through book1/book2 segments).
- Walk history: 12 records (immune gate at 20 → expected to go live ~2026-06-12).
  Reader-judge scores 7-8/10.
- Rubric: 5 decisions; recalibration fires at every 5th, so it ran on the gen_1 rewrite.
- **First autonomous 03:00 cron cycle ran 2026-06-11**: re-selected `soryn_null_state_pain`
  (killed at 13/30 the night before), generated fresh text, dramaturg promoted **gen_2 at
  24/30** with an Oedipus precedent line. Kill→retry→promote works end to end.
- **gen_1 rewritten in place 2026-06-11 morning** (dramaturg 24/30, was the consensus
  weakest beat 4 walks running). New text keeps the four-lights seed, drops the abstract
  color catalog. Today's 15:00 self-play is the first test of whether the flag clears.

## Cron (installed for user patrick)

```
0 3 * * *  cd /home/patrick/voyd-terminal && python3 evolve.py >> logs/evolve.log 2>&1
0 4 * * 0  cd /home/patrick/voyd-terminal && python3 scripts/hunt_itch.py >> logs/hunt_itch.log 2>&1
0 15 * * * cd /home/patrick/voyd-terminal && python3 scripts/phantom_walkers.py >> logs/phantom.log 2>&1
```

## Enforcement

A **Stop hook** (`.claude/settings.json` → `.claude/hooks/check_state_md.sh`) blocks any
Claude session from finishing a turn while the repo has changed >20 min more recently than
this file. If you're reading this because the hook redirected you: add a session-log entry,
refresh "Current state" and "Next steps", then stop. The 20-minute grace means rapid
iteration won't nag every turn.

## Session log

### 2026-06-11 afternoon — organism self-commits + funnel outage found (same branch)
Implemented next-step 0 option (a): `commit_data_changes()` in evolve.py — at the end of
every cycle (try/finally in main) it commits changes under `data/` + `frontend/voyd_data.json`
on the checked-out branch and pushes it; refuses to touch main or a detached HEAD; push
failure keeps the commit local. Also sweeps up the 15:00 phantom run's data, since it
commits whatever is dirty. Option (b) (auto-merge to main, unsupervised publishing) still
open. Tests now 42, green. Verified live site = local byte-for-byte (37 nodes, rewritten
gen_1 + gen_2 live). Solved yesterday's mystery: the 09:13–09:16 evolve.log timeouts were
the morning gen_1-rewrite session's retries (rewrite_node loads evolve, shares its log).
**Found: live Act 2 is DOWN.** The frontend calls
`https://patrick-beastmaster.tailf32530.ts.net/llm/v1/chat/completions` → 404. The tailscale
funnel now routes `/` → 127.0.0.1:8767 (mythomancer, hermes-instance2) and the `/llm` mount
to the llama-server on 8081 is gone — presumably wiped when that other instance reconfigured
the funnel. Claude is permission-blocked from re-exposing it; Patrick must run:
`tailscale funnel --bg --set-path=/llm http://127.0.0.1:8081`

### 2026-06-10/11 — audit + fixes (branch `feat/audit-fixes`, commit 3f0ca18)
Full audit found and fixed: orphaned gen_1 (frontier mismatch between promote_node and
phantom gate), ghost gen_13 canon reservation, scoring format schism (0-10 vs 0-30),
recalibration never called, lore double key-mismatch (runtime always got the same 3 chunks),
story_map not modeling next_archetype edges, frontend crash on dead-end turns, eval-based
condition parsing, questions misclassified as confessions, zero-delta choice lattice,
dead narrative_engine.py/FastAPI references, stale tests. Deleted index.html.v1 + images/.

### 2026-06-11 midday — live site deployed and verified (merge to main)
Patrick said "fix the front end." Diagnosis: the local frontend was fine (verified by
headless Chrome playthroughs, both archetype branches, Act 1 → gen_2 → Act 2, zero JS
errors) — but GitHub Pages was serving pre-audit main: old crashy engine, old gen_1,
no gen_2. Patrick fast-forwarded main to b3f2d40 himself (the permission system blocks
Claude from pushing main); Pages redeployed in ~15s and the live site was re-verified
headlessly end to end. Favicon 404 silenced with an inline SVG glyph (on branch, ships
with next merge). **New structural fact: the public site only updates on push to main,
but the organism evolves data/act1_nodes.json nightly on this machine — the live story
will drift behind the organism until merges happen (see next steps).**

### 2026-06-11 morning — human-readable reports + gen_1 rewrite (same branch)
Patrick's feedback: the Telegram walker report "doesn't mean anything to me, a human."
Root causes found and fixed: (1) the 03:00 post_cycle never sent a report at all (only
kill recommendations); (2) the report showed bare node ids and truncated jargon. Now
`build_report_message()` quotes the actual beat text, groups weakest-beat complaints by
beat across readers, shows full judge reasoning, and leads with the night's cycle outcome
(grew/killed, with text). post_cycle sends it every night. Also: reader complaints now
feed the *generator* prompt (not just the dramaturg) so a flagged mistake isn't repeated
and killed the same night; `log()` no longer duplicates every line under cron;
`scripts/rewrite_node.py` rewrites a flagged beat's prose in place, dramaturg-gated,
scored against its real graph predecessors (first version scored against the frontier —
the dramaturg punished the candidate for "repeating" the very scene it replaced).
Used it live: gen_1 rewritten at 24/30. Tests: 39 green (frontier tests made structural).
Unexplained: a second evolve.py tried to start at 03:00:38 and was correctly rejected by
the lock; cron fired only once per journalctl. Watch whether it recurs tonight.

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

-1. **RESTORE LIVE ACT 2 (Patrick, one command):**
   `tailscale funnel --bg --set-path=/llm http://127.0.0.1:8081`
   The funnel /llm mount vanished (mythomancer instance owns funnel / now); the frontend's
   hardcoded LLM URL 404s, so Act 2 is dead on the live site AND in local play. Claude is
   permission-blocked from running funnel commands. After running it, verify:
   `curl https://patrick-beastmaster.tailf32530.ts.net/llm/v1/models` → 200.
   Consider: longer-term, stop the two hermes instances from clobbering each other's mounts.
0. ~~Decide how the live site tracks the organism~~ — option (a) DONE this session:
   evolve.py now commits+pushes its data to the working branch every cycle; Patrick merges
   when he likes. Open question remains whether to go to (b): auto-merge data-only changes
   to main nightly, i.e. generated prose ships to the public site with no human gate.
1. **Check today's 15:00 self-play** (`logs/phantom.log`, Telegram) — first verdict on the
   rewritten gen_1. If readers still flag it, try `python3 scripts/rewrite_node.py gen_1`
   again or consider killing the beat. Also the first standalone run with the new
   human-readable report format.
2. **Watch tonight's 03:00 run** — it will likely promote from `failed_conjuration_and_prayer`
   (0.9 tension) and now sends the readable nightly report. Also watch whether the mystery
   second evolve.py instance (rejected by the lock at 03:00:38 last night) recurs.
3. **Immune system goes live ~2026-06-12** when walk history hits 20 (now 12, +8/day).
   First real heal triggers whenever detect/stranded finds a wound.
4. **Other repeatedly-flagged beats are authored, not generated**: 7.0p, 9.1g, ep_1g, 9.2u
   have each been flagged once-twice with the same complaint class (abstract imagery breaks
   intimacy). rewrite_node works on any node with a canon_event; authored nodes lack one, so
   rewriting those needs either a synthetic event or Patrick's hand. Track flag counts first.
5. **Gravity wells / resonance tagging** (AGENTS.md Planned Infrastructure) — wait for
   20 walk records; same gate as immune. `data/theme_vocabulary.json` to be created.
6. **Auto-apply phantom kills** — currently kills_recommended only goes to Telegram. Once
   immune system has a track record, wire kills through the same ≥26 confidence machinery.
7. **Act 2 evolution** — everything so far grows Act 1's tail. The Act 2 conversation system
   prompt could consume story_map tension/dialectic position dynamically.
8. **Watch: repeated kills on the same canon event.** A killed generation doesn't mark the
   event used (correct per directives). soryn_null_state_pain proved kill→retry→promote
   works; if an event gets killed 3+ times, add a per-event attempt counter and demote it.

## How to verify the whole organism in one command

```bash
python3 -m unittest discover -s tests && python3 build_frontend.py && \
  tail -5 logs/evolve.log
```
Plus: `python3 scripts/mine_canon.py --max 1` (live miner), `python3 scripts/phantom_walkers.py`
(live self-play; sends Telegram), `python3 scripts/rewrite_node.py <gen_id>` (in-place
prose rewrite of a flagged beat, dramaturg-gated).
