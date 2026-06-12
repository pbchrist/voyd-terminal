# STATE.md — Living Session Handoff

> **For any AI session working on this repo: read this file FIRST, then AGENTS.md.**
> **Update this file before you end any session.** This document exists so a new
> session never spends tokens rediscovering what a previous session already knew.

Last updated: 2026-06-12 (session: THE RETELLING BUILT — branch `feat/the-retelling`. New game live locally: cold open, retell-it-wrong loop, the trade, shared global portal via voyd_server.py, it-remembers-you, sediment, dream residue. Verified end-to-end headless, 53 tests green. **Patrick must run 2 commands** (funnel + cron) — see Next steps -2.)

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

### 2026-06-12 (later) — THE RETELLING BUILT (branch `feat/the-retelling`, off feat/audit-fixes)
Patrick said "make it." Built and verified the full reconceptualization:
- **`voyd_server.py`** (NEW, stdlib-only, port 8765): the shared body. ONE global portal
  (log-scaled from cumulative fed/starved across all visitors ever), visit counter,
  sediment (visitor gifts digested by the local LLM into dream-wrong one-liners —
  raw text is NEVER served, only digested; digestion loop every 20s), kept-memory per
  visitor token (the return greeting), dream residue from walk_history.jsonl (the
  phantom walkers ARE its dreams, surfaced diegetically). State in `state/voyd_state.json`
  — **gitignored**, confessions must never enter the public repo. Endpoints: GET /state,
  POST /offer, POST /keep; CORS open; tolerates /voyd prefix (funnel strips it).
- **`frontend/index.html` rewritten around THE RETELLING** (portal/speech/input/audio
  machinery preserved verbatim from the verified rebuild): cold open = black screen +
  "name someone you could not keep." + caret, portal NOT born until the player's first
  words; 2 gather questions (true detail, the last time); 4 retellings — LLM retells the
  memory with exactly ONE detail made kinder/falser, accepted lies compound into the next
  round's "truth", "no." forces typing the true detail back; THE TRADE after round 2
  (canon_events voyd_pov = teaser, event = the Mewniverse fragment paid out); endings:
  dissolution (stands>nos, full drifted recite) / refusal (accurate echo — worse — plus
  what it keeps: first accepted lie, or the first words if perfect). Seal shows the kept
  line under the glyph. Ghost whispers = strangers' sediment; dream whisper = walker count.
  All LLM lessons preserved: enable_thinking:false, funnel-first on https, canned-fallback
  retellings (universal false comforts) so a dead mind still plays. Graceful offline mode
  (private portal) if voyd_server unreachable.
