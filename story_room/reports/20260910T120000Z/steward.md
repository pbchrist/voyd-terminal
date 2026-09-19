# CANON / CONTINUITY STEWD — PROSECUTION
## Cycle 20260910T120000Z — M1 / M2 / M3

**Prosecutor role:** Canon & Continuity Steward.
**Standard of proof:** BLOCK only on a *concrete* contradiction, an *impossible transition*, or a *missing causal obligation*. Dramatic preference is not grounds for BLOCK.
**Scope reviewed:** genome.json (laws), STORY_PHYSICS.md, frontier.json, mutations.md, and all 24 scene files under `story/scenes/` (with focus on the declared fork/reconvergence scenes and the protected 040a chain).

**Verdicts up front:**

| Mutation | Dimension | Verdict |
|---|---|---|
| M1 | Knowledge (files / names / replays) | **PASS** |
| M2 | Obligation / debt (P'taxx / Temple / stray) | **PASS** |
| M3 | Spent resource (anonymity filed / named / replayed) | **PASS** |

All three are HONE, declare "no new files," and are canon-safe. No mutation makes the protagonist learn or be told the name. No mutation touches the 040a fork's causal ownership. No mutation edits source/book canon. No mutation creates a link to a non-existent file or leaves a scene with both choice links and a frontier block. The detailed grounds follow.

---

## 0. Shared findings that apply to all three mutations

### 0a. Withheld-name canon — NOT violated (M1/M2/M3)

The story's withheld object is the protagonist's NAME: filed by the ledger, legible to the SYSTEM, not to the protagonist. I read every scene that touches the name. The corpus is consistent and the name is never *given* to the protagonist:

- **022b L31–35** — "The name burns across the lid... Your name." The name is *shown to the system* (the lattice/reliquary); the young acolyte reacts ("That is impossible") — the reader and the system see it, the protagonist does not learn it.
- **040b L49–51** — "Letters burn across its iron lid... Your name." System-readable, not protagonist-readable.
- **040c L55–57** — "Beneath the unfinished outline, letters appear. Your name. The stray reads it aloud." Note: *the stray* reads it aloud, not the protagonist. The name stays out of the protagonist's knowledge.
- **040d L41** — "Under the stray's skin, your name lengthens by one letter." And **L61** — "The orange projection turns its head and **speaks your name in your own voice**." This is the *system* speaking the name in the protagonist's voice — the name is legible to the system, and the city hears it. The protagonist is the *carrier* of the voice, not the one who learns the name. This is the exact "legible to the system, not to the protagonist" convention the task's canon note codifies.
- **011 L119–125 / 022a L19–21** — "You already know what it says. **YOU LOOKED AWAY.**" The *door's title* is the known line; it is a state word, not the name.
- **040a-03 / 040a-let-01 / 040f / 040g** — "The name is still filed." Persistent, withheld, system-owned.

The "named" facet (M1/M2/M3) is therefore correctly understood as the **ledger naming the subject in its own record** — the name is legible to the SYSTEM, not to the protagonist. **None of M1, M2, or M3 causes the protagonist to learn or be told the name.** All three *extend* the existing system-readable convention (filed / named / replayed) rather than inverting it.

**Canon check on the name: PASS for all three.** No BLOCK.

### 0b. 040a witness fork causal ownership — UNTOUCHED (M1/M2/M3)

Protected chain: 040a (commit/refuse) → 040a-03 (refuse, performed) → 040a-let-01 (the recall) → 040f (cost) → 040g (canonical head, ACTIVE FRONTIER).

I read the chain in full. The causal ownership is intact:
- **040a L29–35** — two genuinely distinct actions under pressure (commit / refuse), each landing a changed state; the pre-declared act is deleted (performed agency).
- **040a-03 L1–37** — the *protagonist's performed act* (physically NOT crossing, NOT putting shoulder to shoulder, NOT letting eyes fall into the angle) is the cause. The copy stays a witness; the record about the protagonist stays unfinished; the cost is the lever.
- **040a-let-01 L31–33** — "You caused this. You held your gaze. You refused the flinch. And the ledger, denied its method, did something new... The reclassification is the consequence of your holding, not a gear that was always turning." The **protagonist's act causes the recall**; the system's response (recall) is a **NEW method** — "It does not file. It does not provoke. It does not wait. It *recalls*." (L11). This is exactly candidate law_bb750d1bdb10: protagonist causes the turn, system responds with a new method, not a reversion.
- **040f / 040g** — the recall's route-specific cost (P'taxx as a subject) is landed, and 040g is the canonical head (ACTIVE FRONTIER).

