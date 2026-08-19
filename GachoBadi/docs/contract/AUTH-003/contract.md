# Contract: Folder Management — Reduce Redundancy, Improve Clarity

**ID:** AUTH-003
**Status:** READY FOR REVIEW

## Problem

The project has accumulated redundant directories, misplaced files, and duplicated documentation across its evolution. Two directories named `definitions/` exist at different tree levels. `design_review/` mixes project design artifacts with course assignment handouts. A Mermaid architecture diagram lives in `design_review/` instead of `docs/architecture/`. Generated output and runtime logs are tracked in git, creating noise on every run. Empty placeholder directories (`src/`, `tests/`) have never held code. Documentation repeats the same information across `AGENTS.md`, `docs/architecture/`, `docs/development.md`, `workflow/README.md`, and `Readme.md`.

## Desired Outcome

By the end, there is one `definitions/` directory with both game and verification models. All documentation lives under `docs/`. Course materials live in a separate `assignments/` directory. Generated output, logs, and OS metadata are gitignored. Empty placeholders are removed. Each piece of documentation has a single authoritative home with no duplication.

## Requirements

1. **Merge definitions directories.** Move `workflow/definitions/models_verification.py` to `definitions/models_verification.py`. Delete `workflow/definitions/`. Update imports in `workflow/` files that reference `workflow.definitions.models_verification` to use `definitions.models_verification` instead.

2. **Consolidate design_review into docs.** Move `design_review/gdd.txt` → `docs/gdd.txt`. Move `design_review/SYNTHESIS.md` → `docs/synthesis.md`. Move `design_review/DIAGRAM.md` → `docs/architecture/diagram.md`. Move `design_review/Design Review Board — *.pdf` → `docs/`. Delete `design_review/` after all contents are relocated. Update all references to old paths in `AGENTS.md`, `docs/contract/`, `workflow/README.md`, `Readme.md`, and any Python files that hardcode `design_review/`.

3. **Separate course materials.** Create `assignments/` at the project root. Move `Assignment #4_ Dynamic Content Pipeline.txt`, `ASSIGNMENT #6 (MANDATORY)_ Build a GER Pipeline for Your Capstone.docx`, and `Rubric.png` from `design_review/` (or from wherever they land after step 2) into `assignments/`. These are course handouts, not project design artifacts.

4. **Update .gitignore.** Add to `GachoBadi/.gitignore`:
   - `output/crew/` — generated content regenerated every run
   - `workflow/logs/` — runtime JSONL logs
   - `.DS_Store` — macOS metadata
   - `*.pyc` is already covered; confirm `__pycache__/` is covered
   Then `git rm --cached` the currently tracked copies of these files.

5. **Remove empty placeholders.** Delete `src/` and `tests/` directories (both contain only `.gitkeep`). Remove their entries from `AGENTS.md` "Important Directories" and `docs/architecture/architecture.md` if referenced.

6. **Deduplicate documentation.** For each topic duplicated across files, designate one authoritative source and remove the duplicate from the other files:

   | Topic | Keep in | Remove from |
   |---|---|---|
   | Directory map / layer overview | `AGENTS.md` (concise) | `docs/architecture/architecture.md` (replace with a "see AGENTS.md" pointer) |
   | Verification commands | `AGENTS.md` "Before Completing a Task" | `docs/development.md` (replace with a "see AGENTS.md" pointer) |
   | Agent architecture diagram | `docs/architecture/diagram.md` (moved from `design_review/DIAGRAM.md`) | `docs/architecture/architecture.md` (replace inline diagram with a link to `diagram.md`) |
   | GER pipeline overview | `workflow/README.md` (canonical) | `Readme.md` (replace with a one-liner + link to `workflow/README.md`) |
   | Domain models | `definitions/models.py` (code is truth) | `docs/domain-models.md` (replace with "see `definitions/models.py`" + link) |

7. **Rename Readme.md for consistency.** Rename `GachoBadi/Readme.md` → `GachoBadi/README.md` to match the uppercase convention used by `workflow/README.md` and standard GitHub convention.

## Constraints

