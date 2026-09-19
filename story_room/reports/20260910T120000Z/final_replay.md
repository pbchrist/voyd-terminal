# FINAL REPLAY — 20260910T120000Z (post-M3 implementation)

**Walker role:** Independent Final Replay Walker (isolated; did not write scenes, did not design M3, did not judge the mutation).
**Target:** The IMPLEMENTED (post-M3) story under `story/scenes/`.
**Test:** Walk the 8 prescribed paths. Find the earliest structural break. Decide PASS/FAIL.

**Method:** Full-text read of all 24 scenes under `story/scenes/`, plus mechanical verification:
- Outbound-link integrity across all 24 files: **26/26 links resolve** (no broken `.md` links).
- 031 L87 route-bleed: pattern `door in the room behind | same filed fragment | the filed fragment` → **0 matches in 031** (the bleed is gone from the Stray route).
- "still" chains: every remaining `still` is a single-occurrence prose usage (e.g., 040e L65/L77, 022a L31, 040f L29-31), **not** a repeated re-assertion chain. The pathologically repeated "still"-blocks that characterized the pre-M3 text are absent from the M3-relevant scenes (011, 021a/021b, 031/032, 022).
- M3's cost clause ("the spend must be irreversible, or it is a toggle") verified per scene below.

---

## VERDICT

**PASS — no structural break found.**

All eight paths walk cleanly against the implemented story. Every M3 obligation is met in the text, the 040a witness chain's causal ownership is preserved, the 031 L87 route-bleed is fixed, the "still" chains are gone, and the 022 collision presents the three spent states as irreversible. The only deviations from the M3 design document are *conservative* (narrower, not looser) — they do not break structure and they do not re-erasure the fork.

**Earliest structural break: none.**

---

## PATH WALKS

### Path 1 — CHANGED PATH (Antiquarian): 000 → 010 → 011 → 022 → 022a → 040e → 040a → [commit/refuse] → 040a-03 → let-01 → 040f → 040g

| Scene | M3 spend check | Evidence |
|---|---|---|
| 010 | Pre-spend foreshadow | L105-107: "the corridor does not file objects. It files the cats who walk it… **Whatever you choose, you are about to spend it.**" — spend is announced *before* the route, satisfying M3's "spend must be explicit." |
| 011 | **FILED spend lands** | L113: "The name under the name — the one the city has never measured… is on the stone now." L121: "The door keeps what it reads. It does not unkeep." L141: "The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays." L145: "the door keeps what it reads, and it does not unkeep." L161: "The name is filed." — **Irreversibility stated four times. Spend is explicit and irreversible.** |
| 022 | Collision | L97-107: "The lattice does not show you the three points. / It shows you the three spends. / The name is filed in P'taxx's shop. / The name is on the Temple's iron. / The name is under the stray's skin. / **You have spent your anonymity three times, and the spend is irreversible.**" — the three spent states collide as irreversible. |
| 022a | Carries spent state | L49-75: repeated "The name is filed. / The name is not on the fragment. The name is on the door. The fragment was the lever. The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays." (5×). **Deviates from M3** — see §2. |
| 040e | Route-specific action | Single exit: "Stand the copy against the seam → 040a." The copy-as-witness is constrained by the FILED spend (the copy stands between you and the seam; only the filed cat can stand it as witness). |
| 040a | Witness fork | Commit (040a-make-the-witness-work) / Refuse (040a-03). Causal ownership: the protagonist's *act* (standing the copy / refusing the flinch) causes the turn. |
| 040a-03 | Refuse leaf | L27: "the cost is the lever. The copy stays a witness… and a witness you cannot deploy is a lever you no longer have." — refuse = spend the lever, keep the WANT. Extends the Antiquarian spend. |
| let-01 | Recall | L11: "It does not file. It does not provoke. It does not wait. It *recalls*." L33: "You caused this. You held your gaze. You refused the flinch. And the ledger, denied its method, did something new to finish the record." — **Causal ownership preserved verbatim: protagonist's act (refusal) causes the recall; system's response is a new recall method.** |
| 040f | P'taxx spent | L7: "The cost is P'taxx." L19: "The ledger finished that one. The ledger finished the relationship." L27: "the cost of the refusal is the cat who stood with you while you refused." — **The Antiquarian spend (trust in P'taxx's discretion) is the resource the recall spent. M3's downstream extension is native.** |
| 040g | Frontier | L49: "the cost is the relationship that made the refusal possible." The room-that-keeps frontier is constrained by the spent P'taxx relationship and the broken bell. |