All three mutations **decline to touch** this chain. Their declared treatment of 040a's leaves:
- M1: leaves "inherit the Antiquarian facet" — an *epistemic* inheritance, no change to act → recall → cost causality.
- M2: leaves are "different **payments** of the same debt, not new debts" — the commit leaf *pays* the Antiquarian debt in the ledger's currency; the refuse leaf *keeps it unpaid*. This is a re-description of the *same* two actions, not a re-assignment of who causes the turn.
- M3: leaves are "different **spends** of the same resource, not new spends" — commit spends the WANT in the ledger's currency; refuse spends the lever. Again, a re-description of the *same* two actions.

**No mutation re-assigns causal ownership, reverts the test to "will you flinch," or makes the system deliver the decisive move.** The recall remains the protagonist-act → new-method (recall) → cost (P'taxx) → 040g.

**Canon check on the 040a fork: PASS for all three.** No BLOCK. (M3's explicit invocation of law_bb750d1bdb10 as "extended, not violated" is consistent with the chain as written.)

### 0c. Source-canon boundary — RESPECTED (M1/M2/M3)

Law_f1d61deb3858: "Source book canon is immutable inside the Terminal; only Terminal story canon may evolve." All three mutations operate exclusively on Terminal story canon (scene text under `story/scenes/`). None inserts a source-book canon event, none rewrites Gate of Nyandor mythography, none edits `voyd_canon_mythography.md` or the wiki. The mutations are pure in-story structural HONE. **PASS for all three.**

### 0d. Scene-ending invariant (choice links XOR frontier block) — PRESERVED (M1/M2/M3)

Every scene in the corpus ends with **exactly one** of: choice links OR a frontier block — never both. I verified the boundary scenes:

| Scene | Ending |
|---|---|
| 000 | choice links (3) |
| 010 | choice links (2) |
| 011 | choice link → 022 (1) |
| 020 | choice links (2) |
| 021a | link → 022 (lattice) |
| 021b | link → 022 (lattice) |
| 030 | choice links (2) |
| 031 | choice link → 040c (1) |
| 032 | choice link → 040d (1) |
| 022 | choice links → 022a / 022b (2) |
| 022a | choice link → 040e (1) |
| 022b | choice link → 040b (1) |
| 040b | **ACTIVE FRONTIER** |
| 040c | **ACTIVE FRONTIER** |
| 040d | **ACTIVE FRONTIER** |
| 040e | choice link → 040a (1) |
| 040a | choice links → make / 040a-03 (2) |
| 040a-make | **ACTIVE FRONTIER** |
| 040a-03 | choice link → let-01 (1) |
| 040a-let-01 | choice link → 040f (1) |
| 040f | choice link → 040g (1) |
| 040g | **ACTIVE FRONTIER** (canonical head) |

No mutation is a structural re-route: all are HONE (text/state within existing scenes), and none deletes a scene or re-targets a link to a non-existent file. The invariant is preserved across every edit. **PASS for all three.**

### 0e. Graph reachability & link integrity — PRESERVED (M1/M2/M3)

Every choice link in the corpus targets an existing file. I verified all targets resolve to a real scene file. No mutation introduces a link to a non-existent file (all HONE, no new files, no re-targets). Downstream states remain reachable:

- Antiquarian: 000 → 010 → 011 → 022 → 022a → 040e → 040a → {make / 040a-03} → let-01 → 040f → **040g**.
- Temple: 000 → 020 → 021b (or 021a) → 022 → 022b → **040b**.
- Stray: 000 → 030 → {031 → 040c | 032 → 040d}.

The mutations carry route-specific state *into* 022/022a/022b and *out* to 040b/040c/040d/040e/040a. All of these remain reachable and consistent. The orphaned scene `040a-the-second-question.md` (frontier.json orphaned_scenes) is already unreachable (its terminal link was re-routed to 022 in a prior cycle) and is *not* in any mutation's files_to_change, so it stays a structural reference — no new orphan is created, none is broken. **PASS for all three.**

### 0f. Law inheritance — NO active hard law violated (M1/M2/M3)

- **law_a509c75fb6a1** (active, `require`) — "within reach of every frontier there must be a choice between two actions under pressure whose consequences differ in what the protagonist **knows, owes, or has spent**." This is the law all three mutations are *repairing*. M1 = "knows," M2 = "owes," M3 = "has spent." Each directly satisfies the law's tripartite clause. No contradiction.
- **law_4ca0ffd21c42** (active, `prefer`) — causality outranks imagery. All three mutations produce a *causal* turn (collision of route-carried state), not an imagery label. Compliant.
- **law_5361b415500d** (active, `require`) — "a scene earns existence by changing what the next scene must obey." The 022 collision turn changes what the next scene (022a/022b → corridor) must obey. Compliant.
- **law_80984901e75f** (active, `require`) — sequences must answer/complicate/negate prior scenes. The reconvergence *collides* with, rather than re-asserts, the route state. Compliant.
- **law_4d3da1051141** (candidate) — reconvergence branch-awareness. The mutations *extend it upstream*: branch-awareness is achieved in the branches (each route lands its own facet/debt/spend) rather than re-asserted downstream in the node. This is an extension, not a violation. The mutations flag it as "superseded in spirit (branch-awareness moved upstream); Acumen Keeper may revise." No BLOCK on a candidate law; the extension is coherent.
- **law_bb750d1bdb10** (candidate) — apex-head causal ownership. M3 invokes it; the 040a chain it governs is left untouched (see 0b). Consistent.

No active `require` law is violated by any mutation. **PASS for all three.**

---

## M1 — KNOWLEDGE: each route reveals a different facet of the method

**VERDICT: PASS**

### Canon check
- **Withheld name:** PASS. The Temple "names" facet is the *ledger naming the subject in its own record* (021a reliquary / 022b "The name burns across the lid. Your name.") — the name stays system-legible, never learned by the protagonist. The "files" facet (011) is a filed *frame*, not a name reveal. The "replays" facet (031/032) is a proxy re-enactment (kit/sliver). None teaches the protagonist their name.
- **040a fork:** PASS. Antiquarian facet inherited by the leaves is epistemic only; act → recall → cost → 040g is untouched (see 0b).
- **Source-canon boundary:** PASS. In-story structural HONE only.

### State logic
- **Reachability:** The three facets are each *landed* as a stated true proposition in the route's signature scene (011 filing / 021a reliquary / 031–032 kit+scar), then carried through 022 (singular shared reveal, kept whole) and forked in 022a/022b. Downstream 022a/022b/040b/040c/040d remain reachable. No non-existent-file link. No both-ends scene.
- **No impossible transition:** The "three methods wearing one face" collision is a *new state* produced by the incompatibility of the three knowledge states — it is a legitimate turn under STORY_PHYSICS (the larger unit produced by the collisions inside it), not a re-read. The "still" chains die because 022 asserts *new* state (the collision's result). This is a valid forward state, not a reversion.

### Downstream obligations
1. ✅ 011/021a/031/032 land their facet as explicit knowledge — declared and consistent with the scenes.
2. ✅ 022 closing presents the three points as three *readings* that collide — declared; the shared reveal stays singular (no split) while its interpretation forks.
3. ✅ 022a/022b carry their facet forward so 040b/040e/040c/040d have route-specific actions — declared.
4. ✅ **031 L87 route-bleed fixed.** L87 currently reads: "The Voyd... It is the door in the room behind the shop, seen from inside — the same ledger of looking-aways, the **same filed fragment**, the same countdown." The "door in the room behind the shop" + "the same filed fragment" is Antiquarian-route state bleeding into the Stray route (the stray has no shop, no high door, no filed fragment). M1 re-grounds L87 to the Stray *replay* facet (kit/sliver proxy), deleting or re-grounding the Antiquarian bleed. This is a genuine side-effect fix and is declared.
5. ✅ 040a fork untouched; leaves inherit the Antiquarian facet — consistent with 0b.

**No concrete contradiction, no impossible transition, no missing causal obligation. PASS.**

---

## M2 — OBLIGATION/DEBT: each route creates a different debt

**VERDICT: PASS**

### Canon check
- **Withheld name:** PASS. The Temple "named subject" debt is the *reliquary naming them* — the Temple has a named subject in its vessel; the name is the *ledger's* record, not information the protagonist learns. The P'taxx debt (filed proof in his shop) and the stray debt (kit on the cistern's rim) are obligation states, not name reveals. None teaches the protagonist their name.
- **040a fork:** PASS. The Antiquarian debt is inherited by the leaves as "different **payments** of the same debt, not new debts" — commit = pay in the ledger's currency; refuse = keep unpaid. This is a re-description of the *same* two actions, not a re-assignment of who causes the recall. Act → recall → cost → 040g untouched (see 0b).
- **Source-canon boundary:** PASS. In-story structural HONE only.

### State logic
- **Reachability:** Debts are *created* as explicit obligations in the signature scenes (011 P'taxx custodianship / 021a reliquary named subject / 031–032 kit on the rim). Carried through 022 (singular) and forked in 022a/022b. Downstream 022a/022b/040b/040c/040d remain reachable. No non-existent-file link. No both-ends scene.
- **No impossible transition:** The "three debts to three creditors that the lattice cannot pay in three currencies at once" collision is a *new state* (which debt to pay first; what the unpaid debts cost) — a legitimate forward turn, not a re-read or reversion.

### Downstream obligations
1. ✅ 011/021a/031/032 *create* their debt as an explicit obligation — declared and consistent with the scenes.
2. ✅ 022 closing presents the three debts as *incompatible* (cannot be paid at once) — declared.
3. ✅ 022a/022b carry their debt forward so 040b/040e/040c/040d have route-specific actions — declared.
4. ✅ **031 L87 fixed** — "the Antiquarian debt is not the Stray's." Same L87 bleed as M1 (see M1 §4); the P'taxx/filed-fragment Antiquarian debt is re-grounded so it does not leak into the Stray route. Declared side-effect fix.
5. ✅ 040a fork untouched; leaves extend the Antiquarian debt as different *payments* — consistent with 0b.

**No concrete contradiction, no impossible transition, no missing causal obligation. PASS.**

---

## M3 — SPENT RESOURCE: each route spends a different irreversible resource (anonymity)

**VERDICT: PASS**

This is the mutation closest to the withheld-name canon, so it is prosecuted most carefully.

### Canon check — withheld name (the critical test)
M3's three spends are all spends of **anonymity / unmeasurability**:
- **Antiquarian (filed):** "the protagonist's name is **FILED** in his shop. Irreversible: cannot be unfiled."
- **Temple (named):** "the protagonist becomes a **named subject**. Irreversible: cannot be unnamed."
- **Stray (replayed):** "the protagonist's name is **legible under the stray's skin**. Irreversible: cannot be unreplayed."

The question is whether any of these *makes the protagonist learn or be told the name*.

- **filed (Antiquarian):** The name is filed in P'taxx's shop — the *system/ledger* holds it. This matches 011/022a where the door's title is **FILED** and the known line is **YOU LOOKED AWAY** (a state word, not the name). The protagonist never reads the filed name. **Name stays withheld.**
- **named (Temple):** The reliquary *names* the subject — the name burns across the iron lid (022b L31–35). This is *exactly* the existing convention: the name is legible to the system (the lattice/reliquary), the acolyte reacts, the protagonist does not learn it. M3 does not add a reveal; it re-describes the *existing* 022b/040b naming as an irreversible spend. **Name stays withheld.**
- **replayed (Stray):** The name is legible under the stray's skin — this matches 032 L61–65 ("A name written beneath the skin... It is not his name. It is yours.") and 040c L55–57 (letters appear under the outline; *the stray* reads it aloud) and 040d L41 (name lengthens under the skin) + L61 (the projection *speaks it in the protagonist's voice*). In every case the name is system-legible; the protagonist is the carrier, never the learner. M3 re-describes this as an irreversible spend. **Name stays withheld.**

**None of the three spends teaches the protagonist their name.** M3's "named" facet is the ledger naming the subject in its own record — the name is legible to the SYSTEM, not to the protagonist — which is precisely the canon the task note codifies. **Canon check on the name: PASS. No BLOCK.**

### Canon check — 040a fork & law_bb750d1bdb10
M3 inherits law_bb750d1bdb10 (candidate) and declares it *extended, not violated*: the 040a fork's causal ownership is preserved, and the spend structure extends the state difference downstream. The Antiquarian spend (anonymity filed) is extended through the 040f/040g chain, where "P'taxx lost as a cost" is the *downstream extension* of the Antiquarian spend. I read 040f/040g: the recall's cost is the relationship with P'taxx (he becomes a subject), which is exactly "the relationship is the resource the recall spent." This is consistent — the spend structure flows forward without touching act → recall → cost causality. **PASS.**

### State logic
- **Reachability:** Spends are *irreversible costs* landed in the signature scenes (011 filed / 021a named / 031–032 replayed). Carried through 022 (singular) and forked in 022a/022b. Downstream 022a/022b/040b/040c/040d remain reachable. No non-existent-file link. No both-ends scene.
- **No impossible transition:** The "spent unmeasurability three different ways; the next move is a move of a measured cat" collision is a *new state* (what the protagonist has lost; what the lost state costs) — a legitimate forward turn. The spends are *irreversible* (cannot be unspent), which is what makes them a *spend* rather than a *toggle* — satisfying M3's own cost clause and STORY_PHYSICS's "irreversible action" requirement. No reversion.

### Downstream obligations
1. ✅ 011/021a/031/032 *spend* their resource as an explicit irreversible cost — declared and consistent.
2. ✅ 022 closing presents the three spent states as *irreversible* — declared.
3. ✅ 022a/022b carry their spent state forward so 040b/040e/040c/040d have route-specific actions — declared.
4. ✅ **031 L87 fixed** — same L87 Antiquarian→Stray bleed (see M1 §4 / M2 §4); the "same filed fragment / door in the room behind the shop" Antiquarian spend is re-grounded to the Stray replayed spend. Declared side-effect fix.
5. ✅ 040a fork untouched; leaves extend the Antiquarian spend (commit spends the WANT in the ledger's currency; refuse spends the lever, keeps the WANT) as different *spends of the same resource* — consistent with 0b.
6. ✅ 040f/040g extend the Antiquarian spend (the P'taxx relationship is the resource the recall spent) — consistent with the 040f/040g text as written.

**No concrete contradiction, no impossible transition, no missing causal obligation. PASS.**

---

## 1. Consolidated adjudication

| Check | M1 | M2 | M3 |
|---|---|---|---|
| Withheld-name canon (protagonist learns/told name?) | No → PASS | No → PASS | No → PASS |
| 040a fork causal ownership (protagonist causes recall; system = new method) | Untouched → PASS | Untouched (payments) → PASS | Untouched (spends; law_bb750d1bdb10 extended) → PASS |
| Source-canon boundary (no Gate of Nyandor edits) | Respected → PASS | Respected → PASS | Respected → PASS |
| Downstream state (022a/022b/040b/040c/040d) reachable & consistent | Yes → PASS | Yes → PASS | Yes → PASS |
| No choice link to non-existent file | Yes → PASS | Yes → PASS | Yes → PASS |
| No scene with both choice links AND frontier block | Yes → PASS | Yes → PASS | Yes → PASS |
| 031 L87 route-bleed fix (declared) | Fixed → PASS | Fixed → PASS | Fixed → PASS |
| 021b restructure (Temple state carried intact, not pre-spent) | Declared → PASS | Declared → PASS | Declared → PASS |
| 040a fork untouched | Yes → PASS | Yes → PASS | Yes → PASS |
| No active hard Genome law violated | Yes → PASS | Yes → PASS | Yes → PASS |

**FINAL VERDICTS:**
- **M1: PASS** — canon-safe (name withheld, fork untouched, source-canon intact), state-logically sound (reachable, no broken links, no both-ends scenes), and all declared downstream obligations (L87 fix, 021b restructure, fork untouched) are fulfilled.
- **M2: PASS** — same grounds; the debt dimension is a valid causal collision, and the Antiquarian debt is extended through the 040a leaves as different *payments*, not new debts.
- **M3: PASS** — the closest to the withheld-name canon, but all three spends (filed/named/replayed) re-describe the *existing* system-readable naming convention; the protagonist never learns the name. The 040a fork and 040f/040g cost chain are untouched/extended consistently. law_bb750d1bdb10 is extended, not violated.

**No mutation is BLOCKED.** There is no concrete contradiction, no impossible transition, and no missing causal obligation in any of M1, M2, or M3.

---

## 2. Watch items (non-blocking, for the room)

These are NOT grounds for BLOCK (dramatic preference / future-cycle concerns only), recorded for continuity:

1. **021b geography (pre-existing, not introduced by these mutations):** 021b is titled "The Walk to the Shop" and ends with a link to 022 "The Lattice" (the shop-floor lattice reveal). The Temple route's *actual* state (020 square, acolytes, open reliquary) is what 022b re-asserts. The mutations restructure 021b so the Temple state is "carried intact, not pre-spent." This is a HONE within 021b; no new file, no broken link. The room should verify the restructured 021b still lands the Temple *names* facet as a stated proposition (per M1 §obligation 1) so 022b's re-assertion has a true antecedent.
2. **022 shared-reveal singularity:** All three mutations keep the 022 reveal *singular* (no split) while forking its *interpretation*. The room must ensure the closing beat does not accidentally split into three objects (the cost clause warns of this). This is a craft/execution check, not a canon contradiction — if the implementation splits the reveal, that is a future-cycle structural defect, not a BLOCK on the declared mutation.
3. **law_4d3da1051141 status:** The mutations flag it as "superseded in spirit (branch-awareness moved upstream); Acumen Keeper may revise." It remains a *candidate* law. The mutations do not activate or contradict it; they extend it upstream. The Acumen Keeper should decide whether to revise/supersede it at the next cycle — that is a governance action, not a canon prosecution outcome.

*Prosecution complete. Three mutations, three PASS verdicts.*
