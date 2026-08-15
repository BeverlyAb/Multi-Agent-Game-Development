# Design Review Board — Moderator Synthesis

Document reviewed: `gdd.txt` (GDD Draft #11)
Date: 2026-08-15
Method: six isolated reviewer contexts · parallel Round 1 · cross-examination Round 2 · moderated synthesis

Board tally: 30 Round 1 findings (six reviewers × five). After cross-examination,
final severities: **10 BLOCKING / 16 MAJOR / 4 MINOR** (finding-level; the chain
softlock is one merged board issue across SD-2 + AQA-1 + F-03, and PP-1 was upgraded
to effectively BLOCKING). **3 unresolved disagreements** escalated to the design owner.

---

## TOP 5 ISSUES

### 1 — BLOCKING — Chain-reaction tasks are a permanent, unretirable softlock
**Problem.** The Goose Solution Planner certifies solvability but is forbidden to
plan chain reactions; the Chain Reaction Agent certifies nothing; and an un-fired
chain step is invisible to the retirement detector (residents and items are present,
they just never act). A chain task whose goal needs a resident-authored
`chain_effect` is neither planner-verifiable, nor Director-pollable, nor retirable —
and the consumed pairing can never regenerate.
**Flagged by:** Systems Designer (SD-2), Adversarial QA (AQA-1), Feasibility Lead
(F-03).
**Cross-examination:** STRENGTHENED. SD-2 and F-03 were upgraded MAJOR → BLOCKING
and merged with AQA-1 into one board BLOCKING. AQA-1's root-cause diagnosis (no
guarantee the state being checked is ever reachable) was held against F-03's
symptom-level poll-trigger fix.

### 2 — BLOCKING — The completion gate and ending are incoherent: harmony is either unearned (retirement counts) or unreachable (retirement cannot fire)
**Problem.** The ending is reached "whether by resolution or by outright retirement,"
but a retired task is, by the pitch's own definition, a thread that stayed open —
so the harmony beat can play over the pitch's definition of *not* harmony (NC-01).
Conversely, the only defined retirement trigger is bug-classified and never fires in
intended play, so a genuinely stuck player has no skip, no hint sufficiency, and no
exit from the 100%-completion gate (SD-1). The player either gets silent retirement
with no accounting (PP-1) or a permanent wall.
**Flagged by:** Narrative Critic (NC-01, BLOCKING), Systems Designer (SD-1,
BLOCKING), Player Psychologist (PP-1, MAJOR → effectively BLOCKING), Business
Analyst (BA-F4, MINOR → MAJOR).
**Cross-examination:** STRENGTHENED. Five reviewers converge on one unresolved model
choice; PP-1 was upgraded on NC-01's promise-breaker argument; BA-F4 was upgraded
because the same root breaks two promises at the climax.

### 3 — BLOCKING — "Everything past week 3 is additive, not load-bearing" is false; the pitched game is validated by a slice that is not it
**Problem.** The systems deferred past the week-3 checkpoint — chain reactions, item
reset/loss recovery, the Newscaster reward loop, the full-cast ending, real-latency
async — are the ones the pitch names as its differentiation, and the FPS validates
2 residents, 1 building, 1 task. The checkpoint can pass while the differentiating
promise is missing, and the real failure is discoverable only in week 12. The stated
descope contingency would cancel the game's own completion structure.
**Flagged by:** Feasibility Lead (F-01, BLOCKING), Business Analyst (BA-F3, MAJOR →
BLOCKING).
**Cross-examination:** STRENGTHENED. BA-F3 was upgraded to BLOCKING read jointly with
F-01 as a pitch-integrity defect plus a schedule-integrity defect. F-01's evidence
was re-anchored onto the reset rule, hint sufficiency, and the chain/latency/ending
systems.

### 4 — BLOCKING — The physical-comedy core has no committed technology substrate
**Problem.** The core loop and goal-state system are built on physical-comedy
emergence (gates, hoses, puddles, wet targets, moved objects) and the document names
two 3D physics parents, yet it commits to no engine, no 2D/3D decision, no physics
approach, no rendering stack, and no save-state model. Weeks 1–12 and the "reused
unchanged" schedule basis are uncheckable without a substrate.
**Flagged by:** Feasibility Lead (F-02, MAJOR → BLOCKING).
**Cross-examination:** STRENGTHENED. Upgraded to BLOCKING because colleague findings
(NC-05 staging, SD-3 reset movement, BA-F1 market tier) all terminate in the
uncommitted substrate; each finding makes the others more severe.

