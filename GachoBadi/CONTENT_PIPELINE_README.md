# Gachō Badi — Dynamic Content Pipeline (Assignment #4)

**Game:** *Gachō Badi (Goose Buddy)*. This is a second, separate pipeline
alongside the AI Architecture crew in this folder (`agents.py`/`crew.py`/
`main.py`, Assignment #3's deliverable, untouched by this work) — it
targets Assignment #4's rubric specifically: a RAG pipeline that reads
the GDD, generates content the game actually needs, and runs a
Consistency Critic Agent over the result.

Run it with:

```bash
cd GachoBadi
python3 run_content_pipeline.py
```

No API key required — see `llm_client.py`; the deterministic local
fallback always produces output. Full output (query, retrieved chunks,
raw generation, critic report, corrected text) is written to
`output/content_pipeline_run.json`.

## Playing it in Phaser

`web/index.html` + `web/game.js` turn that JSON into an actual scene, the
same pattern as `../UntitledGooseGame_Multi_Agent/web`: the memento
becomes a real prop, the relationship backstory becomes Hazel and Otto's
intro caption, and the (critic-corrected) task premise's verb plan
becomes the goose's own five-verb controls.

```bash
cd GachoBadi
python3 -m http.server 8000
# open http://localhost:8000/web/index.html
```

Serve from `GachoBadi/` itself, not from inside `web/` — the page fetches
`../output/content_pipeline_run.json`, and a server rooted at `web/`
can't resolve that path (verified: it 404s and the page silently falls
back to the JSON snapshot embedded in `index.html`, which still runs but
won't reflect a fresh pipeline run). Opening `web/index.html` directly as
a `file://` URL also works, off that same embedded snapshot — regenerate
it by pasting a fresh `output/content_pipeline_run.json` in after
re-running the pipeline.

**Controls:** move with WASD/arrows; the goose's five verbs are Honk
(Space), Grab (E), Pick up (R), Duck (Q), Dash (Shift). The **Task**
panel lists which verbs the active plan still needs — perform them near
Hazel's Bakery to resolve the task and trigger Otto's reaction line. The
**Lore** panel shows all three RAG-grounded outputs; the **Consistency
Critic** panel shows the same pass/corrected verdicts as the JSON,
in-game.

## Knowledge base (Game-Anchored Source)

The knowledge base is `gdd.txt` itself — Gachō Badi's own GDD, currently
Draft #10, the same file the rest of this repo keeps in sync. `rag.py`
splits it into 89 paragraph-level chunks (this document already writes
one paragraph per line, so chunking follows that structure directly
rather than an arbitrary character window) and retrieves with plain
TF-IDF over those chunks — no embeddings, no third-party dependency,
consistent with every other crew in this repo. Nothing here is
placeholder or generic lore; every generated output below is grounded in
an actual retrieved sentence from the actual GDD.

## Agents integrated from `UntitledGooseGame_Multi_Agent`

Three of the four agents in `content_agents.py` are adapted from that
crew's agents rather than written from scratch, each one aimed at a real
gap between GachoBadi's GDD and GachoBadi's own code:

| This pipeline's agent | Adapted from (UGG) | Gap it fills |
|---|---|---|
| Item Interaction Content Agent | Prop Designer Agent | The GDD (Draft #8+) describes an Item Interaction / World Affordance Agent that `agents.py`/`crew.py` never actually implemented — `Readme.md`'s own caveat admits this. |
| Relationship Backstory Content Agent | Villager Routine Agent | `RelationshipAgent` in `agents.py` only assigns a label (e.g. "drifted apart"); Draft #9 made the one-line authored "why" behind that label mandatory, and nothing generates it. |
| Task Premise Content Agent | Checklist Creator Agent | Draft #10 states the ~30-40 task premises are meant to be pre-authored content; the runtime `TaskCreatorAgent` only round-robins 5 generic templates — there's no authored catalog matching the GDD's own connection-type taxonomy. |
| Consistency Critic Agent | *(not adapted — see below)* | Exists because the borrowing above is itself a risk. |

That fourth agent is the point of the exercise as much as the other
three: Untitled Goose Game is a mischief/chaos game with five verbs
(Honk/Grab/Run/Tug/Flap) Gachō Badi doesn't share (Gachō Badi's five are
Honk/Grab/Pick up/Duck/Dash, and its tone is "quiet community-builder,"
never mischief-for-its-own-sake). Reusing UGG's agents is exactly how
that vocabulary leaks in, so a Critic Agent that checks every output
against the GDD chunks it was actually grounded in isn't optional here.

## The three generated outputs (Content Fit)

1. **Item affordance spec** for a memento — fills the Item Interaction
   Agent gap above. Grounded in gdd.txt's "How items participate in
   tasks" paragraph and the Item Interaction Agent's own description.
2. **Relationship backstory** for Hazel and Otto ("drifted apart") —
   fills the missing-backstory gap above. Grounded in the Relationship
   Agent's own description, which contains the GDD's example phrasing
   ("drifted apart after a mixed-up mail delivery").
3. **Task premise + goose-verb plan** for a "mend a falling-out" task
   between Hazel and Otto at Hazel's Bakery — fills the missing
   authored-catalog gap above. Grounded in the GDD's actual task
   definition paragraph ("Tasks are actions that the goose must
   perform...").

## RAG Implementation — query, retrieved chunk, output

From an actual run (`output/content_pipeline_run.json` has the full,
un-truncated version of all three):

**Query:** `"item interaction affordance memento goose actions reset rule no permanent loss"`
**Retrieved chunk #20** *(Game Mechanics)*: `"How items participate in tasks: every interactive object has an explicit affordance record maintained by the Item Interaction Agent..."`
**Output:** `"a lost memento (memento): identifies an owner and a shared-memory association; the goose can grab/carry/drop/hide it; residents can notice/retrieve/discuss it; it drifts back to its owner or origin building if left obscure outside of active use. No task-critical item can become permanently unrecoverable, per the GDD's Item Interaction Agent guarantee."`

**Query:** `"relationship agent authored backstory drifted apart why not just a label flip"`
**Retrieved chunk #59** *(Relationship Agent (new))*: `"...reads resident personalities and generates both a pairwise social state...and a short one-line backstory for how that state came to be (e.g. 'drifted apart after a mixed-up mail delivery')..."`
**Output:** `"Hazel and Otto: drifted apart -- a missed birthday."`

**Query:** `"tasks are actions goose must perform on residents or buildings open-ended indirect interaction"`
**Retrieved chunk #19** *(Game Mechanics)*: `"Tasks are actions that the goose must perform on residents or buildings, framed around bringing residents together rather than causing them trouble..."`
**Output (before critic):**
```
Help Hazel and Otto patch up a disagreement at the Hazel's Bakery.
Goose: Grab near the Hazel's Bakery.
Goose: Run near the Hazel's Bakery.
Goose: Honk near the Hazel's Bakery.
Otto: startles, then laughs off the disagreement with Hazel
```

## Consistency Checking — what the Critic actually caught

The task-premise output above used the goose verb **"Run"** — left over
from `CONNECTION_KINDS["mend_fallout"]` in `content_agents.py`, which
was adapted from UGG's `ChecklistCreatorAgent.OBJECTIVE_KINDS["distract_and_swap"]`
without updating its verb list. Gachō Badi's five goose verbs are
Honk/Grab/Pick up/Duck/Dash — "Run" isn't one of them. This is the exact
failure mode the agent-mapping table above predicts, left in the code on
purpose rather than hand-fixed, so this catch is real:

```
[Consistency Critic Agent] caught 1 issue(s) in task_premise:
  - used goose verb 'Run', which is not one of Gacho Badi's five verbs
    (Dash, Duck, Grab, Honk, Pick up) -- consistent with it being carried
    over while adapting an Untitled Goose Game agent; replaced with 'Dash'.
corrected -> Help Hazel and Otto patch up a disagreement at the Hazel's Bakery.
Goose: Grab near the Hazel's Bakery.
Goose: Dash near the Hazel's Bakery.
Goose: Honk near the Hazel's Bakery.
Otto: startles, then laughs off the disagreement with Hazel
```

The critic also carries a second, independent check (banned tone words
— "mischief," "chaos," "prank" — replaced with "connection," "harmony,"
"gesture") that didn't fire this run because nothing tripped it, but
exists for the same reason: it's a rule extracted from the GDD's own
"quiet community-builder, not mischief-for-its-own-sake" framing, checked
against the retrieved grounding chunks, not the critic's opinion.

## Voice Judgment — self-assessment

**Does it sound like Gachō Badi, not generic content or Untitled Goose
Game?** Mostly yes, once corrected. The item-affordance spec and the
relationship backstory both came out grounded and in-voice on the first
pass — no critic intervention needed. The task premise needed the
correction above to actually be true to the game (a task that told the
goose to "Run" would have been importing UGG's verb into Gachō Badi's
plan, which is precisely the lore break Assignment #4 asks a critic to
catch and correct, not just claim it would).

**A concrete retrieval tweak made to improve fit:** the task-premise
query originally read `"task creator connection goose verbs honk grab
pick up duck dash no dialogue"`. Run against the knowledge base, that
retrieved the roster/scoping paragraph and the tutorial-opening
paragraph — reasonable context, but not the GDD's actual task-definition
paragraph (chunk #19, "Tasks are actions that the goose must perform on
residents or buildings..."), which is the sentence that actually
establishes the task's tone and gives worked examples (the memento
return, the honk-at-the-coffee-carrier). Rewriting the query to
`"tasks are actions goose must perform on residents or buildings
open-ended indirect interaction"` — closer to the GDD's own wording
instead of a list of loosely related keywords — pulled chunk #19 in as
the top hit instead. That's the version in `content_pipeline.py` now;
the before/after is left as a comment at the call site.
