@AGENTS.md

# Claude Code in Athenas

Only what is specific to Claude Code. Everything else is in `AGENTS.md`. Folder-specific rules
load from `.claude/rules/backend.md` and `.claude/rules/frontend.md`.

## Skills

Invoke the matching skill before acting, not after a mistake. Never stack two skills that opine
on the same thing.

| Situation | Skill |
| --- | --- |
| Any code task | `ponytail`, with the scope below |
| Any change that alters pixels in `frontend/` | `impeccable` |
| CORE slice | `estudo-guiado`: Diogo predicts before seeing the code |
| Bug, exception, red test, regression | `mattpocock-skills:diagnosing-bugs` |
| Unit-level logic that needs tests, outside `tests/acceptance/` | `mattpocock-skills:tdd`, agreeing the seams with Diogo first |
| Django model, ORM, DRF or migration design | `django-patterns`; add `django-security` near user input or files |
| Diogo presents a plan, or a plan looks like it has a hole | `mattpocock-skills:grilling` |
| Review for bugs and security | `/code-review` |
| Review against the spec and the repo rules | `mattpocock-skills:code-review`, against `docs/spec.md`, `DECISIONS.md` and `AGENTS.md` |
| Review for over-engineering | `ponytail:ponytail-review` |
| Any PR that touches `backend/` | also the `django-reviewer` agent |

### Ponytail scope

Ponytail stays on in every session. What it decides depends on the task class:

- PLUMBING: `full`. The shortest working diff wins: reuse `frontend/src/ui/`, the existing
  services and the standard library before anything new.
- CORE: it still rules out new dependencies, new abstractions and "for later" code, but it never
  cuts acceptance tests, validation, history preservation or the step of describing the approach
  before code. When a shorter diff and the spec rule disagree, the spec rule wins.
- UI work: ponytail owns the logic and the dependencies; `impeccable` owns the visual layer and
  the interaction. Ponytail never removes accessibility, contrast or component states.

### Impeccable

- It works from the project's own design record: `PRODUCT.md`, `docs/design-system.md` and
  `frontend/src/styles/tokens.css`. Where they disagree with `docs/spec.md`, the spec wins.
- `taste-skill` and `frontend-design` are never used here: they bring their own palette and type
  and fight the tokens.
- The impeccable hook only reports after a write. It does not replace invoking the skill.

### Not in this repo

- `mattpocock-skills:research` for anything the repo or the spec already answers.
- `graphify`, except when resuming after a long pause.
- `mattpocock-skills:domain-modeling` must not create `docs/adr/` or a glossary file: decisions go
  to `DECISIONS.md` and the glossary lives in spec 3.1.
- `dataviz`: v1 has no charts and no metrics screen (spec 2.2).

## Guardrails in `.claude/settings.json`

- Edits under `tests/acceptance/` are denied (spec 7). The deny covers the file tools, not Bash,
  so never write there through the shell either. When a scenario needs a change, say what and let
  Diogo write it.
- That file is versioned: no secrets in it. Personal settings go to `.claude/settings.local.json`.
