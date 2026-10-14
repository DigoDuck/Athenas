# Decisions

Decisions that shape Athenas, newest last. Each entry says what was decided, why, and where it
came from. Accepted entries change only through a new entry that supersedes them.

The day 28 verdict (spec section 4.11) is written here as its own entry.

## Accepted

### D-001: Daily study happens only in Athenas

- Date: 2026-10-12. Source: interrogation, decision 1.
- Decision: in the daily routine, studying, practicing and reviewing happen only in Athenas.
  External tools (NotebookLM, Claude) are used only to prepare content.
- Why: the Obsidian system stopped because the tools were spread out.

### D-002: Tool first, portfolio later, standard stack

- Date: 2026-10-12. Source: interrogation, decision 2.
- Decision: build for real use first; portfolio polish only after the first month of use.
  Standard stack with no exceptions: Django 5 + DRF + Py-FSRS, React + Vite, PostgreSQL,
  Docker Compose.
- Why: the hypothesis needs real use before finish work; the stack counts for the job search.

### D-003: v1 has the eight briefing items, each at its minimum, plus session logging

- Date: 2026-10-12. Source: interrogation, decision 3.
- Decision: organization, roadmap, content, study, practice, review, pomodoro and backup, each
  at the minimum listed in spec section 2.1, plus the session event table.
- Why: each item replaces a tool that is outside Athenas today.

### D-004: First-month metrics, written verdict on day 28

- Date: 2026-10-12. Source: interrogation, decision 4.
- Decision: measure the first month; write the verdict on day 28. No stop rule and no freeze.
- Why: without a written consequence, the metric is decoration.
- Note: D-010 defines the window, the unit and the pre-written reading of each result. It keeps
  this entry's "no stop rule and no freeze".

### D-005: Review without pressure: Py-FSRS, daily caps, silent return

- Date: 2026-10-12. Source: interrogation, decision 5; review rules 1 to 7.
- Decision: Py-FSRS scheduling, a daily review cap (20) and a daily new card cap (5), both
  adjustable; only "reviews today" is shown, never overdue totals; overflow is redistributed
  silently; after 3 or more days away, a return session with no mention of the absence;
  ratings Again, Hard, Good; the day follows Bahia time.
- Why: spaced repetition piles up by nature.

### D-006: One Markdown file per subtopic, with fixed labels

- Date: 2026-10-12. Source: interrogation, decision 6; content contract rules 1 to 4.
- Decision: content is one Markdown document per subtopic in the template of spec section 4.1.
  Questions (`P1`...) and cards (`C1`...) have fixed labels that carry their history.
- Why: the same file works as the prompt for NotebookLM and Claude and as the export to the
  vault.

### D-007: Markdown cards enter pending and are approved one by one

- Date: 2026-10-12. Source: interrogation, decision 7; content contract rule 5.
- Decision: cards declared in the Markdown enter as pending, outside the queue. Approval is one
  at a time with keyboard shortcuts, with no "approve all". The new card cap applies to them.
- Why: a card that may have been written by AI goes through Diogo's review before the routine.

### D-008: Desktop only, local, use mode always on, backup to the vault

- Date: 2026-10-12. Source: interrogation, decision 8.
- Decision: runs only on the computer, locally. Use mode is always on (starts with Windows,
  `127.0.0.1` only, no login), its data is separate from dev, and a daily backup goes to the
  vault folder.
- Why: running locally must not become the friction Athenas exists to remove.

### D-009: Athenas does not use ZEUZ

- Date: 2026-10-12. Source: interrogation, decision 9 (ZEUZ DEC-088).
- Decision: Athenas does not integrate with ZEUZ.
- Why: the DEC-087 test found no concrete reason to.

### D-010: Day 28 rule: pre-written reading, no automatic stop

- Date: 2026-10-12. Source: Diogo's choice of "rule A, adjusted" in the day 28 discussion.
- Decision: the verdict on day 28 applies a reading written in advance for each result. There
  is no automatic stop and no freeze, so D-004 stands.
  - Window: 4 blocks of 7 consecutive days from day 1, in Bahia time. Day 1 is the first day
    use mode works with at least one concept registered (to be confirmed when recorded, spec
    `[Q1]`).
  - Unit: a distinct day with at least one completed activity. Several sessions on the same
    day count once.
  - 3 or 4 blocks with 3 or more days of use: success. Move on to the portfolio phase.
  - 2 of 4: neither success nor failure. One single 14-day extension, with no new features.
    Success if both extra blocks meet the bar. If the 2 blocks that met it are the last two of
    the original window, the tie-break leans toward success.
  - 0 or 1 of 4: hypothesis not confirmed. A written diagnosis from the session event table
    comes before any new feature; the next decision is Diogo's.
  - The verdict contains, in this order: numbers per block, features that shipped that month,
    sessions lost to being away from the computer, the reading applied.