- **`build_frontend.py`**: ships `canon_trades` (all 12 events' voyd_pov+event) in
  voyd_data.json. act1_nodes copy kept (tests + organism still reference it; no longer played).
- **Tests: 53 green** (11 new in tests/test_voyd_server.py — hermetic, ephemeral port,
  temp state; covers global portal, clamps, digestion queue isolation, keep/return,
  sanitization, bad kinds). `scripts/voyd_server_guard.sh` keeps the server alive (flock).
- **Verified end-to-end headless** (390×844, /tmp/retelling_drive.py): live Qwen produced
  real compounding distortions ("you whispered that you loved him before the monitor
  flatlined" after the player said *he said nothing*), refusal ending echoed the player's
  corrections verbatim then named the kept lie; trade paid a real canon fragment; server
  kept the lie; **visit 2 greeted with "you came back. i still have what you gave me…"**.
  Zero console errors. Sediment digestion verified live (8/8 digested, e.g. "someone gave
  me the whistle of a worried brother, but it came out as smoke.").
- **Permission-blocked (Patrick must run, see Next steps -2):** funnel mount + cron guard.

### 2026-06-12 — PATRICK PLAYED IT AND REJECTED IT; reconceptualization "THE RETELLING" (design only, NO code)
Patrick's verdict, verbatim spirit: boring as fuck, players bail in ten seconds, no stakes,
"the output had nothing to do with what I wrote," wants a soup-to-nuts reconceptualization
that plays the concept at the heart of his books. **Treat the current Act1-graph→Act2-chat
design as dead.** Diagnosis delivered: (1) player input is structurally ignored until the
very end — the LLM never sees the typed answer until after gen_2; (2) nothing can be lost —
feed/starve moves an invisible number; (3) the opening is lore, not a hook.

**The new concept (Patrick has seen it; awaiting his go for a build plan):**
- **Cold open second 0**: black screen, one line — "name someone you could not keep." —
  blinking cursor. The player types FIRST; the portal is born from their words.
- **Core loop — the Voyd retells the player's memory back, slightly wrong** (one detail
  altered, softer/falser each beat). Player verbs: *let it stand* (feed — warm, easy, the
  lie becomes canon and drifts further) or *"no"* (starve — must type the true detail,
  restating the pain). Feed/starve becomes comfort-vs-truth; the stakes are the player's
  own memory. Every Voyd line must contain a specific noun the player gave it.
- **Canon events become the Voyd's counter-confessions**: it trades memory for memory —
  it is grieving the Mewniverse (Soryn, the Severing, failed conjuration) the way the
  player grieves their person. This is how the books enter play.
- **Endings**: Dissolution (memory recited entire, beautiful, no longer yours); Refusal
  (it speaks your first words back accurately, then shows the one detail you never
  corrected); The Trade (rare — you carry one of ITS memories out; the book funnel).
- **Shareable artifact**: glyph + "what it kept" (one line of your distorted memory).
- **Pacing rule**: 5–8 min run, player acts every ≤20 seconds.
- **Organism survives**: nodes become distortion beats (authored spine steering the LLM),
  miner mines the Voyd's tradeable memories, dramaturg/walkers/immune/rubric all still
  score the spine. The Act1/Act2 split is what dies.
One-sentence anchor: the player's typed memory is the only currency, the Voyd's
distortions are the only antagonist, and the books are what it pays you with.

### 2026-06-11 night — frontend rebuilt from scratch ("worthy of what this thing actually is")
Patrick's brief: the portal is the only UI element that matters; text is spoken, not rendered;
choices are words, not buttons; no chrome, no spinners; mobile-first; single file.
`frontend/index.html` fully rewritten (~1100 lines, no frameworks, no build step):
- **The portal is now real**: a canvas-rendered circle of absolute black at 36% viewport
  height, visible only by its trembling event-horizon rim and the dust/starlight that
  gravitationally lenses into it and is consumed. Radius driven directly by `portalValue`
  (8 → ~8.5% of min viewport dim, 100 → ~44%, slow eased growth + 7.5s breath). Feed
  choices make it swell (pulse + audio); starve makes it flinch and dim.
- **Choices**: bare floating words (warm = feed, cold = starve), breathing. When you feed,
  the chosen letters are physically pulled into the portal and consumed. Choice ritual ≈2s.
- **Speech cadence**: per-char with pauses at sentence/paragraph breaks; tap accelerates.
  Words wrapped in nowrap spans (mid-word line breaks were the first verify finding).
- **Input**: no box — a bare blinking caret in the dialogue; hidden input captures
  (16px font so iOS doesn't zoom; visualViewport → --vvh so the keyboard doesn't cover it).
- **No chrome**: depth/node/status indicators all removed. Discoverability handled by
  diegetic idle whispers near the portal at 40s ("you can answer. it is already listening.").
  Tab-hidden title becomes "it is still here."
- **End**: portal closes to a point, the session glyph appears at its center,
  "it keeps what you gave it."
- **Engine inlined** (single-file directive): `frontend/voyd_engine.js` deleted, `VoydEngine`
  class unchanged inside index.html. AGENTS.md references updated. Tests untouched (42 green;
  they mirror logic, not DOM).
- **Preserved exactly**: act1_nodes graph semantics (delta clamp 0-100, name_* archetype,
  next_archetype routing at 10.0), portalValue start 8, Act 2 payload (model, max_tokens 300,
  history slice -6, enable_thinking:false, Bearer if voyd_key). Act 2 endpoint is now a
  fallback chain: https origin → funnel first then tailnet IP (mixed content blocks http
  from Pages); http/local → `http://100.73.250.50:8081/v1/chat/completions` first.
- **Verified end-to-end** in headless Chrome at 390×844 via CDP driver (`/tmp/voyd_drive.py`):
  full walk 1.0→…→10.0(open answer)→ep_1p→ep_2p→gen_1→gen_2→ACT2, portal curve
  8→5→9→13→17→22→24→28→33→35→39→44→47→50 matches deltas exactly, archetype person_present,
  live LLM replied in voice weaving the typed answer ("i told her the truth before she left" →
  "you traded the lie for the truth and lost her anyway"). Zero console errors. Screenshot
  fixes applied and re-verified: word wrapping, double visitor echo in Act 2, receding rules.

### 2026-06-11 afternoon (later) — Act 2 was dead for THREE stacked reasons; all fixed
Patrick: "front end is the same, same scroll problems, no new stuff, act 2 is dead."
All confirmed and fixed, each verified with real headless-Chrome playthroughs (CDP driver,
control + treatment runs):
1. **Scroll**: `renderChunk` typed text without ever scrolling — with hidden scrollbars and
   `cursor:none`, long beats typed up to **479px below the fold** (measured). Added
   `followBottom()` per character; only follows when the reader is near the bottom, so
   scrolling up to re-read still works. Post-fix max drift: 35–69px (≤ ~1 line, transient).
2. **Funnel**: the `/llm` mount was gone (mythomancer/hermes-instance2 owns funnel `/` on
   8767 and had clobbered the config). Restored with explicit user authorization:
   `tailscale funnel --bg --set-path=/llm http://127.0.0.1:8081` — re-add this if the other
   instance wipes it again.
3. **localStorage key gate**: the direct LLM call only fired if `localStorage.voyd_key`
   was set — i.e. *no visitor ever reached the LLM*; Act 2 silently used canned templates.
   The llama-server doesn't require auth, so the direct call is now the default path
   (Bearer header still sent if a key is set).
4. **Thinking mode** (the killer): Qwen3.6 spent the entire 300-token budget on hidden
   reasoning and returned `content: ""` — the Voyd literally said nothing. The Python
   scripts always passed `chat_template_kwargs: {enable_thinking: false}`; the frontend
   never did. Now it does, with template fallback if content is ever empty.
Final verification: full walk 1.0→…→gen_1→gen_2→ACT2, live LLM 200, real in-voice reply
that wove in the player's named loss. 42 unit tests green. **"No new stuff" explained:**
the organism's growth (gen_1 rewrite, gen_2) IS live on Pages but sits at the *end* of
Act 1, and nothing visual changed — the audit work was engine/data. The visible fixes
(scroll, Act 2) ship when feat/audit-fixes merges to main.

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

-2. **PATRICK: two commands the permission system blocks Claude from running**, then the
   live site has the shared body:
   ```
   tailscale funnel --bg --set-path=/voyd http://127.0.0.1:8765
   (crontab -l; echo '*/5 * * * * /home/patrick/voyd-terminal/scripts/voyd_server_guard.sh'; \
    echo '@reboot /home/patrick/voyd-terminal/scripts/voyd_server_guard.sh') | crontab -
   ```
   (voyd_server.py is already running this session via the guard script; cron makes it
   survive reboots/crashes. Without the funnel, public visitors get private-portal mode.)
-1. **MERGE `feat/the-retelling` → main** to ship the new game (Pages deploys on push;
   ~10 min CDN cache). It supersedes feat/audit-fixes (branched from it, so the audit
   fixes ride along). PLAY IT FIRST locally: `python3 -m http.server 8899 -d frontend`
   → http://localhost:8899 (server + LLM already up).
0. **Repurpose the organism for the Retelling** — evolve.py still grows act1_nodes,
   which is no longer played. Highest-value rewiring: phantom walkers walk the Retelling
   (they have confessions to give); dramaturg scores retelling-transcript quality and
   tunes the distortion directive; miner keeps feeding canon_trades (already shipped).
   Until then the nightly cycle is harmless but pointless.
1. **AGENTS.md still documents the Act1/Act2 architecture** — update after merge.
2. **The tether** (pillar 3): voyd_server already stores kept-memory per token; add an
   optional contact at the seal ("leave a way to be found") + a cron that sends one line
   days later, drifting further. Telegram plumbing exists for Patrick's reports.
3. **The long clock** (pillar 5): fed/starved totals are already accumulating in
   state/voyd_state.json. Decide the two world-event thresholds and what each does.
4. **Watch tonight's 03:00 cron** — it will commit cycle data on feat/the-retelling
   (commit_data_changes commits to the checked-out branch).
   Funnel /llm is restored and Act 2 verified live — but watch that the other hermes
   instance (mythomancer, port 8767) doesn't clobber the funnel mount again; if Act 2
   404s, re-run: `tailscale funnel --bg --set-path=/llm http://127.0.0.1:8081`
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
