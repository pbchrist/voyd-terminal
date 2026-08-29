---
name: voyd-story-room
description: Run the Voyd Terminal as a Hermes multi-agent story evolution room. Expert Phantom Walkers prosecute structure, mutations compete, and Patrick-derived Story Genome laws accumulate through an Acumen Keeper.
version: 3.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [storytelling, narrative, delegation, multi-agent, voyd, acumen, evolution]
    category: creative
    requires_toolsets: [delegation, terminal, file]
---

# Voyd Story Room

Use this skill whenever Patrick asks to evolve, fix, audit, improve, playtest, generate, or restructure the Voyd Terminal story.

This is a real Hermes multi-agent workflow. Do not replace the Phantom Walkers with one LLM pretending to be six reviewers.

## Load first

Read these before doing story work:

- `references/STORY_PHYSICS.md`
- `references/ROOM_PROTOCOL.md`
- `references/ACUMEN_PROTOCOL.md`
- project `story_room/genome.json`
- project `story_room/walkers/*.md`
- `story/README.md` and reachable `story/scenes/*.md` as the primary reader-facing fiction
- `story_room/frontier.json` as the canonical-head / active-frontier ledger
- the underlying narrative data/code for continuity and state verification

Do not trust summaries when the story itself is available. The `story/` fiction is the thing being written; internal graphs and packets support it rather than replacing it.

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

The Story Director may accept autonomously when one repair is structurally justified, canon-safe, and independently demonstrated to remove the targeted failure without introducing a worse one. Ask Patrick only at a genuine unresolved artistic fork.

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

The **Acumen Keeper** is a separate delegated role and must also use `background=false`. It never writes prose. It compares surviving mutations with `story_room/genome.json`, preserves Patrick's prior structural judgments, and decides whether inherited acumen already resolves the fork.

Selection rules:

1. If no mutation survives, rebuild from the diagnosed root cause.
2. If exactly one mutation survives, select it.
3. Active hard Genome laws may eliminate mutations that repeat already-decided structural mistakes.
4. If multiple structurally valid futures remain and the Genome does not compel one, stop at a **human speciation gate**.

For a human speciation gate, show Patrick only the irreducible artistic fork, usually 2-4 compact options in this form:

`A — structural change -> story consequence -> price`

Do not dump pages of prose on him. Ask for a selection and, when useful, one sentence of why.

After Patrick chooses, the Acumen Keeper records the complete fork and extracts reusable structural law. Explicit laws activate immediately. Inferred laws remain candidates until a second independent Patrick decision confirms them. Rejections are inherited too.

Use `story_room/genome.py` and `story_room/speciation.py` rather than inventing ad-hoc memory formats.

## Dramatist

Only after selection does a Dramatist implement the chosen structural species in the reader-facing `story/` prose and any underlying playable state required to support it. Every accepted cycle must leave a readable narrative advance, repair, or branch differentiation; internal state-only mutations are insufficient. Update `story_room/frontier.json` whenever the canonical frontier or active leaves change.

The reader surface must never expose node IDs, lifecycle predicates, rubric scores, agent names, or implementation terminology.

Only after selection does the Dramatist implement the chosen structural species in playable nodes/prose as needed for system continuity. Structure comes first. The Dramatist may not quietly alter the selected causal design to rescue a line it likes.

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
- do not ask Patrick to choose when inherited acumen already clearly decides the issue