- Why: without a written consequence the metric is decoration (D-004), and four weeks of one
  person's data is too small a sample to freeze the project on.
- Completion recording: answered in D-013 (`completed_at`).
- Note: D-016 supersedes the day 1 line. The rest of this entry stands.

### D-011: Redistribute overflow when building the queue, without rewriting due dates

- Date: 2026-10-12. Source: proposal P-01 in the first spec draft, accepted by Diogo.
- Context: review rule 3 says cards due beyond the cap are redistributed silently, lowest
  estimated retention first. This can be done two ways.
- Decision: keep the due date Py-FSRS computed. When the day's queue is built, order due cards
  by current retrievability, ascending, and take up to the cap. Cards left out stay due and
  compete again the next day.
- Why: the stored state stays exactly what Py-FSRS produced, so the future optimizer trains on
  clean data, and there is no batch job that can fail silently. The user sees the same thing
  either way.
- Risk: if Diogo stays under the cap for a long time, a backlog of due cards grows invisibly.
  The UI still never shows it (rule 2), but the support metric "fraction of the day's reviews
  done" must be read against the capped queue, not the backlog.

### D-012: Repository documents in English

- Date: 2026-10-12. Source: proposal P-02 in the first spec draft, accepted by Diogo.
- Decision: `docs/spec.md`, `DECISIONS.md` and other repo documents are in English, like
  commits and pull requests. Contract text that the app parses (Markdown headings such as
  "Ideia central", the "Resposta de referência" line) and UI copy stay in Portuguese.
- Why: the repo becomes a portfolio piece after the first month (D-002).

### D-013: Answers to the spec's open questions

- Date: 2026-10-12. Source: Diogo accepted the suggestions for Q1 to Q17 in the first spec
  draft.
- Decision: the answers are listed in `docs/spec.md` section 9 and written into the rules they
  affect. The ones that shape the core most:
  - A session event has `completed_at`, empty when the activity is abandoned. Only events with
    it count as sessions (Q1).
  - Completion is suggested for a subtopic when all its blocks were read and one attempt is
    rated right or partial; a concept's status is derived from its subtopics (Q3, Q4).
  - The review cap counts distinct cards per day; a same-day repeat does not use a slot (Q14).
  - The day in Bahia time starts at midnight (Q9).
- Why: the source left these open, and the core acceptance tests depend on them.

### D-014: Text before the first heading is kept as an extra block with an empty heading

- Date: 2026-10-12. Source: parser slice (`backend/content/parser.py`); Diogo asked for it to be
  recorded.
- Context: spec 4.2 says an unknown `##` heading becomes an `extra` block and `[C3]` says content
  is never discarded, but nothing defines text that comes before the first `##`.
- Decision: such text becomes an `extra` block with an empty heading, in first position. Blank
  text creates no block.
- Why: it is the smallest way to honor `[C3]` without a new block kind.
- Risk: re-import identity follows the `P` and `C` labels (spec 4.2.6), not blocks, so an empty
  heading does not collide today. If a later slice matches blocks by heading, this entry has to be
  revisited.

### D-015: A block's read mark lives on the block and survives re-import only for identical text

- Date: 2026-10-12. Source: card approval slice; Diogo chose option A of three.
- Context: spec 4.4.4 suggests completion when all of a subtopic's blocks were read, but does not
  say where "read" is stored. Blocks are rebuilt on every import and have no identity of their own
  (spec 4.2.6), so a read mark cannot follow a block across re-imports by heading: the empty
  heading of D-014 would collide.
- Decision: each block has a nullable `read_at`. On re-import, a new block whose kind, heading and
  body are all identical to an old block that was read takes over that mark. Any other block
  starts unread.
- Why: fixing a typo in one section unmarks only that section, and nothing matches by heading.
  The alternatives were resetting every mark on re-import (any edit erases reading progress) and
  deriving reads from session events (they do not exist yet and would point to rebuilt blocks).
- Risk: two blocks with identical text are interchangeable, so their marks are shared one to one
  in no particular order.

### D-016: Day 1 starts with the first release that passes the M1 gate

- Date: 2026-10-14. Source: proposal P-03 in `docs/plan.md`, accepted by Diogo.
- Context: D-010 set day 1 as the first day use mode works with at least one concept registered,
  marked "to be confirmed when recorded". Under that line, tagging the current skeleton and
  registering a concept would start the 28-day window before the app could run the cycle or
  record session events.
- Decision: day 1 is the first day use mode runs a tag that passes the M1 gate of `docs/plan.md`
  (study, practice, completion rules, review, home screen with the return session, session events
  and backup), with at least one concept registered. Notebook mode, pomodoro and the settings
  screen may ship during the month; the verdict lists them under the features that shipped that
  month. This supersedes only D-010's day 1 line.
- Why: the verdict must judge an app that can run the full cycle, and days of use before session
  events exist cannot be counted.
