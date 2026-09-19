# INDEPENDENT REPLAY — MUTATION M3 (SPENT RESOURCE)

**Walker:** independent replay walker (not author, not judge, not advocate)
**Cycle:** 20260910T120000Z
**Mutation under test:** M3 — each route (Antiquarian / Temple / Stray) spends a different *irreversible* resource — all three are spends of **anonymity / unmeasurability** (filed / named / replayed). The 022 reconvergence *collides* the three spent states instead of re-asserting objects; 022a/022b carry their spent state forward; the 040a witness chain is protected and the Antiquarian spend is extended downstream (P'taxx lost as the recall's cost in 040f/040g).
**Standard applied:** the mutation's own cost clause — *"The spend must be irreversible (if undoable, it is a toggle, not a spend). The reconvergence must present the spent states as irreversible; if merely different, the collision is weak."* A spend that is merely different (not irreversible) is a structural failure.

**Method:** cold walk of the seven required paths against the *post-M3* state. All scene reads are full; evidence cited as scene + line.

**Baseline facts the walks depend on (verified):**
- Graph: `000` 3-way fork → {010→011 | 020→021a/021b | 030→031/032} → `022` (2-way: 022a/022b) → {022a→040e→040a→{make | 040a-03→let-01→040f→040g} | 022b→040b} and {031→040c, 032→040d}. Every choice link resolves to an existing file (Steward §0e, re-verified by reading all 24 scenes).
- Active law being repaired: `law_a509c75fb6a1` — "within reach of every frontier there must be a choice between two actions under pressure whose consequences differ in what the protagonist **knows, owes, or has spent**."
- Protected chain (not tested as a change target): 040a (commit/refuse) → 040a-03 → 040a-let-01 → 040f → 040g.
- 031 L87 verbatim: "The Voyd. The name is not new. It is the door in the room behind the shop, seen from inside — the same ledger of looking-aways, **the same filed fragment**, the same countdown." (Antiquarian state bleeding into the Stray route.)

---

## PATH 1 — CHANGED PATH (Antiquarian)
`000 → 010 → 011 → 022 → 022a → 040e → 040a → [commit/refuse] → 040a-03 → let-01 → 040f → 040g`