**Path 1 verdict: CLEAN.** Spend lands, collision presents irreversibility, downstream frontiers route-specific, witness chain's causal ownership preserved, P'taxx spend extends through 040f/040g.

---

### Path 2 — CHANGED PATH (Temple): 000 → 020 → 021a/021b → 022 → 022b → 040b

| Scene | M3 spend check | Evidence |
|---|---|---|
| 020 | Pre-spend foreshadow | L87-101: "The reliquary is not a box. It is a name… And the lid has been waiting for a name. And the name it is waiting for is the one the city does not know… If you go to the temple, the lid will close. And the name under the name will be on the iron. And the iron does not give it back." |
| 021a | **NAMED spend lands** | L29: "The name is on the iron." L39: "And the iron does not give it back." L59: "The name is filed in the iron." L61: "The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays." L65: "The cat who walks out is named… The cat who walks out is the one the temple holds." L71: "And what is done stays done." — **Irreversibility stated. Spend explicit.** |
| 021b | **NAMED spend lands (carried intact)** | L57: "The name is on the iron." L67: "And the iron does not give it back." L87: "The name is filed in the iron." L89: "The name is the cost. And the cost is not a thing you can walk back from." L93: "The cat who walks out is named… the one the temple holds." L99: "And what is done stays done." — **Restructured so the Temple spend is carried intact, not pre-spent (M3's 021b obligation met).** |
| 022 | Collision | (see Path 1) — three spends collide as irreversible. |
| 022b | Carries spent state | L51: "You have spent your anonymity. The name is on the iron. It cannot be unnamed. The containment the acolytes came to make is the containment you cannot refuse, because you are already the named subject, and the named subject cannot be un-named." L69: "And the spend is irreversible." — **Spend carried forward; capability spent (ability to be contained) made explicit.** |
| 040b | Route-specific action | Single exit: "Hold your gaze — the reliquary is open." L73-74: "the reliquary now bears your name and the system has widened its test to Faelspire. It is no longer testing only you." — frontier constrained by the NAMED spend (the named subject cannot be un-named; the test widens because the name is legible). |

**Path 2 verdict: CLEAN.** Spend lands in both 021a and 021b (021b carried intact, not pre-spent), collision presents irreversibility, downstream frontier route-specific.

---

### Path 3 — CHANGED PATH (Stray-open): 000 → 030 → 031 → 040c

| Scene | M3 spend check | Evidence |
|---|---|---|
| 030 | Pre-spend foreshadow | L127-141: "The cistern is not a hole. It is a name… And the lid has been waiting for a name. And the name it is waiting for is the one the city does not know… It wants to replay you… If you open the cistern, the lid will lift. And the name under the name will be under the stray's skin. And the skin does not give it back." |
| 031 | **REPLAYED spend lands** | L87: "The Voyd. The name is not new. It is the thing under the stray's skin, seen from outside… And the kit in the cistern is what the name replayed first." L89: "The name is under the stray's skin." L93: "The name is under the skin. The fragment was the lever. The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays." L97: "The cat who walks out is replayed… the one the name holds." L103: "And what is done stays done." — **Irreversibility stated. Spend explicit.** |
| 031 L87 | **Route-bleed fixed** | L87 is now "The Voyd. The name is not new. It is the thing under the stray's skin, seen from outside — the same name under the fur, the same name under the scar, the same name the city does not know." — **This is the Stray facet (replayed), NOT the Antiquarian "door in the room behind the shop / the same filed fragment" bleed.** The bleed is gone. |
| 040c | Route-specific action | Single exit: "Watch what the kit repeats." L75: "the cistern has named you and its lid can no longer close. The next move must confront the kit without letting the fragment choose your response first." — frontier constrained by the REPLAYED spend (lid jammed, name legible under skin; the kit is a proxy that can replay the protagonist's movements). |

**Path 3 verdict: CLEAN.** Spend lands, L87 route-bleed fixed (re-grounded to Stray facet), downstream frontier route-specific.

---

### Path 4 — CHANGED PATH (Stray-truth): 000 → 030 → 032 → 040d

| Scene | M3 spend check | Evidence |
|---|---|---|
| 030 | (shared with Path 3) | Pre-spend foreshadow. |
| 032 | **REPLAYED spend lands** | L61-67: "A name written beneath the skin. You lean closer. It is not his name. It is yours." L73: "The name is under the stray's skin." L77: "The name is under the skin. The fragment was the lever. The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays." L81: "The cat who walks out is replayed… the one the name holds." L87: "And what is done stays done." — **Irreversibility stated. Spend explicit. The name is the protagonist's own, under the stray's skin.** |
| 040d | Route-specific action | Single exit: "Make the fragment ask again." L41: "Under the stray's skin, your name lengthens by one letter. Then stops." L75: "your name is now legible and Faelspire has gone silent. The next move must use the dead sliver's failure before the system begins testing another cat." — frontier constrained by the REPLAYED spend (name legible under skin; the dead sliver holds an unfinished record the protagonist can leverage). |

**Path 4 verdict: CLEAN.** Spend lands on the Stray-truth sub-branch, downstream frontier route-specific. **030 cistern fork now produces distinguishable state** (031 = name replayed via the kit; 032 = name replayed via the dead sliver; different available actions at 040c vs 040d).

---

### Path 5 — NEIGHBORING PATH (030 cistern fork): 030 → 031 vs 030 → 032

**Distinguishable state: YES.**
- 031 (open cistern): the kit emerges from the impossible sky; the name is replayed *through the kit* (L87: "the kit in the cistern is what the name replayed first"); the cistern lid jams (040c L63: "The lid drops crookedly into the crack and jams. It can no longer close the cistern.").
- 032 (force the truth): the stray's scar reveals tiny letters — the protagonist's *own* name (L67: "It is not his name. It is yours."); the dead sliver is the lever (040d: "Your fragment holds a complete movement… His holds an unfinished one"); the name "lengthens by one letter" (040d L41).

**Different downstream actions:** 040c = "Watch what the kit repeats" (confront the kit, proxy replay); 040d = "Make the fragment ask again" (use the dead sliver's failure). **The fork is causal, not cosmetic.** Both spends are irreversible. **No break.**

---

### Path 6 — UNAFFECTED CONTROL PATH (040a witness chain): 040a → 040a-03 → let-01 → 040f → 040g

| Check | Result | Evidence |
|---|---|---|
| Causal ownership (protagonist's act causes the recall) | **PRESERVED VERBATIM** | let-01 L31-33: "You caused this. You held your gaze. You refused the flinch. And the ledger, denied its method, did something new to finish the record it has not finished. The reclassification is the consequence of your holding, not a gear that was always turning." |
| System's response = new recall method | **PRESERVED** | let-01 L9-11: "So the ledger does something it has not done before. It does not file. It does not provoke. It does not wait. It *recalls*." |
| 040a fork untouched | **PRESERVED** | 040a-the-witness-you-made L31-35: commit/refuse fork intact; the two leaves are different *spends* of the same Antiquarian resource (commit = spend the WANT in the ledger's currency; refuse = spend the lever, keep the WANT), not new resources. |
| 040f/040g extend the Antiquarian spend | **PRESERVED** | 040f L7: "The cost is P'taxx." L19: "The ledger finished the relationship." 040g L49: "the cost is the relationship that made the refusal possible." |

**Path 6 verdict: CLEAN.** The protected chain is untouched. Causal ownership is preserved. The Antiquarian spend extends through 040f/040g natively. **This is the strongest confirmation that M3's repair and the protected element are the same causal thread.**

---

### Path 7 — DOWNSTREAM RECONVERGENCES (022 collision)

| Check | Result | Evidence |
|---|---|---|
| 022 presents three spent states as irreversible | **YES** | 022 L97-107 (cited in Path 1). |
| 022 is a *collision*, not a *re-assertion* | **YES** | 022 L97: "The lattice does not show you the three points. / It shows you the three spends." — the node asserts *new* state (the three spends collide; "the cat who walks out is filed / named / replayed"), not old state re-read. L139-141: "The lattice is the creditor. And the lattice cannot be paid in three currencies at once." — the collision produces a *new* dramatic reality (a measured cat, no longer unmeasurable), not a re-label. |
| 022a carries the Antiquarian spent state | **YES** (see §2 deviation) | 022a L49-75. |
| 022b carries the Temple spent state | **YES** | 022b L51: "You have spent your anonymity. The name is on the iron. It cannot be unnamed… the named subject cannot be un-named." |
| "Still" chains gone | **YES** | No repeated "still"-blocks in 022/022a/022b. The only "still" in 022 is L59 ("the three suns are still shining") — a single prose usage, not a re-assertion chain. |

**Path 7 verdict: CLEAN.** The 022 collision is genuine: it presents the three spent states as irreversible, asserts new state (the collision's result), and is not a re-assertion of route objects.

---

### Path 8 — AFFECTED ENDINGS (040b/040c/040d/040e/040g frontiers)

| Frontier | Route-specific available action? | Constrained by the spend? | Evidence |
|---|---|---|---|
| 040b (Temple) | YES — "Hold your gaze — the reliquary is open" | YES — NAMED spend | L73-74: "the reliquary now bears your name and the system has widened its test to Faelspire. It is no longer testing only you." The named subject cannot be un-named; the test widens because the name is legible. |
| 040c (Stray-open) | YES — "Watch what the kit repeats" | YES — REPLAYED spend | L75: "the cistern has named you and its lid can no longer close. The next move must confront the kit without letting the fragment choose your response first." The kit is a proxy that replays the protagonist's movements. |
| 040d (Stray-truth) | YES — "Make the fragment ask again" | YES — REPLAYED spend | L75: "your name is now legible and Faelspire has gone silent. The next move must use the dead sliver's failure before the system begins testing another cat." The dead sliver holds an unfinished record the protagonist can leverage. |
| 040e (Antiquarian) | YES — "Stand the copy against the seam" | YES — FILED spend | L79-80: "the copy is a subject now, and the seam is aimed at you… the only one who can stand the copy as the ledger's witness against itself is you." The filed cat is the only one who can stand the copy as witness. |
| 040g (Antiquarian) | YES — "Enter the room that keeps" | YES — FILED + P'taxx spend | L43-44: "the room behind the room is the room where the filing happens… The next move is not an attitude. The next move is a step." The spent P'taxx relationship and the broken bell constrain the frontier. |

**Path 8 verdict: CLEAN.** All five frontiers have route-specific available actions constrained by the spend. The single-exit corridors are no longer *cosmetic* — each exit is *constrained by the spent state* (the protagonist cannot unspend). **The corridor repair is met.**

---

## DEVIATIONS FROM THE M3 DESIGN DOCUMENT (non-breaking)

These are places where the implementation is *narrower* than the M3 design document. None of them break structure; they reduce downstream differentiation but do not re-erase the fork.

### §1. 022 collision presents only TWO exits, not three

**M3 design (mutations.md L79):** "022a/022b carry *their* spent state forward so each frontier has different available actions." The design implies three downstream carriers (one per route).

**Implementation:** 022 (L149-153) presents only two exits:
- L149: "Hold your gaze — the room behind you holds the door that filed the proof → 022a" (Antiquarian)
- L152: "Hold your gaze — the iron box beside you is open → 022b" (Temple)

**There is no 022c (Stray) exit.** The Stray route (030→031/032) bypasses 022 entirely: 031 → 040c and 032 → 040d are *direct* transitions that never pass through the 022 lattice. The Stray spent state (REPLAYED) is *declared* in the 022 collision text (L105: "The name is under the stray's skin") but is *not carried forward* by a 022c scene. The Stray frontier (040c/040d) is reached *without* passing through the 022 collision.

**Impact:** The 022 collision *names* the Stray spend (the reader learns "the name is under the stray's skin") but the Stray reader *does not walk through the collision* — they walk directly to 040c/040d from 031/032. This is a *narrower* implementation than the design: the Stray spent state is *asserted* at 022 (for the Antiquarian/Temple readers who walk 022) but is *not carried forward* by a 022c for the Stray reader. The Stray frontier is still route-specific and spend-constrained (Path 3/4/8 confirm), so the *fork is not re-erased* — but the *reconvergence* is incomplete for the Stray route. The Stray route never *collides* with the other two spends; it *bypasses* the collision.

**Why it is non-breaking:** The M3 design's core claim is that "the 022 collision presents the three spent states as irreversible" — and it does (L101-107). The Stray spent state is *present* in the collision text. The missing 022c means the Stray reader does not *experience* the collision, but the Stray frontier (040c/040d) is still route-specific and spend-constrained. The *causal fork* (030 cistern fork → distinguishable state at 040c/040d) is intact (Path 5). The *reconvergence* (022) is incomplete for the Stray route, but it is not *erased* — the Stray spend is named in the collision text, and the Stray frontier is spend-constrained.

**Recommendation (non-blocking):** A future cycle could add a 022c (Stray) so the Stray route also passes through the 022 collision, completing the tripartite reconvergence. This would strengthen the M3 implementation but is not required for a PASS — the current implementation preserves the fork and presents the three spent states as irreversible.

### §2. 022a repeats the FILED block 5× (mild "still"-chain residue)

**M3 design:** "The 'still' chains die because the node now asserts *new* state (the collision's result), not old state re-read."

**Implementation:** 022a (L49-75) repeats the following block **five times**:
> "The name is filed. / The name is not on the fragment. The name is on the door. The fragment was the lever. The name is the cost. And the cost is not a thing you can walk back from. It is a thing that stays. / The name is filed in P'taxx's shop."

This is a *mild* re-assertion chain — the same 4 lines repeated 5×. It is not the *pathological* "still"-chain of the pre-M3 text (which repeated across many scenes), but it is a *residual* re-assertion within a single scene. The block does assert *irreversibility* (the cost "is not a thing you can walk back from"), so it is not a *toggle* — but the 5× repetition is *re-assertion*, not *collision*.

**Impact:** 022a's job (per M3) is to "carry the spent state forward so 040e has route-specific actions." It does that — 040e is route-specific (Path 1). But the 5× repetition is *re-assertion* of the FILED state, not a *new* assertion. This is *mildly* at odds with M3's claim that "the 'still' chains die." It does not break structure (the spend is still explicit and irreversible; the frontier is still route-specific), but it is a *residue* of the pre-M3 re-assertion pattern.

**Why it is non-breaking:** The M3 cost clause ("the spend must be irreversible") is satisfied — the FILED spend is stated as irreversible 5×. The 5× repetition is *emphasis*, not *erasure*. The 040e frontier is still route-specific. The *collision* at 022 (Path 7) is genuine. The 022a repetition is a *prose* issue (redundant emphasis), not a *structural* break.

**Recommendation (non-blocking):** A future cycle could trim 022a's 5× repetition to 1-2× and replace the surplus with a *new* assertion (e.g., the copy-as-subject, or the Lattice's fourth point) to complete the "collision, not re-assertion" repair. This is a *polish* item, not a *structural* fix.

---

## RUBRIC CROSS-CHECK (categories 26-35, interactivity)

| Category | Assessment | Evidence |
|---|---|---|
| 26. Meaningful agency | **PASS** | Each choice (000 three-way, 030 cistern fork, 040a commit/refuse) expresses a distinct intention and produces a distinct, interpretable consequence (FILED / NAMED / REPLAYED spend; different frontiers). |
| 27. Choice legibility | **PASS** | Each option's attitude/tactic/risk is legible (010 L105-107 foreshadows the spend; 020 L87-101 foreshadows the naming; 030 L127-141 foreshadows the replay). |
| 28. Consequence depth | **PASS** | Consequences operate at all four levels: (1) immediate response (022 collision), (2) later callback (040f P'taxx spent), (3) changed available strategy (route-specific frontiers), (4) changed interpretation (the measured cat). |
| 29. Branch differentiation | **PASS** | The three routes produce different *dramatic experiences* (FILED / NAMED / REPLAYED spend), not just different *objects*. The 030 cistern fork produces distinguishable state (Path 5). |
| 30. Reconvergence quality | **PASS** (see §1 deviation) | 022 carries state forward (three spent states collide as irreversible). 022a/022b carry their spent state forward. The Stray route bypasses 022 (§1) but its frontier is still spend-constrained. |
| 31. State as storytelling | **PASS** | The spent state (FILED / NAMED / REPLAYED) *embodies* the theme (the name is legible to the system, not the protagonist). The irreversible spend *is* the story's central argument. |
| 32. Failure quality | **PASS** | 040a-03 (refuse) produces a *dramatic* failure (the lever is lost; the record stands unfinished) that becomes part of the character's history (040f/040g). Not a cosmetic lockout. |
| 33. Player-character relationship | **PASS** | The player *chooses* the spend (000 three-way, 030 cistern fork, 040a commit/refuse); the character *experiences* the spend (the name is filed / named / replayed). The distance between player choice and character cost is deliberate. |
| 34. Interface-theme unity | **PASS** | The act of *choosing* (selecting a route) *is* the act of *spending* the anonymity. The interface (the fork) participates in the meaning (the spend is irreversible; the choice is the cost). |
| 35. Ending recognition | **PASS** | Each frontier (040b/040c/040d/040e/040g) reflects the player's *accumulated* pattern of action (the route chosen at 000/030, the commit/refuse at 040a), not only the final selection. |

---

## FINAL DECISION

**PASS.**

All eight paths walk cleanly against the implemented (post-M3) story. The M3 mutation is implemented:
- Each route spends a different irreversible resource (FILED / NAMED / REPLAYED), stated explicitly in the signature scene (011 / 021a+021b / 031+032).
- The 022 collision presents the three spent states as irreversible ("You have spent your anonymity three times, and the spend is irreversible" — 022 L107).
- The downstream frontiers have route-specific available actions constrained by the spend (040b/040c/040d/040e/040g).
- The 031 L87 route-bleed is fixed (re-grounded to the Stray facet).
- The "still" chains are gone (no pathological re-assertion blocks; one mild 5× repetition in 022a is a prose residue, not a structural break).
- The 040a witness chain's causal ownership is preserved verbatim (protagonist's act causes the recall; system's response is a new recall method).
- The choice still creates distinguishable state (030 cistern fork → 040c/040d different actions; 040a commit/refuse → different spends).
- The implementation expresses the selected structural species (M3 = spent resource): the spend is irreversible, the collision is a collision of spent states, and the Antiquarian spend extends natively through the protected 040f/040g chain.

**Earliest structural break: none.**

**Two non-breaking deviations** (§1: 022 presents only two exits, not three — the Stray route bypasses the collision; §2: 022a repeats the FILED block 5× — a mild re-assertion residue) are *narrower* than the M3 design but do not break structure and do not re-erasure the fork. They are candidates for a future polish cycle.
