# Phantom Writers' Room Protocol

## Cycle

1. **Story Director** assembles one story packet from the actual playable story: current Terminal spine, player state, unresolved setups/payoffs, source-canon boundaries, active Story Genome laws, and prior walker reports.
2. Director uses Hermes `delegate_task(tasks=[...])` to spawn all six Phantom Walkers in parallel. They walk the story in order and report the earliest structural wound. They do not edit files.
3. Director preserves each report unchanged and sends the complete evidence to a separate **Structural Editor**.
4. Structural Editor identifies root cause and creates **2-4 structurally distinct mutations**, not cosmetic rewrites. Each mutation declares causal consequences and downstream obligations.
5. **Canon/Continuity Steward** prosecutes every mutation. Concrete canon contradiction, impossible state transition, or missing causal obligation blocks it.
6. The same logical Phantom Walkers walk every surviving mutation. A structural failure eliminates the mutation; no numeric total can rescue it.
7. **Acumen Keeper** compares survivors with `story_room/genome.json` and runs the speciation rule in `ACUMEN_PROTOCOL.md`.
8. If inherited hard law leaves one survivor, the room may select autonomously. If multiple structurally valid futures imply different stories and the Genome does not decide, stop at a **human speciation gate** for Patrick.
9. After selection, Acumen Keeper records the decision and proposed/confirmed laws. **Dramatist** implements the selected structural species in playable nodes/prose.
10. The six logical walkers replay the implementation. A revision succeeds only when the targeted wound disappears without creating a worse earlier wound.

## Recursive story physics

Every dramatic unit must operate as:

`claim / desire / pressure -> counterforce -> changed state`

This is recursive:

`line -> exchange -> beat -> scene -> sequence -> act -> whole story`

The larger unit must emerge from collisions inside it. Labels such as "turn", "ordeal", or a rising `tension_delta` do not count as drama.
## Walker report contract

Every report must include:

- `walk_until`
- `choices_made`
- `first_failure`
- `atomic_dialectic`
- `scene_function`
- `macro_effect`
- `choice_integrity`
- `continuity`
- `repair_or_mutation_pressure`
- `verdict`

No overall numeric score. Consensus is evidence, not democracy.

## Mutation contract

Every Structural Editor mutation must include:

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

Mutations must differ in dramatic machinery. Three phrasings of the same fix are one mutation, not three.

## Authority boundaries

**Source canon** is read-only: facts from The Gate of Nyandor books and author-approved mythography.

**Terminal story canon** is mutable: current scene order, objectives, relationships, setups, payoffs, consequences, branches, state, and Terminal-only facts.

The Structural Editor may change Terminal canon only after a mutation survives the selection process. A Dramatist may not quietly alter structure while writing prose.

## Phantom Walker identity

Hermes child processes are fresh. Logical walker identity persists through dossier files and prior reports under:

`story_room/reports/<cycle-id>/<walker-id>.md`

Each replay receives its prior finding so recurring wounds and failed repairs remain visible.

## Forbidden shortcuts

- no `tension_delta` arithmetic as proof of drama
- no forced walker routes to guarantee an archetype
- no single writer agent generating and approving its own work
- no Save the Cat beat-sheet governance
- no vague "great literature" scoring
- no canon-event slot machine
- no imagery/lore/surprise standing in for causal turns
- no averaging away a demonstrated failure
- no inferred Patrick preference becoming doctrine after one ambiguous decision
