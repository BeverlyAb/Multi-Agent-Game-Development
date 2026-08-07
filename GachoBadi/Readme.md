# Gachō Badi — Dynamic Content Pipeline (Assignment #4)

A RAG pipeline that reads Gachō Badi's own GDD (`gdd.txt`) and generates
three content types the game specifically needs, each checked by a
Consistency Critic Agent before it's accepted. Separate from the AI
Architecture crew in this folder (`agents/runtime/`, `agents/dev_time/`,
`crew.py`, `main.py` — Assignment #3, untouched by this work).

```bash
cd GachoBadi
python3 run_content_pipeline.py
```

No API key required (deterministic fallback, see `llm_client.py`). Full
output — query, retrieved chunk, raw generation, critic report,
corrected text — is written to `output/content_pipeline_run.json`.

## Game-Anchored Source

Knowledge base = `gdd.txt` itself, Draft #10 (no placeholder lore).
`rag.py` splits it into paragraph-level chunks (83 as of this GDD draft)
and retrieves with plain TF-IDF — no embeddings, no third-party
dependency.

## Content Fit — what was generated, and why the game needs it

| Content type | Fills this gap |
|---|---|
| **Item affordance spec** (a memento) | GDD describes an Item Interaction Agent (Draft #8+); `agents/runtime/` never implements one. |
| **Relationship backstory** (Hazel/Otto, "drifted apart") | `RelationshipAgent` only assigns a label; Draft #9 made the one-line authored "why" mandatory, and nothing generates it. |
| **Task premise + verb plan** (mend a falling-out at Hazel's Bakery) | Draft #10 says the ~30-40 task premises are pre-authored content; the runtime `TaskCreatorAgent` only round-robins 5 generic templates. |

Three of the four pipeline agents (`agents/dynamic_content/`) are
adapted from `UntitledGooseGame_Multi_Agent`'s agents, each pointed at
one of these gaps. The fourth, the Consistency Critic Agent, exists
because that borrowing risks leaking UGG's own verbs/tone in — see below.

## RAG Implementation — query, retrieved chunk, output

**Query:** `"item interaction affordance memento goose actions reset rule no permanent loss"`
**Retrieved chunk #14:** `"How items participate in tasks: every interactive object has an explicit affordance record maintained by the Item Interaction Agent..."`
**Output:** `"a lost memento (memento): identifies an owner and a shared-memory association; the goose can grab/carry/drop/hide it; ...it drifts back to its owner or origin building if left obscure..."`

**Query:** `"relationship agent authored backstory drifted apart why not just a label flip"`
**Retrieved chunk #53:** `"...a short one-line backstory for how that state came to be (e.g. 'drifted apart after a mixed-up mail delivery')..."`
**Output:** `"Hazel and Otto: drifted apart -- a missed birthday."`

**Query:** `"tasks are actions goose must perform on residents or buildings open-ended indirect interaction"`
**Retrieved chunk #13:** `"Tasks are actions that the goose must perform on residents or buildings, framed around bringing residents together rather than causing them trouble..."`
**Output (before critic):**
```
Help Hazel and Otto patch up a disagreement at the Hazel's Bakery.
Goose: Grab near the Hazel's Bakery.
Goose: Run near the Hazel's Bakery.
Goose: Honk near the Hazel's Bakery.
Otto: startles, then laughs off the disagreement with Hazel
```
(Full, un-truncated triples for all three in `output/content_pipeline_run.json`.)

## Consistency Checking — what the Critic actually caught

The task premise above used **"Run"** — Untitled Goose Game's verb, left
in `CONNECTION_KINDS["mend_fallout"]`
(`agents/dynamic_content/task_premise_content_agent.py`) when that table
was adapted from UGG's `ChecklistCreatorAgent` without updating its verb
list. Gachō Badi's five verbs are Honk/Grab/Pick up/Duck/Dash — "Run"
isn't one of them. Left in on purpose so this catch is real, not staged:

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

A second, independent check (banned tone words — "mischief," "chaos,"
"prank" → "connection," "harmony," "gesture") didn't fire this run
because nothing tripped it, but exists for the same reason: Gachō Badi
is "quiet community-builder," never mischief-for-its-own-sake.

## Voice Judgment

**Does it sound like Gachō Badi, not UGG or generic content?** Yes, once
corrected — the item affordance and relationship backstory were in-voice
on the first pass; the task premise needed the critic's fix above to
stop importing UGG's verb.

**Concrete retrieval tweak:** the task-premise query originally read
`"task creator connection goose verbs honk grab pick up duck dash no
dialogue"`, which retrieved the roster/scoping paragraph instead of the
GDD's actual task-definition sentence. Rewriting it to echo the GDD's own
wording (`"tasks are actions goose must perform on residents or
buildings open-ended indirect interaction"`) pulled chunk #13 in instead
— the version now in `content_pipeline.py` (see the comment at the call
site for the before/after).

## Bonus: playing it in Phaser

`web/index.html` + `web/game.js` turn the same JSON into a scene (same
pattern as `UntitledGooseGame_Multi_Agent/web`). Serve from `GachoBadi/`
itself (not from inside `web/`, which 404s the live fetch):

```bash
cd GachoBadi && python3 -m http.server 8000
# open http://localhost:8000/web/index.html
```

Move with WASD/arrows; verbs are Honk (Space), Grab (E), Pick up (R),
Duck (Q), Dash (Shift). The **Task** panel shows which verbs the plan
still needs; the **Consistency Critic** panel shows the same pass/fail
verdicts as above, in-game.
