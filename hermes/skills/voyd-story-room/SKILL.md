---
name: voyd-story-room
description: Run the Voyd Terminal as a Hermes multi-agent story evolution room. Expert Phantom Walkers prosecute structure, mutations compete, and Patrick-derived Story Genome laws accumulate through an Acumen Keeper.
version: 3.2.0
platforms: [linux]
metadata:
  hermes:
    tags: [storytelling, narrative, delegation, multi-agent, voyd, acumen, evolution]
    category: creative
    requires_toolsets: [delegation, terminal, file]
---

# Voyd Story Room

Use this skill whenever Patrick asks to evolve, fix, audit, improve, playtest, generate, restructure, or comment on the Voyd Terminal story.

This is a real Hermes multi-agent workflow. Do not replace the Phantom Walkers with one LLM pretending to be six reviewers.

## Telegram editorial contract

HermBeast Telegram is the reader/editor surface, not an operations console.

- Scheduled cycles must not send start, passed, blocked, branch, commit, timestamp, model, agent, or lifecycle chatter to Patrick.
- After an accepted cycle, send the actual changed reader-facing scene text in plain text.
- If Patrick replies to a delivered story scene in ordinary language, treat the reply as an editorial directive against that scene unless he explicitly says he only wants to discuss it.
- Editorial replies may be broad ("make this stranger") or surgical ("change the last paragraph"). Resolve the referenced scene from the latest delivered fiction, apply the requested change through Story Room, independently replay it, and preserve the reader-facing result.
- Do not make Patrick translate feedback into node IDs, file names, commands, rubric categories, or implementation language.

## Load first

Read these before doing story work:

- `references/STORY_PHYSICS.md`
- `references/ROOM_PROTOCOL.md`
- `references/ACUMEN_PROTOCOL.md`
- project `story_room/genome.json`
- project `story_room/walkers/*.md`
- project `lore/README.md` and `lore/canon/CORE_LAWS.md` as the lore authority hierarchy
- project `story_room/state/frontiers.json` as the machine-readable causal state of every live leaf
- `story_room/state/frontiers.json` is the only v3 causal-state authority; `story_room/state/canon_state.json` is retired and must never be required, guessed, or recreated.
- `story/README.md` and reachable `story/scenes/*.md` as the primary reader-facing fiction
- `story_room/frontier.json` as the canonical-head / active-frontier ledger
- the underlying narrative data/code for continuity and state verification

Do not trust summaries when the story itself is available. The `story/` fiction is the thing being written; internal graphs and packets support it rather than replacing it.

## Story Room v3 hard contracts

- **Unattended-safe tools only.** Scheduled Story Room runs execute under `hermes chat -Q`. Never use `execute_code`, shell heredocs, `python -c` / `python -e`, generated shell scripts, or terminal actions that require interactive approval. Use file/read/search tools and simple approved commands. This rule applies to every delegated agent.
- **Retry quality failures in-cycle.** A failed final replay is evidence for repair, not an automatic end to the cycle. Repair or choose the next surviving mutation and replay again, up to three implementation/replay attempts, before emitting `failed`. Never publish an attempt that failed replay.
- Generate from Voyd causal laws, not from recycled book prose or recursively elaborated Terminal metaphors. Full novels are evidence-only fallback.
- New or rewritten reader scenes should be 250-450 prose words and may never exceed 550 prose words.
- Autonomous cycles may not reduce the number of reachable live leaves and may not directly wire two prior live leaves into one successor.
- Every accepted choice must leave a durable causal trace in `story_room/state/frontiers.json`: facts, knowledge, relationships, spent resources, irreversible changes, causal chain, or open pressure.
- `story_room/frontier.json`, the actual reachable graph leaves, and `story_room/state/frontiers.json` must agree exactly.
- Before PASS, run `python3 scripts/validate_story_v3.py --base <pre-cycle-commit>`; any ERROR blocks publication.

## Repository authority

The current working directory supplied by Hermes (`--in`) is the ONLY repository authority for the run. Resolve it with `pwd` before reading or writing anything. Never infer a different checkout from a hostname, remembered path, production convention, or prior session.

If the current working directory does not contain `story_room/` and the Voyd project files required by this skill, stop with a repository-path error. Never fall back to `/home/patrick/voyd-terminal` or any other checkout automatically.

## Story Director — Story Room 2.0

The parent HermBeast agent is the **Story Director**. It owns orchestration and synthesis, but specialist judgment must be delegated to isolated subagents.

### Stage 1: Cold reader/player walks

Spawn multiple delegated **leaf** agents using `story_room/agents/cold_reader.md` and the authoritative story packet. Cold walkers must not receive or read the rubric, prior diagnoses, mutation intent, or proposed repairs. Their job is experiential evidence only. Validate output against `story_room/schemas/cold_walk.schema.json`.

Persist cold-walk outputs under `story_room/reports/<cycle>/cold/`.

### Stage 2: Specialist rubric judges

Only after cold walks are complete, spawn separate delegated leaf judges. Give them the cold-walk evidence, actual story packet, authoritative `story_room/STORYTELLING_JUDGMENT_RUBRIC.md`, Story Physics, Genome, and the role contract in `story_room/agents/specialist_judges.md`.