**Does the "filed" spend land as an explicit irreversible cost in 011?**
Partially. 011 lands the *object* of the spend explicitly: the fragment slides into the high door's light, "The light closes. The fragment is gone." (L97-101), the title shifts to **FILED** ("'Filed,' he says. 'The door keeps what it reads.'", L105), and the new line reads **YOU LOOKED AWAY** (L123-125). But the *spend* M3 names — the protagonist's **anonymity** filed, **cannot be unfiled**, and the **relationship spent: trust in P'taxx's discretion** — is not stated as a cost in 011. What 011 actually costs is the *proof* (the fragment leaves the protagonist's possession), not the protagonist's unmeasurability. The "filed" that matters to M3 (the *name* filed) only appears downstream in 040f/040g ("The name is still filed", 040a-03 L35; 040f L31; 040g L31) — i.e., the spend is **landed late**, at the cost-of-holding scene, not at the signature scene (011) where M3's obligation (1) requires it.

**Does 022 collide the three spent states (not re-assert objects)?**
No — as written, 022 does not. 022 is the *shared* lattice reveal and its two exit links are object-re-assertions: "the room behind you holds the door that **filed the proof**" → 022a; "the iron box beside you is open" → 022b (L99-103). The collision M3 declares ("the name is filed in P'taxx's shop / on the Temple's iron / under the stray's skin — you have spent your anonymity three times, and the spend is irreversible") is **not present** in 022's text. M3's declared edit ("022 closing presents the three spent states as irreversible") is an *intent*, and 022 currently re-asserts two route objects, not three spent states.

**Do the downstream frontiers have route-specific actions constrained by the spend?**
No. 040e has one exit (→ 040a) whose blurb is an is-chain restatement, not a spend-constrained action. 040a is a genuine two-action fork (commit/refuse), but M3 re-describes those two leaves as "different spends of the same resource" (commit spends the WANT; refuse spends the lever) — a re-label of the *existing* fork, not new route-specific actions. The frontier at 040g is single-exit (ACTIVE FRONTIER, no `## Choose`). The Antiquarian spend therefore does not visibly *constrain* a distinct set of downstream options; it is carried as residue, not as a constraint on available actions.

**PATH 1 — EARLIEST FAILURE:** the "filed" spend is not landed as an explicit irreversible cost in the signature scene 011 (it lands in 040f instead); 022 does not collide three spent states (re-asserts two objects).
**EVIDENCE:** 011 L97-125 (object filed, spend not stated); 022 L99-103 (two object re-assertions, no spend collision); 040f/040g L31 ("The name is still filed" — spend lands here, late).
**SEVERITY:** prose defect (declared intent not present in text; no broken link, no impossible transition, no canon break).

---

## PATH 2 — CHANGED PATH (Temple)
`000 → 020 → 021b (or 021a) → 022 → 022b → 040b`

**Does the "named" spend land as an explicit irreversible cost?**
Partially, and with a continuity break. 022b does land the named state: "The name burns across the lid… **Your name.**" (L31-35) — the reliquary naming the protagonist, which is exactly M3's "named" spend and is irreversible (a name on the iron lid cannot be unnamed). BUT 022b opens with a **continuity contradiction**: "They do not look as though they were in the square when the bell first rang. They look as though they have been waiting for it in the dark of the shop and it finally came" (L7) — when the acolytes *were* in the square in 020. This is the same break present in 021a L21. Additionally, the "named" spend's stated collateral — **capability spent: ability to be contained** — is not landed; the containment doctrine is never resolved (the reliquary *recognized* the fragment, it did not contain anything), so that half of the spend is declared but unlanded.

**Does 022b carry the Temple spent state forward?**
Yes, in part — the name-bearing reliquary is carried to 040b ("the reliquary now bears your name", 040b L73). But 021b (the walk-to-the-shop) **pre-spent** the Temple branch's distinctive state: it is a five-line teleport to P'taxx's shop where "You sent him to me" is never resolved (021b L23-25, flagged by cold walk2 as its first_failure). So by the time 022b re-asserts the name, the Temple branch's *causal history* (the reliquary's recognition as the Temple's containment act) was already partially consumed in 021b. 022b's "You have another fragment" (L45) is a turn the route never set up.

**PATH 2 — EARLIEST FAILURE:** 022b L7 continuity break (acolytes "not in the square" when they were in 020) — and, structurally, 021b pre-spent the Temple state before 022b re-asserts it.
**EVIDENCE:** 022b L7 vs 020 (acolytes in the square); 021b L23-25 (unresolved "You sent him to me", teleport); 022b L45 ("You have another fragment" — no setup).
**SEVERITY:** prose defect / continuity break (pre-existing, not introduced by M3's declared edits; M3 does not worsen it, and its 021b restructure is declared but not yet in the text).

---

## PATH 3 — CHANGED PATH (Stray)
`000 → 030 → 031/032 → 040c/040d`

**Does the "replayed" spend land as an explicit irreversible cost?**
Yes, on both sub-branches, and this is the strongest of the three spends.
- 031 (open cistern): the kit is "what the Voyd learned to wear after he ran" (L85); the cistern names the protagonist — the kit's paw closes the rim, "The stone splits under its claws. The lid drops crookedly into the crack and jams. **It can no longer close the cistern.**" (040c L61-63). The name is legible (040c L55-57). Irreversible: the lid cannot be un-jammed.
- 032 (force explanation): "A name written beneath the skin… **It is yours.**" (L57-67); "Under the stray's skin, your name **lengthens by one letter**." (040d L41); the projection "speaks your name in your own voice" (040d L61). Irreversible: the name cannot be unreplayed; the city now knows (040d L69 "They know which cat to ask next").
The relationship spent (trust in the stray's silence) is implicitly landed — the stray's silence is broken by the cistern speaking in both their voices.

**Does the 031 L87 route-bleed get fixed?**
**No — not in the current text.** 031 L87 still reads verbatim: "It is the door in the room behind the shop, seen from inside — the same ledger of looking-aways, **the same filed fragment**, the same countdown." This is Antiquarian-route state (the room behind the shop, the high door, the filed fragment) bleeding into the Stray route, which has never been to the shop or seen a filed fragment. M3's obligation (4) declares this fixed ("the Antiquarian spend is re-grounded to the Stray replayed spend"), but the text has not been edited. This is the **loudest** route-bleed in the corpus and the **first_failure of cold walk3** — a first-time-player contract break at the exact moment of the Stray route's peak reveal.

**PATH 3 — EARLIEST FAILURE:** 031 L87 route-bleed (Antiquarian "filed fragment / room behind the shop" state leaking into the Stray route) — declared fixed by M3 but **not present in the text**.
**EVIDENCE:** 031 L87 verbatim; cold walk3 `confused` + `_annex` first_failure.
**SEVERITY:** **structural break** (route-state bleed violates the first-time-player causal contract and the branch-awareness law; it is a declared-but-unimplemented fix).

---

## PATH 4 — NEIGHBORING PATH (030 cistern fork under M3)
`030: "open cistern" (→031) vs "force explanation" (→032)`

**Does the choice now produce different downstream *physical* state (not just different backstory knowledge)?**
**No.** Both branches converge on **identical downstream physical state**:
- 040c (from 031, open cistern): lid jammed open, kit at the rim, name legible, city silent.
- 040d (from 032, force explanation): name lengthens under the stray's skin, city silent, dead sliver dead.
The only difference carried is *backstory knowledge* (twelve-years courier story in 032 vs. kit-reveal in 031). 032 even *opens* with the open-cistern beat — "'Three breaths,' you say. 'Then I open the cistern.'" (L3) — the story *telling the player the branches will merge*. The downstream physical state (lid jammed, name legible, city silent) is the same either way. This is the **exact** failure the Governing Judge diagnosed: "The 030 cistern fork must produce different downstream physical state, not different backstory knowledge… one branch jams the lid, the other does not; one branch makes the name legible, the other does not." M3's declared 030 fork re-tasking ("the name is legible under the stray's skin" as the replayed spend) is **informational, not causal** — both branches land the same physical state.

**PATH 4 — EARLIEST FAILURE:** the cistern fork's branches converge on identical downstream physical state; the choice differs only in backstory knowledge. The 030 fork remains a flavor toggle, not a causal fork.
**EVIDENCE:** 032 L3 ("Then I open the cistern" — the branch announces its own merge); 040c L61-63 vs 040d L41/69 (same lid-jammed / name-legible / city-silent state).
**SEVERITY:** **structural break** (the fork's consequence is informational-only; a scene in the middle of the branch (032's backstory) can be removed without changing later behavior — the rubric's exact failure sign; direct violation of active law `law_a509c75fb6a1`).

---

## PATH 5 — UNAFFECTED CONTROL PATH (040a witness chain)
`040a → 040a-03 → let-01 → 040f → 040g`

**Confirm M3 does not change this chain's causal ownership.**
**Confirmed — the chain is intact and untouched.**
- 040a: two genuinely distinct actions under pressure (commit / refuse), pre-declared act deleted (performed agency). M3 re-describes the leaves as "different spends of the same resource" — a re-label, not a re-assignment of causality.
- 040a-03: the *protagonist's performed act* (physically NOT crossing) is the cause; the cost is the lever ("a witness you cannot deploy is a lever you no longer have", L27).
- 040a-let-01: "**You caused this.** You held your gaze. You refused the flinch. And the ledger, denied its method, did something new… The reclassification is the consequence of your holding, not a gear that was always turning." (L31-33). The system's response is a **NEW method** — recall — "It does not file. It does not provoke. It does not wait. It *recalls*." (L11). This satisfies candidate law `law_bb750d1bdb10` exactly.
- 040f: the recall's route-specific cost lands — **P'taxx** becomes a subject ("The ledger finished the relationship", L19).
- 040g: canonical head, ACTIVE FRONTIER.
M3 does not re-assign who causes the turn, does not revert the test to "will you flinch," and does not make the system deliver the decisive move. **Causal ownership preserved verbatim.**

**Is the Antiquarian spend (P'taxx lost) consistently extended through 040f/040g?**
**Yes.** 040f L15-19: "the recall pulled all of it back… the recall made all of it a subject. … The ledger finished the relationship." 040g L47-49: P'taxx "at the desk, face on the stone… the cost is the relationship that made the refusal possible." This is exactly M3's declared downstream extension: "the 040f/040g chain (P'taxx lost as a cost) is the downstream extension of the Antiquarian spend… the P'taxx relationship is the resource the recall spent." The spend structure flows forward consistently. (Minor prose note: 040f L15 says "the recall reached back through the keeping" while 040a-let-01 L13 says the ledger "has not spent anything before" — the *cost* is the relationship, not the ring; consistent, no break.)

**PATH 5 — EARLIEST FAILURE:** NONE.
**EVIDENCE:** 040a-let-01 L31-33 (protagonist causes recall); 040f L15-19, 040g L47-49 (P'taxx spend extended).
**SEVERITY:** none.

---

## PATH 6 — DOWNSTREAM RECONVERGENCES
**At 022, do the three spent states produce a genuine NEW state (a turn), not a re-read?**
**No — not as the text stands.** 022's turn is the shared lattice reveal (the fourth point above the palace, "It measures looking away / It has no word for looking back", L63-79) — a *system* reveal, not a collision of three route-carried spent states. The two exit links re-assert route objects (filed door / open reliquary, L99-103). The M3-declared collision ("you have spent your anonymity three times, and the spend is irreversible") is **absent** from 022. So the reconvergence, as written, still *re-asserts* (movement 1 repeated) rather than *collides* (movements 2+3).

**Do the "still" chains (022a/022b/040e/040g) disappear because the node now has new state to assert?**
**No.** The "still" chains are present and are the consensus attention-kill across all four cold walks:
- 022a L43-47: "The high door is still open. The filed frame is still laid across the stone. The line beneath FILED is still being carved… The seam is still aiming. The line is still being carved. The subject is still the copy.…"
- 022b L51-67: 8-clause is-chain ("The reliquary is still open. The name is still burning. The seam is still matching…").
- 040e L57-87: "the filed frame is still laid across the stone, and the line beneath FILED is still being carved, and the copy is still standing between you and the seam."
- 040g L51/55/63: "The sheet on the desk is open… the bell is broken… the room is the method, and the method is the keeping…"
These chains exist *because* the reconvergence has no new state to collide — the branch difference was not carried as irreversible spend into the node. M3's declared fix ("The 'still' chains die because the node asserts new state (what the protagonist has lost)") is **not realized in the text**; the chains persist.

**PATH 6 — EARLIEST FAILURE:** 022 re-asserts route objects (two exit links) instead of colliding three spent states; the "still" chains persist at 022a/022b/040e/040g.
**EVIDENCE:** 022 L99-103; 022a L43-47; 022b L51-67; 040e L57-87; 040g L51/55/63.
**SEVERITY:** prose defect (the collision intent is declared but the node's text still re-asserts; the "still" chains are a symptom of the un-implemented collision).

---

## PATH 7 — AFFECTED ENDINGS (040b/040c/040d/040e/040g frontiers)
**Do they now have route-specific available actions (constrained by the spend), or are they still single-exit corridors?**
**They are still single-exit corridors.**
- 040b (Temple): `## ◉ ACTIVE FRONTIER` — no `## Choose` block. Single "next move." The "named" spend (reliquary bears the name) does not produce a distinct set of available actions; the frontier is a corridor.
- 040c (Stray-open): `## ◉ ACTIVE FRONTIER` — single-exit. The "replayed" spend (lid jammed, name legible) does not open a route-specific fork.
- 040d (Stray-truth): `## ◉ ACTIVE FRONTIER` — single-exit. Same downstream physical state as 040c (see Path 4).
- 040e (Antiquarian, pre-040a): one exit (→ 040a) with an is-chain blurb.
- 040g (Antiquarian canonical head): `## ◉ ACTIVE FRONTIER` — single-exit, the canonical head.
M3's declared effect ("the spend *constrains* the options — the protagonist cannot unspend") is **not realized**: none of the five frontiers has a spend-constrained, route-specific set of available actions. The single-exit corridors persist on 040b/040c/040d (the Temple and both Stray routes), which is the direct violation of active law `law_a509c75fb6a1` that M3 is supposed to repair. The only genuine fork (040a commit/refuse) is route-gated behind the Antiquarian route and is re-labeled, not opened, by M3.

**PATH 7 — EARLIEST FAILURE:** the affected frontiers remain single-exit corridors; no route-specific spend-constrained actions are present.
**EVIDENCE:** 040b/040c/040d/040g `## ◉ ACTIVE FRONTIER` with no `## Choose`; 040e single link.
**SEVERITY:** **structural break** (the corridors' existence is the direct failure sign of the active law `law_a509c75fb6a1` M3 is declared to repair; "the corridors exist because the branches converged to the same state, leaving only one possible next move" — Governing Judge).

---

# OVERALL VERDICT

## M3 FAILS (demonstrated structural breaks)

M3's *diagnosis* is sound and its *cost clause* is well-formed (irreversibility is the right discriminator; the three spends are genuinely irreversible where they land). But M3 is a **declared-intent mutation whose declared fixes are not present in the scene text**, and the paths it is supposed to repair still exhibit the exact structural failures it targets. As a cold player walking the post-M3 state, the earliest structural breaks are:

### THE EARLIEST FAILURE (earliest on the page, highest leverage)
**The 030 cistern fork remains a flavor toggle, not a causal fork (Path 4).** Both branches (open cistern / force explanation) converge on *identical* downstream physical state (lid jammed, name legible, city silent); the only difference carried is backstory knowledge. 032 opens with "'Three breaths,' you say. 'Then I open the cistern.'" — the story announcing its own merge. This is the rubric's exact failure sign (a middle branch scene removable without changing later behavior) and the direct violation of active law `law_a509c75fb6a1`. It is the earliest *demonstrated* structural break because it is a fork (a causal mechanism), not a line of prose.

### Other demonstrated structural breaks (in order of leverage)
1. **Affected frontiers are still single-exit corridors (Path 7).** 040b/040c/040d have no `## Choose` block; no route-specific spend-constrained actions. M3's declared repair of `law_a509c75fb6a1` is not realized.
2. **031 L87 route-bleed is declared fixed but not fixed (Path 3).** "the same filed fragment / the door in the room behind the shop" still leaks Antiquarian state into the Stray route — a first-time-player contract break at the Stray route's peak reveal.
3. **022 does not collide three spent states; it re-asserts two objects (Paths 1 & 6).** The M3-declared collision ("you have spent your anonymity three times, and the spend is irreversible") is absent; the "still" chains persist at 022a/022b/040e/040g.
4. **The "filed" spend is landed late (Path 1).** 011 files the *fragment* (object), not the protagonist's *anonymity*; the name-filed spend only lands in 040f/040g, not at the signature scene M3's obligation (1) requires.
5. **Temple "named" spend has a continuity break (Path 2).** 022b L7 contradicts 020 (acolytes "not in the square" when they were), and 021b pre-spent the Temple state before 022b re-asserts it.

### WHY (one paragraph)
M3 is structurally *diagnosed* correctly — it identifies the right root cause (branches delivering the same reveal) and the right repair dimension (branch consequence via irreversible spent resource) — and its cost clause (irreversibility) is the right discriminator. But a mutation is only as sound as the state it produces, and M3's declared edits ("011/021a/031/032 spend their resource as an explicit irreversible cost", "022 closing presents the three spent states as irreversible", "022a/022b carry their spent state forward so 040b/040e/040c/040d have route-specific actions", "031 L87 fixed") are **not present in the scene text**. The scene files still (a) converge the cistern fork on identical physical state, (b) leave the 040b/040c/040d frontiers as single-exit corridors, (c) still bleed Antiquarian state at 031 L87, and (d) still re-assert objects (with "still" chains) at 022/022a/022b rather than colliding spent states. The one thing M3 gets right — the Antiquarian spend extended through the protected 040f/040g chain (P'taxx lost as the recall's cost) — is consistent, and the 040a witness chain's causal ownership is preserved verbatim. But the protected-chain success does not cure the four demonstrated breaks on the changed and neighboring paths. Per the replay standard, a spend that is merely "different" (the cistern fork's branches differ only in backstory knowledge, not in irreversible physical state) is a structural failure; and the mutation's own cost clause requires the reconvergence to present the spent states as irreversible, which the current 022 text does not do. **M3 FAILS.** The mutation is not eliminated by the Steward's PASS (which is canon-safe: no name reveal, no broken link, no canon break) — it is eliminated by the *independent replay* finding that the declared structural repairs are not realized in the produced state.

---
*Walker notes: I did not average scores. The Steward's canon-safety PASS and the architecture/interactive judges' praise of the Antiquarian chain are consistent with my Path 5 (control path holds). My FAIL rests on the changed-path and neighboring-path breaks (Paths 1, 3, 4, 6, 7), which the canon prosecution does not test. The 040a witness chain (protected) is confirmed untouched — M3 does not touch it, and that is correct.*
