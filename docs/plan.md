# Athenas v1 delivery plan

Status: accepted, 2026-10-14. `docs/spec.md` says what v1 is; this file says in which order it
gets built and what each slice needs. Where the two disagree, the spec wins. Proposals P-03 to
P-06 were accepted as `DECISIONS.md` D-016 to D-019; P-07 is still open. The phase after v1 (hosting, login,
three testers) is ordered in `docs/plan-testers.md` (D-042).

## 1. Where v1 stands

State of `main` at `b333839`:

| Spec item (2.1) | Done | Missing |
| --- | --- | --- |
| Organization | Areas, concepts, subtopics with the four fields; tracks and steps with move up and down | Concept status derived from subtopics (4.4.6) |
| Roadmap | Track list and step order | Status per concept and the next step (4.5.1) |
| Content | Paste, preview, save as draft or ready, re-import by label, pending card approval | Nothing for v1 |
| Study | `Block.read_at` (D-015) | Reading screen, resume position, in-progress rule (4.4.5), notebook mode |
| Practice | `PracticeQuestion` and `Attempt` models | Endpoints and screen, draft that survives closing the browser (4.8.4) |
| Review | `Flashcard` and `ReviewLog` models, `fsrs==6.3.2` installed | FSRS state on cards, queue and caps, rating, review screen, manual cards, return session |
| Pomodoro | Durations in `Settings` | Timer and notice |
| Backup | `Settings.backup_folder` | Export, schedule, retention, restore command |
| Measurement | Nothing | `SessionEvent` and recording from every activity |
| Home screen | Opens on the roadmap | Continue where I stopped, next step, "revisões de hoje: N" |
| Settings | `/api/settings/` endpoint | Screen |
| Use mode | Compose file, `make use-*`, `.env.use` created | No tag exists yet; Docker Desktop was not running on 2026-10-14 |

Acceptance scenarios already covered: 16 to 18 and 26 to 42 from spec section 8, plus 43 to 48
and a to f. Still open: 1 to 15 and 19 to 25.

## 2. Findings that shape the order

1. **Day 1 can start by accident.** D-010 defines day 1 as the first day use mode works with at
   least one concept registered. Tagging `v0.1.0` today and registering a concept would start the
   28-day window with no study, no review and no session events: days of real use would go
   unmeasured, and the verdict would judge an app that cannot run the cycle. See P-03.
2. **Session events come before day 1.** The day 28 metric is computed only from `SessionEvent`.
   The model lands with the first activity (S1), and every later activity slice records its own
   events.
3. **Events must not point at blocks.** Blocks are rebuilt on every re-import (D-015) and cascade
   from `Content`. A foreign key from `SessionEvent` to `Block` would either be deleted by a
   re-import or block it. See P-04.
4. **The card model does not fit manual cards yet.** `Flashcard.subtopic` is required, there is no
   `origin`, and the unique constraint on (subtopic, label) would reject a second manual card with
   an empty label. FSRS state is missing too. See P-05.
5. **Py-FSRS 6.3.2, checked in the wheel:** `Scheduler(desired_retention=0.9,
   learning_steps=(1 min, 10 min), relearning_steps=(10 min,), enable_fuzzing=True)`,
   `review_card`, `get_card_retrievability`, `Card.to_dict` and `from_dict`, `ReviewLog.to_dict`
   and `from_dict`. Two consequences: fuzzing makes due dates random, so tests that check dates
   turn it off or check a range; and `due` must also be a real indexed column, because the queue
   filters on it.
6. **The vault lives on `G:`, a Google Drive virtual drive.** Nobody has checked whether Docker
   Desktop can bind-mount it and whether files written from a container sync. That decides how
   backup runs, so it is a short spike in M0, not a discovery inside S7. See P-06.
7. **`Settings.backup_folder` and a bind mount disagree.** A container only sees the host folders
   mounted in the compose file, so a path typed in the UI cannot point anywhere new. See P-06.
8. **Each new tag migrates the real database.** From day 1 on, every `make use-up` of a new tag
   runs migrations on the data the experiment depends on. The release checklist (section 5) runs
   a backup first.

## 3. Decisions

| # | Question | Answer | Needed before |
| --- | --- | --- | --- |
| P-03, D-016 | When does day 1 start? | The first day use mode runs a tag that passes the M1 gate. Notebook mode, pomodoro and the settings screen ship during the month and are listed in the verdict, as D-010 already expects ("features that shipped that month"). This amends only D-010's day 1 line, which was marked "to be confirmed". | Tagging anything |
| P-04, D-017 | What does a session event reference? | `subtopic` (protected FK) plus `block_order` (integer) for reading, `question` (FK) for practice, nothing for a review session. No FK to `Block`. "Continue where I stopped" reads the latest reading event. | S1 |
| P-05, D-018 | Card model for manual cards and FSRS | `origin` (markdown or manual); `subtopic` and `concept` both nullable, with a check constraint that exactly one is set and that markdown cards have a subtopic; the label constraint applies only to markdown cards; `fsrs_card` JSON from `Card.to_dict()` plus an indexed `due` column kept in sync; `ReviewLog.fsrs_log` JSON. | S4 |
| P-06, D-019 | How does backup run, and where does its path live? | The M0 spike showed a container cannot write to `G:`. An hourly Windows scheduled task runs the management command through `docker compose exec`, which exports into a staging folder on `C:` when the last export is older than 24 h, then copies that folder to the vault with `robocopy`. Both paths live in `.env.use` and `Settings.backup_folder` is dropped. | S7 |
| P-07 | Hours per week and target date | Open. In the vault note since 2026-10-12. Needed to turn section 4 into dates. | Dating the plan |