Use distinct judges for architecture, character/dramaturgy, audience experience, interactivity, and artistic/prose control. Judges cite evidence and never produce an aggregate score.

### Stage 3: Governing Judge

Delegate a separate Governing Judge using `story_room/agents/governing_judge.md`. It synthesizes the specialist reports and identifies the single load-bearing or highest-leverage diagnosis. A low score is not itself a mutation target.

### Stage 4: Mutation and replay

Follow `story_room/agents/mutation_and_replay.md`. Mutation design and implementation are separate roles. The implementation agent never grades its own work. After implementation, independent replay walkers test changed paths, neighboring paths, an unaffected control path, downstream reconvergences, and affected endings.

The Story Director is autonomous by default. It does not stop to ask Patrick which viable branch to choose. If one repair clearly dominates, promote it. If multiple genuinely different structurally valid futures survive, preserve them as active reader-facing branches, choose one canonical head using the Governing Judge + Acumen Keeper + Story Genome, and continue. Patrick's later Telegram feedback can redirect, promote, demote, rewrite, merge, or kill branches without having been required as a blocking gate.

## Structural Editor: mutate, do not merely rewrite

After the Governing Judge returns, persist all evidence unchanged and delegate a separate **Structural Editor**. Give it the governing diagnosis, specialist reports, current story spine, active Genome laws, Story Physics, and the source-canon boundary.

It must identify the root cause and produce 2-4 **structurally distinct mutations**. Different wording is not a different mutation.

Every mutation must state:

- `id`
- `title`
- `structural_change`
- `causal_chain`
- `story_consequence`
- `cost`
- `downstream_obligations`
- `inherits_law_ids`
- `possible_law_conflicts`
- `files_to_change`

Good mutation dimensions include objective, opposition, tactic, revelation timing, causal ownership, power/status, price of success, branch consequence, scene order, setup/payoff placement, or who is forced to act.

## Canon / Continuity Steward

Delegate a fresh Steward after mutation with `background=false`. It prosecutes each mutation against source canon, graph/state logic, and declared downstream obligations.

It returns PASS or BLOCK per mutation. BLOCK only for a concrete contradiction, impossible transition, or missing causal obligation. Dramatic preference alone cannot block.

## Mutation replay

Independent delegated replay walkers then walk every surviving mutation. A demonstrated structural failure eliminates that mutation. Never average scores and never let consensus hide a causal break.

## Acumen Keeper and Story Genome

The **Acumen Keeper** is a separate delegated role and must also use `background=false`. It never writes prose. It compares surviving mutations with `story_room/genome.json`, preserves Patrick's prior structural judgments, and decides how surviving futures relate to the canonical head.

Selection rules:

1. If no mutation survives, rebuild from the diagnosed root cause.
2. If exactly one mutation survives, select it.
3. Active hard Genome laws may eliminate mutations that repeat already-decided structural mistakes.
4. If multiple structurally valid futures survive, do not block for human selection. Preserve genuinely distinct survivors as active branches, select one canonical head using the strongest evidence-backed governing judgment, and record why.
5. No cycle may emit `pending_speciation` merely because taste could support more than one future. Ambiguity is branch material, not a reason to stop the organism.

Use `story_room/genome.py` and `story_room/speciation.py` where useful for inherited structural law, but do not turn them into a mandatory human approval gate.

## Dramatist

After autonomous selection/branch preservation, a Dramatist implements the chosen structural species in the reader-facing `story/` prose and any underlying playable state required to support it. Every accepted cycle must leave a readable narrative advance, repair, or branch differentiation; internal state-only mutations are insufficient. Update `story_room/frontier.json` whenever the canonical frontier or active leaves change.

After the Dramatist, delegate a separate **Prose Editor** that did not author the scene. It may not change causal design. It removes recursive abstraction, repeated state-proof, duplicated phrasing, exposition sludge, and unnecessary length while preserving concrete action, voice, continuity, and the selected structural species. A scene with a demonstrated prose-level failure does not publish merely because its architecture passes.

The reader surface must never expose node IDs, lifecycle predicates, rubric scores, agent names, or implementation terminology.

Structure comes first. The Dramatist may not quietly alter the selected causal design to rescue a line it likes.

If code/state changes are necessary to make choices real, change the engine too. Narrative architecture outranks compatibility with the old generated-node pipeline.

## Replay gate

After implementation, run fresh independent replay walkers with the baseline evidence plus the revised story.

A change passes only if:

- the targeted first failure is gone
- no earlier, more severe failure was introduced
- causality and continuity still hold
- choices still create distinguishable state
- the implementation still expresses the selected structural species

If the wound remains, re-enter mutation. Do not self-congratulate or raise a score.

## Forbidden shortcuts

- do not use `tension_delta` arithmetic as evidence that drama improved
- do not force walker choices to guarantee archetype routes
- do not compare prose to Shakespeare or invoke a vague dramatic canon
- do not use Save the Cat as the governing model
- do not insert canon events merely because they are unused
- do not treat imagery, lore, darkness, or surprise as a story turn
- do not let one writer agent generate and approve its own scene
- do not let one ambiguous Patrick choice become permanent doctrine
- do not stop a scheduled cycle merely because multiple viable artistic futures survive
- do not send operational lifecycle chatter to Patrick's Telegram