- **Scope:** do not modify files outside the stated areas. Do not change any Python logic, agent behavior, or game output — only move/rename files and update path references.
- **Dependencies:** no new dependencies.
- **API compatibility:** no Python API changes. Import path changes from requirement 1 must be the only code modifications.
- **Behavioral rules:** the project's coding rules in `AGENTS.md` apply.
- **Behavioral preservation:** the contract is strictly a file-organization refactor. Every file move, rename, path-reference update, and `.gitignore` change must be verifiably behavior-preserving:
  - Python imports must resolve to the same module objects (same classes, functions, constants).
  - `python3 executable/main.py` must produce identical game output (same agent messages, same generated content, same manifest structure).
  - `python3 workflow/generic/demo_verify.py --agents all` must pass with the same pass/fail verdict for every agent.
  - No new warnings, deprecation notices, or runtime errors may appear that were not present before the change.
  - If any automated check produces different output, the change must be reverted until the discrepancy is eliminated.
- **Import safety:** after requirement 1, run `python3 -c "from definitions.models_verification import *"` from the `GachoBadi/` root to confirm the new import path works. After all requirements, run `python3 workflow/generic/demo_verify.py --agents all` and `python3 executable/main.py` to confirm nothing broke.
- **Output diffing:** before implementing any requirement, capture a baseline of `python3 executable/main.py` stdout and `python3 workflow/generic/demo_verify.py --agents all` stdout to a temporary file. After each requirement, re-run both commands and diff against the baseline. Any non-empty diff (excluding timestamps or PIDs) indicates a behavioral change and must be investigated before proceeding.
- **Contract references:** `docs/contract/` paths are unaffected (they don't reference `design_review/` except in AUTH-001's review which cites `GachoBadi/design_review/SYNTHESIS.md` — update that reference to `docs/synthesis.md`).

## Acceptance Criteria

- [ ] All Requirements above are satisfied.
- [ ] Only one `definitions/` directory exists at the project root, containing both `models.py` and `models_verification.py`.
- [ ] `design_review/` directory no longer exists.
- [ ] `assignments/` contains the three course material files.
- [ ] `src/` and `tests/` directories no longer exist.
- [ ] `output/crew/`, `workflow/logs/`, and `.DS_Store` are gitignored and no longer tracked.
- [ ] `GachoBadi/README.md` exists (uppercase); `Readme.md` does not.
- [ ] `docs/architecture/diagram.md` exists (moved from `design_review/DIAGRAM.md`).
- [ ] No documentation topic is duplicated across more than one file.
- [ ] `python3 workflow/generic/demo_verify.py --agents all` passes.
- [ ] `python3 executable/main.py` runs without crashes.
- [ ] All path references in `AGENTS.md`, `docs/contract/`, `workflow/README.md`, and Python imports are updated.
- [ ] No unintended changes are present (`git diff` reviewed).
- [ ] No P0 or P1 review findings remain open.
- [ ] `AGENTS.md` "Before Completing a Task" steps are satisfied.
- [ ] **Behavior is identical to pre-refactor baseline:** stdout of `python3 executable/main.py` and `python3 workflow/generic/demo_verify.py --agents all` differ from the captured baseline only in timestamps/PIDs (no agent message changes, no output regressions, no new warnings).
- [ ] **Import integrity verified:** `python3 -c "from definitions.models_verification import *"` succeeds from `GachoBadi/` root and all expected names are importable.
- [ ] **No Python logic changed:** `git diff -- '*.py'` shows only import path updates (requirement 1); no function bodies, control flow, or string literals were modified.

## Ownership

- **Human:** owns and modifies this contract. Assigns the `Contract ID` and sets `Status`.
- **Reviewer:** reads the contract and owns this contract directory's `review.md`. Findings are numbered `P0-001`, `P1-001`, `P2-001`, ... per `docs/finding-severity.md`; only the reviewer assigns severities.
- **Implementer:** reads the contract and the review, modifies source code and tests, and owns this contract directory's `response.md`, disposing of each review finding by id.
- **AGENTS.md:** defines repository-wide rules; modified only with human approval (see `AGENTS.md` Governance).
