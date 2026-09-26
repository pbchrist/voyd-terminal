# Story Room causal state

`frontiers.json` is the machine-readable state of every reachable live leaf.
It does not replace the fiction. It records only consequences the fiction has earned.

## Authority
1. `lore/canon/CORE_LAWS.md` governs Voyd cosmology.
2. `lore/canon/voyd_mythography.md` is immutable source canon.
3. `story/scenes/*.md` is reader-facing Terminal canon.
4. `frontiers.json` is a structured projection of that Terminal canon.

If structured state disagrees with the scene, the scene wins and state must be repaired.
A Story Room cycle may propose new state, but it becomes canonical only with accepted fiction.

## Butterfly-effect rule
Every accepted choice must leave at least one durable causal trace: a fact learned,
relationship changed, resource spent, obligation incurred, capability changed, object state
changed, or new pressure created. Later scenes retrieve those traces instead of re-summarizing
prior prose.

The protagonist's name is permanently `WITHHELD`. `role` and `want` remain null until the
fiction establishes them. Empty `available_actions` means the current leaf has not yet
dramatized a choice; the next planner must create actions rather than inventing them here.
