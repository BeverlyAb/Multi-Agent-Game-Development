# DESIGN REVIEW BOARD — SYNTHESIS

**Document:** Gachō Badi GDD Draft #11 (gdd.txt)
**Date:** 2026-08-17
**Reviewers:** Systems Designer, Narrative Critic, Player Psychologist, Feasibility Lead, Adversarial QA, Business Analyst

---

## 1. TOP 5 ISSUES

### #1 — Task count math is incoherent with the pair-consumption model
**Severity:** BLOCKING · **Confidence:** High · **Cross-exam outcome:** STRENGTHENED

The document claims "roughly 30-40 one-time tasks" but the consumption rule ("each resident/resident pair's task once") caps two-resident tasks at 15 with 6 residents. Three-resident tasks are even more pair-expensive. Every downstream calculation — the 75% set threshold, the true-ending tally, the executive summary scope claim — inherits this error.

**Flagged by:** Adversarial QA (Finding 1). **Connected by:** Systems Designer (cross-exam: smaller pool makes retirement more damaging), Narrative Critic (cross-exam: pair-consumption means zero room for accumulative relationship-building), Business Analyst (cross-exam: developer may plan for 30-40 and discover 15 at week 6). **Survived cross-examination:** Strengthened — the error is structural, not cosmetic, and changes the denominator of every pacing calculation.

**Recommendation:** Explicitly state that multi-resident tasks read pairwise records without consuming them (the most likely intended design), add that exception to the consumption rule, and verify the 30-40 ceiling is reachable under the clarified model. If not, revise all downstream math.

---

### #2 — The retirement subsystem is unconstrained and contradictory
**Severity:** BLOCKING · **Confidence:** High · **Cross-exam outcome:** STRENGTHENED

Retirement is simultaneously too easy to trigger (planner can retire tasks the player never attempted), unconstrained in volume (no cap on how many tasks retire per set), narratively flat (retired tasks get footnotes, not emotional beats), and contradictory with the "no failure state" claim. Cross-examination revealed this touches nearly every reviewer's concerns: it collapses pacing (Systems Designer), bypasses player agency (Adversarial QA), produces anticlimactic narrative beats (Narrative Critic), and confuses the player (Player Psychologist).

**Flagged by:** Systems Designer (Finding 1: clustering), Adversarial QA (Finding 5: preemptive retirement, Finding 7: no-failure contradiction), Narrative Critic (Finding 3: emotionally flat), Player Psychologist (Finding 5: frustrating, Finding 8: contradicts no-failure claim). **Survived cross-examination:** Strengthened — the two-part fix (cap retirements per set AND require player attempt before retirement) is now a consensus across four reviewers.

**Recommendation:** (1) Cap retirement at ~25% per set. (2) Require the planner to retire only after the player has attempted a task and the attempt has demonstrably failed. (3) Treat retirement as a narrative event with Writer Agent treatment. (4) Reframe "no failure state" as "no blocking failure."

---

### #3 — Backstory generation failure creates an unrecoverable softlock
**Severity:** BLOCKING · **Confidence:** High · **Cross-exam outcome:** STRENGTHENED

If the Relationship Agent permanently fails to attach a backstory after retries are exhausted, the task never counts toward any threshold. The game can never reach its ending. No amount of placeholder polish fixes a threshold that can never be reached.

**Flagged by:** Adversarial QA (Finding 2). **Connected by:** Narrative Critic (cross-exam: same vulnerability at catastrophic severity), Systems Designer (cross-exam: compounds with retirement clustering — two different "not counted" states can trap the player). **Survived cross-examination:** Strengthened — the recommended fix (hard fallback: retire after N retries, count toward thresholds) is now consensus.

**Recommendation:** Add: "If backstory generation fails after 2 retries, the task is automatically retired — it counts toward the 75% threshold and the true-ending tally, and the ending narrates it as an open thread." No task may exist in a state where it is neither resolved nor retired.

---

### #4 — No tiered definition of done; schedule is fiction beyond week 3
**Severity:** BLOCKING · **Confidence:** High · **Cross-exam outcome:** STRENGTHENED

The GDD describes a complete game with ~40 tasks, 13 agents, and a closing sequence, but never defines what minimum viable product looks like. The 12-week schedule acknowledges its own estimates are "rough, unvalidated" but still presents weeks 4-12 as a plan. Content authoring, token validation, and agent integration are all underestimated.

**Flagged by:** Business Analyst (Finding 4: schedule fiction, Finding 7: no done definition). **Connected by:** Feasibility Lead (cross-exam: timeline has hidden scope from onboarding + hint system + content authoring), Player Psychologist (cross-exam: onboarding is an authoring task the schedule underestimates). **Survived cross-examination:** Strengthened — the lack of MVP tiers means the developer won't know what to ship if time runs out.

**Recommendation:** Add a "Minimum Shippable Product" section defining three tiers: MVP (core loop, 3 residents, one task set), acceptable (full cast, one complete set, closing sequence draft), full (all ~30-40 tasks, full closing sequence). Explicitly state that weeks 4-12 are hypotheses, not commitments, to be re-estimated after week 3 ships.