### 5 — BLOCKING — The pitch borrows two audience hooks the design strips, then asserts a crossover nobody can identify
**Problem.** The audience is "the crossover audience of Tomodachi Life and Untitled
Goose Game players," but the design removes the hook of each: the goose "is not
mischief for its own sake," and the player "never directly controls a resident," with
no economy or customization. The crossover is asserted, not argued or quantified,
against a crowded 2026 cozy/life-sim market.
**Flagged by:** Business Analyst (BA-F1, BLOCKING).
**Cross-examination:** STRENGTHENED (argument refined). NC-05 forced a correction:
the mischief *verbs* are retained — honk, grab, drag, drop, hide, spray — only the
*justification* is stripped, so the honest positioning ("cozy-coded goose chaos")
sits closer to Untitled Goose Game-lite and the crossover claim must be argued
against the shipping mechanics, not the label.

---

## UNRESOLVED DISAGREEMENTS

### D1 — The retirement model: a designed path or a bug-only pathology?
**Position A (Systems Designer SD-1):** the only defined trigger is
agent-detected unsolvability, classified as "a genuine authoring or state-tracking
bug, not intended play," so retirement can never fire in intended play and the
reachability claim collapses; a player-initiated retire/skip path is required.
**Position B (Player Psychologist PP-1 / Business Analyst BA):** the GDD carries a
second, routine model — the Draft #10 note ("so retirement counting toward
completion never reads as an unearned success") and the ending's mandatory
open-thread recounting only have meaning if retirement is a normal event; silent
retirement is then a guaranteed, repeated player experience.
**Escalation:** the design owner must decide whether retirement is a designed
player-facing path or an authoring-bug valve. The choice determines five findings
across four reviewers (NC-01, PP-1, BA-F4, SD-1, AQA-2).

### D2 — What the ending honors: effort or connection?
**Position A (Systems Designer SD-1, remedy):** a player-initiated skip preserves
reachability and can be narrated honestly; the reachability promise must win over the
no-failure branding.
**Position B (Narrative Critic NC-01):** adopting that remedy *widens* the
unearned-harmony problem from bug-gated to routine; it must be paired with a
connection-gated completion ("no open threads") or a rewritten harmony sentence, and
the connection gate re-opens the reachability hole it closes.
**Escalation:** the completion-gate semantics — what state actually triggers the
harmony beat — must be defined against one of these, not both.

### D3 — Payoff integrity versus the open-endedness the difficulty curve depends on
**Position A (Player Psychologist PP-3):** the authored payoff must be gated to the
validated, planned solution path, or the reconciliation line can narrate closure the
player's actions never earned (a hose "mending" a memento-driven friendship).
**Position B (Systems Designer, conflict 3):** gating to the planned path shrinks the
effective solution space to the planner's canonical route — exactly the breadth the
flat-difficulty claim depends on — and reintroduces the state-machine outcome; the
correct resolution is payoff keyed to *outcome state* plus an enumerated, budgeted
per-state authoring surface.
**Escalation:** the document must either curtail the open-endedness claim or commit
to the per-state authoring budget; PP-3's fix must not be adopted as a substitute
for the romance-payoff design NC-02 demands.

---

## QUICK WINS

1. **State a target playthrough figure** (hours per run, minutes per session). BA-F2
   flags the omission; Feasibility F-04 cannot compute a per-session API budget
   without it and Systems Designer SD-4 cannot claim pacing structure without per-set
   time. One number unblocks three findings across three reviewers.
2. **Define the item-reset rule** — what "outside of active use" means, how long "a
   short time" is, and a pause during an active plan. This closes AQA-4/SD-3 and
   removes a major source of the unexplained task disappearances PP-1 calls a bug.
3. **Define "island-wide story moments" or drop the phrase**, and give romance a
   culminating state. PP-4 (MINOR) and NC-02 (MAJOR) can be satisfied by one
   commitment: define the moments and include at least one romance-resolving beat
   among them.

---

## ONE PARAGRAPH VERDICT

This document is not ready to drive production. Its engine-level architecture is
well-developed, but the two most load-bearing guarantees — "no softlock" and "a
reachable, finite stopping point" — fail inside the systems the document itself adds
to defend them: the Chain Reaction Agent produces goals no agent can verify or
retire (Issue 1), and the completion gate makes the harmony ending either unearned or
unreachable (Issue 2), while the schedule validates a slice that is not the pitched
game (Issue 3), the physical-comedy core has no committed technology (Issue 4), and
the audience contract is asserted against hooks the design strips (Issue 5). The
single change that matters most is the one the board converges on from both
directions: **resolve the retirement/completion model** — decide whether the ending
honors effort or connection, then make the gate, the retirement trigger, the
player-facing accounting, and the epilogue consistent with that choice, and give the
solvability authority (the Goose Solution Planner) the means to verify
chain_effect-reachable goals or de-scope the chain promise. Until those two
decisions are made and the schedule checkpoint exercises them, the week-3 slice will
certify a game that does not yet exist.
