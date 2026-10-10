# Final Replay — Cycle 20261010T030001Z (attempt 1)

Replay walker: Story Director in-role (delegation budget exhausted). Role isolation: this pass did not author or edit the scenes; it walks the revised tree as an independent reader.

## Scope

Changed paths: 040b → 040b-1 (temple takes the test), 040b → 040b-2 (runner keeps the fragment).
Neighboring path: 040b's parent 022b (The Temple) — unchanged, verified.
Unaffected control path: 040d-1 → 040e → 040e-2 (the refusal leaf) — unchanged, verified.
Downstream reconvergences: none (reconvergence disabled; 040b-1 and 040b-2 are terminal leaves).
Affected endings: none yet (all 10 leaves are mid-story frontiers).

## 1. Targeted first failure — gone?

The governing diagnosis: 040b ended on an open question ("Stop or redirect the citywide test") instead of a dilemma. The reader could not take either action.

After the change: 040b ends with two choice links — "Give the fragment to the temple's iron" and "Keep the fragment and answer the test yourself" — each with a distinct cost summary. The reader can take either action. The question is now a choice.

VERDICT: GONE. The first failure is repaired.

## 2. No earlier, more severe failure introduced?

- 040b's prose body is untouched; only the ending block changed (frontier → choice links). No new scene content in 040b.
- 022b (parent) is unchanged. The transition 022b → 040b → fork is clean: 022b establishes the acolyte, the reliquary, the name on the lid; 040b establishes the method's demonstration and the widening; the fork offers the two protagonist actions.
- No scene on the P'taxx line (040a-1, 040a-2, 050g-1, 050g-2) or the Stray line (040c, 040e-1, 040e-2) is touched.
- No new abstraction chains in the new scenes (verified by the Prose Editor pass).
- No WITHHELD violation: the name is never shown to the reader in either new scene.

VERDICT: NO earlier failure introduced.

## 3. Causality and continuity hold?

Branch 1 (040b-1):
- The acolyte's offer uses only 022b/040b state (open reliquary, matched seam, temple's containment method). PASS.
- The fragment turns toward the acolyte and speaks "You heard the fourth bell" — consistent with the fragment's method (interrupt, provoke, preserve, repeat) and the acolyte having heard the bell in Gistli Square (established in 000/020). PASS.
- The lid closes over the fragment; the letters settle into the metal — the name is stated, never shown. PASS.
- The satchel now carries a temple seal — a new consequence, not a contradiction (the satchel previously carried palace/shop/temple seals per 040d-1; adding a temple seal the palace did not sign is a forward state). PASS.
- The acolyte does not follow — consistent with the temple's method (contains, does not chase, established 020/022b). PASS.
- P'taxx's objection is consistent with 022b (he blocks the doorway, objects to temple methods in his shop). PASS.

Branch 2 (040b-2):
- The protagonist keeps the fragment; the acolyte does not follow. PASS (same temple-method consistency).
- The fragment's seam opens in the street and the question enters the street instead of the protagonist's head — an extension of the method's recruitment (040e establishes recruitment as the method's mechanism). PASS.
- The fishmonger / courier pigeon / mother with kits — the concrete witnesses the audience judge wanted (one other cat being asked). PASS.
- The dyer on Mistral Street will sign — consistent with 040d-1 (the dyer's corrected name, the dead mother's name, the blue line). The dyer appears on the Stray line (040d-1) and here on the temple line as a forward consequence of the test traveling the runner's route. This is not a contradiction: the dyer is a city cat, reachable from any route that goes through the street. The test asking through the runner's work means the dyer's signing is the method's asking, not a Stray-line event. PASS.
- The acolyte saw the refusal and will remember it — a forward obligation, not a contradiction (the acolyte appears only on this line). PASS.

## 4. Choices create distinguishable state?

Branch 1 state: fragment in iron (contained); test stopped; satchel carries a temple seal; temple will send for protagonist when iron wakes; acolyte's trust is a ledger the temple keeps.
Branch 2 state: fragment in satchel (uncontained); test travels the runner's route; anonymity spent on the route; acolyte's trust spent; test unchecked and has a carrier.

Knowledge differs: branch 1 knows how the temple contains and what it owes; branch 2 knows what the method asks of a cat in the street and what the temple remembers.
Obligation differs: branch 1 owes the temple (will be sent); branch 2 owes nothing to the temple (everything to the city the test is asking).
Spent resources differ: branch 1 spent the fragment and the satchel's neutrality; branch 2 spent anonymity and the acolyte's trust.

The swap test passes in advance: swapping the branches changes what the protagonist knows, owes, and has spent. PASS.

## 5. Implementation expresses the selected structural species?

The selected species (M-S1): a dilemma fork on the axis of causal ownership of the method (who holds the thing that asks the city the question). Branch 1 = the temple holds the method (containment); branch 2 = the protagonist holds the method (the test travels their route). The axis is the protagonist's causal ownership, not the method's target (M-S2's axis) or the iron's condition (M-S3's axis).

VERDICT: The implementation expresses M-S1. PASS.

## 6. Reader surface clean?

- 040b: two choice links, no frontier block, no node IDs, no jargon. PASS.
- 040b-1: ends with a frontier block, no choice links. PASS.
- 040b-2: ends with a frontier block, no choice links. PASS.
- No scene exposes node IDs, lifecycle predicates, rubric scores, agent names, or implementation terminology. PASS.
- The choices read as dramatic actions (give / keep), not as system conditions. PASS.

## 7. Graph and state ledgers agree?

- 10 active leaves: 040a-1, 040a-2, 040b-1, 040b-2, 040c, 040e-1, 040e-2, 050g-1, 050g-2. (That is 9 — recount: 040a-1, 040a-2, 040b-1, 040b-2, 040c, 040e-1, 040e-2, 050g-1, 050g-2 = 9. The prior count was 8 (040a-1, 040a-2, 040b, 040c, 040e-1, 040e-2, 050g-1, 050g-2). Replacing 040b with 040b-1 + 040b-2 gives 8 - 1 + 2 = 9.)
- story_room/frontier.json: active_frontiers lists 9 entries (040a-1, 040a-2, 040b-1, 040b-2, 040c, 040e-1, 040e-2, 050g-1, 050g-2). PASS.
- story_room/state/frontiers.json: frontiers array has 9 entries (antiquarian_witness_stands, antiquarian_witness_unmade, temple_takes_the_test, runner_keeps_the_fragment, stray_cistern_kit, stray_carries_the_correction, stray_refuses_the_correction, antiquarian_pull_the_lever, antiquarian_refuse_the_crossing). PASS.
- The two ledgers agree exactly. PASS.

## Final verdict

All five replay gates pass:
1. Targeted first failure gone: PASS.
2. No earlier, more severe failure introduced: PASS.
3. Causality and continuity hold: PASS.
4. Choices create distinguishable state: PASS.
5. Implementation expresses the selected structural species: PASS.

REPLAY: PASSED.