- Risk: the window starts later, and the features that ship during the month change the app under
  measurement. D-010 already expects that, and the verdict names them.

### D-017: A session event references the subtopic or the question, never a block

- Date: 2026-10-14. Source: proposal P-04 in `docs/plan.md`, accepted by Diogo.
- Context: spec 3.2 says a session event references the activity's subject. Blocks are rebuilt on
  every re-import (D-015) and cascade from `Content`, so a foreign key to `Block` would either be
  deleted by a re-import or block it.
- Decision: events about a subtopic (reading, notebook, explanation) store the `subtopic` as a
  protected foreign key; a reading event also stores `block_order`, an integer. A question event
  stores the `question` as a protected foreign key. A review session event has no subject.
  "Continue where I stopped" reads the latest reading event.
- Why: subtopics and questions keep their identity across re-imports (questions are archived,
  never deleted, spec 4.2.6), so the measurement survives any edit to the content.
- Risk: after a re-import that reorders sections, `block_order` can point at another block than
  the one read; "continue where I stopped" then opens a nearby block, and the metric does not use
  the block. A subtopic with events can no longer be deleted, as one with attempts already can't.

### D-018: Card model for manual cards and the Py-FSRS state

- Date: 2026-10-14. Source: proposal P-05 in `docs/plan.md`, accepted by Diogo.
- Context: `Flashcard` requires a subtopic and has a unique (subtopic, label) constraint, which
  rejects a second manual card with an empty label. Spec 3.2 allows manual cards on a concept
  (Q6) and stores the Py-FSRS state as the library gives it.
- Decision:
  - `origin` is `markdown` or `manual`.
  - `subtopic` and `concept` are both nullable; a check constraint requires exactly one of them,
    and a subtopic for markdown cards.
  - The (subtopic, label) unique constraint applies only to markdown cards.
  - `fsrs_card` stores `Card.to_dict()` as JSON. An indexed `due` column is written from it on
    every rating, and the review queue filters on that column.
  - `ReviewLog.fsrs_log` stores `ReviewLog.to_dict()` as JSON.
- Why: the stored state is exactly what Py-FSRS produced (as D-011 requires) and stays usable by
  the later optimizer, while due cards are still filtered in SQL.
- Risk: `due` duplicates a value inside `fsrs_card`. Both are written by one service function
  only, so they cannot drift apart.

### D-019: Backup runs where the vault folder is reachable, chosen by a spike

- Date: 2026-10-14. Source: proposal P-06 in `docs/plan.md`, accepted by Diogo.
- Context: the vault is on `G:`, a Google Drive virtual drive. A container only sees the host
  folders mounted in the compose file, so `Settings.backup_folder` cannot point a container at a
  new place.
- Decision: before the backup slice, a spike writes a file into the vault folder from a container
  and checks that it reaches Drive. The export is one management command either way.
  - If it works: a `backup` service in the use-mode compose checks every hour and exports when
    the last export is older than 24 h, which also covers the startup catch-up (spec 4.10.3). The
    host folder is set in `.env.use`, and `Settings.backup_folder` is dropped, with spec 3.2
    updated in the same PR.
  - If it does not: a Windows scheduled task on the host runs the same command through
    `docker compose exec`.
  The spike result is added to this entry.
- Spike result (2026-10-14, H2): it does not work. Docker Desktop (WSL 2) shares only `C:` with
  its VM; `G:` is not shared even when Drive is mounted before the engine starts. A `-v` bind of
  a `G:` path does not fail: Docker creates an empty folder on the VM's own disk, the write exits
  0, and nothing reaches the vault. The accented `Núcleo` segment is not the cause, since the same
  test on an accented `C:` folder works.
- Outcome: the scheduled task branch, with one change. `docker compose exec` runs the command
  inside the container, which cannot see `G:` either, so the file reaches the vault from Windows:
  - The use-mode `backend` service bind-mounts a local staging folder on `C:`, outside the repo
    because use mode checks out tags in the same folder. The command writes the exports there
    and applies the 30-day retention.
  - A Windows scheduled task runs every hour: the command through `docker compose exec`, which
    exports only when the last export is older than 24 h (spec 4.10.3), then a copy from the
    staging folder to the vault folder with `robocopy`.
  - Both folder paths live in `.env.use`. `Settings.backup_folder` is dropped, with spec 3.2
    updated in the same PR.
- Why: the folder stays configured, not hard-coded (spec 4.10.2), in the only place the
  container and the task can both honor it. Copying every hour, not only after an export, also
  catches up when Drive was not running at export time.
- Risk: with the scheduled task, backup depends on a Windows setting outside the repo. The
  restore drill before day 1 has to cover that path. A `G:` bind fails silently, so nothing in
  compose mounts `G:`, and the task treats a `robocopy` exit code of 8 or more as a failure.
  Retention must reach the vault without a bare `robocopy /MIR`, which would wipe the vault if the
  path were wrong; S7 picks how.