---

### #5 — The pitch promises Tomodachi Life depth without mechanical support
**Severity:** BLOCKING · **Confidence:** Medium · **Cross-exam outcome:** STRENGTHENED

The "Tomodachi Life meets Untitled Goose Game" pitch promises emotional depth, emergent relationship drama, and characters who develop independently of the player. Every system described serves the Untitled Goose Game side (puzzle mechanics). There is no ambient community life, no goose character arc, no emotional escalation in writing or staging, and the pitch comparison creates commitments the architecture cannot fulfill.

**Flagged by:** Narrative Critic (Finding 1). **Connected by:** Systems Designer (cross-exam: the underspecified relationship state machine is the structural cause of flat emotional arc), Player Psychologist (cross-exam: UGG pitch comparison sets wrong expectations), Business Analyst (cross-exam: pitch overpromise is a symptom of no tiered done definition). **Survived cross-examination:** Strengthened — the pair-consumption model (Adversarial QA Finding 1) makes this worse: with only 15 tasks, each pair gets exactly one moment, with zero room for accumulative relationship-building.

**Recommendation:** Either expand the design to include lightweight ambient inter-task behavior (residents reacting to their own history without the goose's involvement) — or honestly revise the pitch to "Untitled Goose Game with authored relationship payoffs" and drop the Tomodachi Life comparison. At minimum, give the goose a present narrative thread and vary the Writer Agent's emotional register across task sets.

---

## 2. UNRESOLVED DISAGREEMENTS

### Disagreement 1: Onboarding severity — BLOCKING or MAJOR?

**Position A (Player Psychologist):** The absence of onboarding for the indirect-puzzle loop is BLOCKING. Without teaching the "orchestrate, don't confront" mental model, the game's core loop never clicks, and nothing else in the GDD rescues the experience. The onboarding gap is the gatekeeper that determines whether the player ever reaches the emotional payoffs the game promises.

**Position B (Adversarial QA + Business Analyst):** Onboarding is MAJOR at highest. It is a polish problem fixable in a week of authoring once the core loop works. BLOCKING should be reserved for issues that make the game structurally unviable (task count math, backstory softlock). A game with no onboarding but a working core loop can be fixed; a game with beautiful onboarding but 7 unimplemented agents cannot.

**Decision being escalated:** Is onboarding a structural design requirement that must be specified before production begins, or a polish task that can be iterated during playtesting? The board cannot settle this because it depends on whether the developer's definition of "production-ready" includes validated player comprehension or only functional systems.

---

### Disagreement 2: Async pipeline — remove or fix?

**Position A (Business Analyst):** The entire async pre-generation pipeline is premature optimization for this scale. Generate content synchronously, show a brief loading screen, and move on. The pipeline adds complexity, creates placeholder reactions that deflate emotional moments, and introduces counting delays that confuse the player.

**Position B (Systems Designer + Narrative Critic):** The async pipeline solves a real problem (API latency during set opens with 5-9 tasks needing simultaneous generation). Removing it means loading screens during gameplay. The fix is to reorder the completion sequence (delay goal-state check until authored content is ready) and add debouncing for re-planning, not to remove async entirely.

**Decision being escalated:** Is the async pipeline the default architecture or a stretch goal validated empirically? The board cannot settle this because it depends on whether the developer's LLM API latency is measured or assumed — and no one has built the test harness yet.

---

## 3. QUICK WINS

1. **Fix the pair-consumption exception.** One sentence: "Multi-resident tasks read pairwise records without consuming them; only dedicated two-resident tasks consume a pair." This resolves Finding #1's mathematical incoherence with zero design change.

2. **Fix set sizes to 8 tasks.** One sentence: "Every task set contains exactly 8 tasks." This eliminates the 75% threshold variance (77.8%-87.5%) and simplifies content authoring (developer creates a predictable number of tasks per set).

3. **Add the backstory failure fallback.** One paragraph: if backstory generation fails after 2 retries, the task retires and counts toward thresholds, narrated as an open thread. This resolves Finding #3's softlock with a one-paragraph addition.

---

## 4. VERDICT

This document is architecturally strong — the Goose Solution Planner's validation loop, goal-state polling decoupled from LLM calls, and retirement-as-safety-valve are genuinely well-designed. The five blocking issues are all fixable with targeted, non-architectural edits (clarify the consumption math, cap retirement, add a generation fallback, define MVP tiers, and either expand or honestly scope the pitch). The single change that matters most is **fixing the retirement subsystem**: cross-examination revealed it as the point of failure that touches pacing, narrative integrity, player agency, softlock prevention, and the "no failure state" claim. Cap retirements at 25% per set, require player attempt before retirement, and treat retirement as a narrative event. Everything else cascades from that fix. The developer should ship the core loop with 3 residents and one task set as the MVP; the full 6-resident, 30-40-task vision should be treated as a stretch goal, not the deliverable.
