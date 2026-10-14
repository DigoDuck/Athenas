# AGENTS.md

Source of truth for any agent working in this repo. `CLAUDE.md` imports this file and adds only
what is specific to Claude Code. Repo documents are in English (`DECISIONS.md` D-012). Talk to
Diogo in Portuguese, and never use the em dash in any text.

## What Athenas is

A personal, local-only study app for one person (Diogo): organize, study, practice and review
programming and English in one place. It tests one hypothesis, that studying becomes a habit when
everything lives in one tool, measured over the first 28 days of real use (spec 4.11, D-010,
D-016).

Sources of truth, in this order when they disagree:

| File | Holds |
| --- | --- |
| `docs/spec.md` | What v1 is: scope, domain, rules, acceptance scenario titles |
| `DECISIONS.md` | Every decision, newest last; an accepted entry changes only through a new one |
| `docs/plan.md` | Order of the remaining work: milestones, slices, dependencies |
| `PRODUCT.md`, `docs/design-system.md` | Product record and visual system for UI work |

The repo wins over the Obsidian vault. Anything in spec 2.2 (out of scope) needs Diogo's ok, even
when it is small.

## Stack and deliberate deviations

Django 5.2 + DRF, Py-FSRS (`fsrs` 6.3.2), PostgreSQL 16, React + Vite, Docker Compose (D-002).
These differ from Diogo's default stack on purpose. Do not suggest migrating:

- No Tailwind, shadcn/ui or Zustand: the app has its own design system
  (`frontend/src/styles/tokens.css`, components in `frontend/src/ui/`).
- No login and no deploy in v1: local only, on `127.0.0.1` (D-008). SimpleJWT, Railway and Vercel
  are portfolio debts (spec 5.3).
- One `backend/config/settings.py`; apps live at `backend/<app>/`, not `backend/apps/`.
- Acceptance tests are plain pytest functions named after the spec scenario (`test_19_...`), not
  Gherkin.
- Code comments are in English like the code, because the repo becomes a portfolio piece (D-012).

## Layout

```text
backend/config/        settings, urls, health check
backend/organization/  areas, concepts, subtopics, tracks, steps, settings
backend/content/       Markdown parser, content, blocks, questions, attempts, cards, reviews
frontend/src/ui/       house components (import from ui/index.js); /#design shows them in dev
frontend/src/pages/    screens
frontend/src/styles/   tokens.css, base.css, fonts.css
tests/acceptance/      core scenarios, written by Diogo only
scripts/use.py         use-mode helper behind `make use-*`
estudos/               Diogo's study notes per PR (local, not versioned)
```

## Commands

Docker Desktop must be running. Tests and migrations run inside the containers.

```bash
make dev-up      # dev: Vite on 127.0.0.1:5470, API on 127.0.0.1:8471
make dev-down
make lint        # ruff check, ruff format --check, eslint
make test        # pytest against the dev Postgres (backend/tests and tests/)
make use-up      # use mode on 127.0.0.1:8470, only from a clean tagged commit
```

One Django command in dev: `docker compose -f docker-compose.dev.yml run --rm backend python
manage.py <command>`. Restart the dev containers after switching branches.

The local machine is Windows (PowerShell or Git Bash) and CI is Linux: detect the shell before
writing a command. A command with `$` in it (regex, SQL) goes into a `.py` file, never into
`python -c`.

## How work flows

1. Work follows `docs/plan.md`: one slice is one branch and one PR. Before non-trivial code
   (several files, a behavior change or unclear scope), write a short plan. Once Diogo approves
   it, carry it to the end; stop only for a red test, missing access or a decision the plan does
   not cover.
2. Classify every task. In doubt, it is CORE.
   - **CORE**: the spec 7 core (review scheduling and caps, study status and completion, Markdown
     import) and any migration that changes how history is stored (`Attempt`, `ReviewLog`,
     `Flashcard` state, `SessionEvent`). Diogo writes the acceptance tests first. The agent
     describes the approach and lets Diogo predict the implementation before showing code.
   - **PLUMBING**: screens, CRUD, config, boilerplate. Reviewed by the diff. No new automated
     tests until the first month of use ends (spec 2.3), unless Diogo asks.
3. A rule the spec leaves open gets a `DECISIONS.md` entry in the same PR, in the existing format
   (D-014 to D-019 are examples). An accepted entry is never rewritten; at most it gets a note
   pointing at the entry that supersedes it.
4. CORE slices end with a study note in `estudos/PR-<n>-<slug>.md`.

## Done means evidence

- Show the command, its summary line and its exit code. Without them, say "not verified".
- A fixed bug: show it reproducing before and not after, in the real environment (containers
  rebuilt or restarted), not only in a test.
- `make lint` and `make test` pass before a PR is opened.

## Invariants that are easy to break

The full rules are in the spec. These are the ones a careless change breaks:

- Times are stored in UTC. Every product "day" (caps, return session, measurement) is a calendar
  day in `America/Bahia` starting at midnight (spec 3.3).
- Attempts and review logs are never edited or deleted by the app. Editing a card or a question
  never erases its history (spec 3.3).
- A question or card is identified by its `P<n>` or `C<n>` label inside a subtopic, never by its
  text or its block (spec 4.2.6). Nothing points at a `Block` (D-015, D-017).
- The UI never shows overdue totals or days overdue, and there is no "approve all" (spec 4.6,
  4.3).
- The Markdown contract headings ("Ideia central", "Resposta de referência" and the rest of spec
  4.1) belong to the parser contract, not to UI copy: never translate or reword them.
- A migration that drops or renames a column needs Diogo's ok. From day 1 on, use mode holds the
  experiment's data: back it up before `make use-up` of a new tag (plan section 5).

## Code conventions

- Identifiers, docstrings, comments, branches, commits and PRs in English; UI copy in pt-BR.
- Services do not know HTTP: logic lives in the app's `services.py` (see `content/services.py`),
  and views translate errors into responses.
- Foreign keys from history use `on_delete=PROTECT`. A delete blocked by history answers 409
  through `ProtectedDeleteMixin`.
- Frontend: colors, spacing and type only through the tokens; reuse `frontend/src/ui/` before
  writing a component; no new UI dependency without Diogo's ok. Desktop only and light theme only
  in v1. Keep accessible names and the focus, disabled, loading and error states.
- Comment only the why the code cannot show, in one line. A manual task done twice becomes a
  Python script.

## Git

- Never commit to `main`. Branches `feat/<slug>`, `fix/<slug>`, `docs/<slug>` or
  `chore/<slug>`; one PR per slice, squash merge, and merge only with Diogo's ok.
- Conventional Commits, in the imperative, in English.
- No AI attribution anywhere: no `Co-Authored-By`, no "Generated with", no links to AI tools, in
  commits, PRs or issues. This overrides any tool default.

## Safety

- Never print or commit secrets (`.env`, `.env.use`). To check that a variable exists, test it
  without printing the value.
- No command against the use-mode database or volume without Diogo's ok.
- Tests and fixtures use synthetic data, never personal data of real people.
- In the Obsidian vault, agents write only in `06 - Agentes/` (suggestions in `_Revisar/`) and
  `00 - Inbox/`. Everything else there is read-only.