## 4. Milestones and slices

One slice is one branch and one PR. CORE slices start with Diogo writing the acceptance tests
(spec 7), and the approach is described before any code. Sizes: S is one sitting, M two or
three, L more.

### M0: Housekeeping, before S1

- H1: the untracked `athenas-design-system/`, `athenas-planos-de-fundo/`, `briefbook-athenas/`
  and `icon_athenas*` (about 22 MB, mostly PNG) move to the vault (`07 - Assets`) or into
  `.gitignore`. The two stale worktrees under `.claude/worktrees/` and the merged local branches
  are removed, with Diogo's ok.
- H2: spike for P-06: write a file into the vault folder from a container and confirm it reaches
  Drive. Done 2026-10-14: it does not work, see D-019.
- H3: Docker Desktop set to start with Windows (spec 5.1).

### M1: Day 1 gate, release `v0.1.0`

| Slice | Branch | Type | What | Acceptance scenarios | Depends on | Size |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | `feat/study-reading` | CORE | `SessionEvent` model (P-04) and endpoints to start and complete an activity; reading screen, one block at a time in contract order; mark a block read; opening the first block moves the subtopic to in progress; resume at the last block after closing the browser | 15, 19; new: reading a block records an event; reopening resumes at the last block | P-04 | M |
| S2 | `feat/practice` | PLUMBING | Questions with the reference answer shown only after submit; "explicar com minhas palavras"; self-assessment; previous attempts visible; draft kept in `localStorage`; create-only attempts endpoint (no update or delete, spec 3.2); events | none (not core) | S1 | M |
| S3 | `feat/completion-rules` | CORE | Completion suggestion and confirmation; concept status derived from subtopics; roadmap shows status per concept and the next step | 20 to 24 | S1, S2 | M |
| S4 | `feat/review-scheduling` | CORE | Card model change (P-05) with a data migration for existing cards; rating through Py-FSRS; day queue: due cards by retrievability up to the cap, distinct cards per Bahia day, new card cap; "reviews today" count | 1 to 11, 25 | P-05 | L |
| S5 | `feat/review-session` | PLUMBING | Review screen with three buttons and keyboard shortcuts; review session event; manual card creation on a subtopic or a concept | none | S4 | M |
| S6 | `feat/home` | CORE | Home screen: continue where I stopped, next step, "revisões de hoje: N"; `app_opened` event; return session after 3 full Bahia days, at most 5 reviews, no mention of the absence | 12 to 14; new: each home load records `app_opened` | S1, S3, S4 | M |
| S7 | `feat/backup` | PLUMBING | Management command exporting JSON (everything) and Markdown (`Content.raw_markdown`, one file per subtopic) into the staging folder; 24 h catch-up; 30-day retention; hourly Windows scheduled task, registered by a script in `scripts/`, that runs the command and copies the staging folder to the vault (D-019); documented restore command | none; restore drill by hand | P-06, S4 | M |
| R1 | tag `v0.1.0` | release | Release checklist (section 5); restore drill; the full cycle of spec 6.1 by hand; day 1 date written in `DECISIONS.md` | everything green | S1 to S7 | S |

Why this order:

- S1 goes first because every later activity records events through its model.
- S4 is the largest risk (FSRS state, caps, Bahia day) and needs no screen, so it can start in
  parallel with S2 or S3 once P-05 is accepted. S5 and S6 wait for it.
- S3 needs attempts (S2) for the completion suggestion.
- S7 last in M1 because its export must include review history (S4), but its spike runs in M0.

### M2: During the first month, tags `v0.2.x`

| Slice | Branch | Type | What | Size |
| --- | --- | --- | --- | --- |
| S8 | `feat/notebook-mode` | PLUMBING | Notebook presentation: Objetivo, Ideia central, Exemplo, Resumo para o caderno, then one practice prompt (Q16); notebook event | S |
| S9 | `feat/settings-pomodoro` | PLUMBING | Settings screen (caps, retention, pomodoro durations); pomodoro with one discreet notice that never blocks studying | M |
| S10 | `feat/theme-screen` | CORE | "Novo tema" screen: Diogo types a theme and a goal, the app builds the request for any AI (the Markdown contract and the `athenas-tema` rules) to copy, then checks the pasted answer with the parser and creates the track, concepts, subtopics and contents, cards pending; one concept per round (D-030) | M |

Each one goes into the verdict under "features that shipped that month". Nothing outside spec 2.1
enters M2 except S10, which Diogo brought into v1 (D-030), and a 14-day extension, if it happens,
has no new features (D-010).

### M3: Day 28

- Compute the metric from `SessionEvent` with a script (no screen in v1, spec 4.11.1).
- Write the verdict entry in `DECISIONS.md`, in the order D-010 sets.
- Only on success: the portfolio debts in spec 5.3.

## 5. Release checklist, for every tag

1. `make lint` and `make test` green on `main`.
2. From day 1 on: run the backup command and confirm the files reached the vault.
3. Tag a clean `main`, check out the tag, `make use-up`.
4. Open `http://127.0.0.1:8470` and run one study step and one review by hand.
5. Check out `main` again for dev work.

## 6. Routine for each slice

- Branch `feat/<slug>` from `main`, one PR, squash merge.
- CORE: Diogo accepts the scenario titles and writes the tests in `tests/acceptance/` before the
  code; the approach is described before code is shown.
- A rule the spec leaves open gets a `DECISIONS.md` entry in the same PR, as D-014 and D-015 did.
- CORE slices get a study note in `estudos/`, as PRs 8, 10 and 13 did.
- v1 is done by spec section 6, not by this list.
