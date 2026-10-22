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

### D-020: A reading event covers one block, and completing an event is its only change

- Date: 2026-10-15. Source: study reading slice (S1); Diogo accepted the recommended options.
- Context: spec 3.2 gives a session event both `started_at` and `completed_at` in one row, while
  history is create-only. The spec does not say what one reading activity is, where the events
  live, or in which order study shows blocks whose headings are out of contract order.
- Decision:
  - `SessionEvent` lives in its own app, `activity`, with generic endpoints that later slices
    reuse: `POST /api/events/` starts an activity and `POST /api/events/<id>/complete/` finishes
    it. There is no list, update or delete endpoint.
  - Completing sets `ended_at` and `completed_at` once. A second completion answers 409, and an
    `app_opened` event cannot be completed, so it never counts as a session.
  - One reading event per block. Opening a block starts it with `block_order`; marking the block
    read completes it and sets the block's `read_at` (D-015) if it was unset.
  - Study shows blocks in document order, which the template already keeps in contract order.
    Known sections written out of order are not rearranged.
- Why: one event per block makes a day with any finished block a session and gives "continue
  where I stopped" the latest block opened (D-017). Generic endpoints keep practice, review and
  the home screen from adding their own. A separate app keeps this slice's migration apart from
  the card model change in `content` (D-018).
- Risk: a block opened and left without marking it read stays as an event without
  `completed_at`, which the metric reads as abandoned, as spec Q1 intends.
- Note: D-023 makes the read mark conditional on the content not being saved after the event
  started, and corrects the claim that the spec leaves block order open. The rest of this entry
  stands.

### D-021: A practice event spans one answer, and saving the attempt completes it

- Date: 2026-10-16. Source: practice slice (S2).
- Context: spec 4.8.3 says practice offers questions with a reference answer and "explicar com
  minhas palavras", that the reference answer appears only after submitting, and that Diogo then
  rates the attempt. It does not say when a practice activity starts or ends, nor how an attempt
  relates to its event.
- Decision:
  - Opening one question or the explanation starts its event through `POST /api/events/`
    (D-020), `question` with the question or `explanation` with the subtopic.
  - `POST /api/attempts/` takes that event, the text and the self-assessment, creates the
    `Attempt` from the event's subject and completes the event, in one transaction. There is no
    other way to create an attempt and no update or delete.
  - Practice lists only questions that are not archived and have a reference answer. Attempts of
    archived questions stay in the database and out of the screen.
  - The draft (text and whether it was submitted) lives in the browser's `localStorage`, per
    question or per subtopic for the explanation, and is cleared when the attempt is saved.
  - Previous attempts appear after submitting, next to the reference answer, so they do not
    give the answer away before a new one is written.
- Why: an attempt without a completed event would be practice the day 28 metric never sees, and
  two separate calls could leave one without the other. The rating comes after the reveal, so the
  attempt can only be saved once the rating exists.
- Risk: the reference answer travels in the practice payload and only the screen hides it, which
  is enough for a single local user. A draft lives in one browser profile; clearing site data
  loses it, which the server never knew about. Reopening a draft starts a new event and leaves
  the earlier one without `completed_at`, which the metric reads as abandoned, as with reading.

### D-024: Study status changes only through the rules, and a completed subtopic can be reopened

- Date: 2026-10-16. Source: completion rules slice (S3); Diogo chose the options.
- Context: spec 4.4 fixes when a subtopic is suggested complete and how a concept's status is
  derived, and spec 3.2 says study status is set by those rules. The Library still had a manual
  "Status de estudo" select, and the spec does not say whether a subtopic can be completed
  without a suggestion, whether a completion can be undone, where the suggestion appears, or
  what counts in the criteria.
- Decision:
  - Study status is read-only in the API and the Library shows it as a badge. It changes in
    three ways only: opening a block (spec 4.4.5), confirming a suggested completion, and
    reopening a completed subtopic.
  - `POST /api/subtopics/<id>/complete/` completes a subtopic only while it is suggested, and
    answers 409 otherwise. `POST /api/subtopics/<id>/reopen/` moves a completed subtopic back to
    in progress, and answers 409 for any other status.
  - A subtopic is suggested only when it has at least one block, every block has `read_at`
    (D-015), and it has an attempt rated right or partial. Every attempt of the subtopic counts:
    questions and explanations, including attempts of archived questions. The content state
    (`draft` or `ready`) does not matter.
  - A re-import that unmarks a block removes the suggestion until the block is read again, and
    never changes a completed status.
  - A concept's status and a track's next step are computed on every read and never stored.
  - The suggestion appears in Study when the last block is marked read and in Practice when an
    attempt is saved.
  - Completing or reopening touches no card and records no session event.
- Why: a status anyone can set by hand would let the first month's measurement record
  completions the rules never saw. Reopening keeps a mistaken confirmation fixable without
  bringing the select back.
- Risk: a reopened subtopic that still meets the criteria is suggested again right away. Status
  values set by hand before this entry stay as they are; use mode holds no data yet (D-016).
### D-022: How the review queue fills a Bahia day

- Date: 2026-10-16. Source: review scheduling slice (S4); Diogo accepted the recommended options.
- Context: spec 4.6 sets two daily caps, retrievability order for overflow (D-011) and distinct
  cards per day (Q14), but not the initial Py-FSRS state, how the two caps combine, or when a card
  counts as due today.
- Decision:
  - Every card gets a fresh `Card()` when it is created, whatever its approval state, and the
    migration gives one to the cards that already exist. Its `card_id` is the `Flashcard` pk, so
    review logs line up with cards for the later optimizer.
  - New cards count inside the review cap and take their slots first, up to the new card cap,
    in creation order (Markdown order). Due cards fill the remaining slots by retrievability,
    ascending.
  - A card already reviewed is due today when its `due` falls before the next Bahia midnight. A
    card already reviewed today comes back only when its `due` has passed (learning and
    relearning steps) and uses no new slot.
  - "Revisões de hoje: N" counts the new and due cards still to be seen today, not those
    same-day repeats, so it never exceeds the remaining cap.
  - The queue ignores study status: completing a subtopic or a concept keeps its cards in review
    (scenario 25).
- Why: one ceiling of 20 cards keeps the daily load bounded, which is what the habit hypothesis
  needs, and reserving the new card slots keeps a backlog from freezing new material. A day-based
  due date keeps N stable through the day.
- Risk: under a long backlog, the new cards take up to 5 of the 20 slots, so the backlog drains
  more slowly. The UI never shows it (spec 4.6.4).
### D-023: Reading after D-020: read marks across a re-import, hidden answers, block order

- Date: 2026-10-16. Source: review of the study reading slice (S1) after PR #22; Diogo asked to
  carry on with the implementation. D-021 and D-022 are reserved by slices running in parallel.
- Context: D-020 marks a block read by `block_order` when its reading event is completed. Blocks
  are rebuilt on every import (D-015), so a re-import between opening and completing a block can
  give that position to other text. The reading screen also showed the "Prática" block as written,
  reference answers included. And D-020 said the spec leaves the order of out-of-order sections
  open, while spec 4.8.1 said "contract order".
- Decision:
  - Completing a reading event marks a block read only when the subtopic's content was not saved
    after the event started (`Content.updated_at <= started_at`). The event is still completed
    and still counts as a session. The reading screen fetches the blocks after starting each
    event and shows the read marks the server returns, so the text on screen is never older
    than the event. This supersedes only D-020's read mark line.
  - Reading shows the "Prática" block with its questions and without their reference answers,
    which spec 4.8.3 shows only after an attempt.
  - D-020's document order stands, as Diogo accepted it with the S1 approach. Spec 4.8.1 now says
    so and points here: a document whose known sections are out of contract order is shown as
    written.
- Why: a read mark on text that was never shown would make "all blocks read" (spec 4.4.4) true
  too early; leaving the block unread is what D-015 already does to any changed block. Document
  order keeps `block_order` equal to `Block.order`, which resuming (D-017) depends on.
- Risk: saving identical content also moves `updated_at`, so a block completed across such a save
  stays unread until it is read again.

### D-025: Review screen: keyboard shortcuts, one event per card shown, manual cards

- Date: 2026-10-16. Source: review session slice (S5); the recommended options, under Diogo's
  implementation-first rule. D-026 is reserved for the home screen slice.
- Context: `docs/plan.md` leaves the review shortcuts open. Spec 3.2 lists the review session as
  an activity with no subject (D-017), but does not say what one review activity is or when it
  starts and ends. Spec Q6 allows a manual card on a subtopic or a concept, but not where it is
  created.
- Decision:
  - Shortcuts: Space or Enter shows the answer, then 1 is errei, 2 parcial and 3 acertei, in the
    order of the buttons, and each button shows its key. They work anywhere on the review screen
    except while typing in a field or with Alt, Ctrl or Meta held.
  - One `review_session` event per card shown. Showing a card starts it through
    `POST /api/events/` (D-020). `POST /api/reviews/` takes that event, the card and the rating,
    rates the card through `rate_card` and completes the event in one transaction. The S4
    endpoint `POST /api/flashcards/<id>/rate/` is removed, so no review exists without a
    completed event, as D-021 does for attempts.
  - After each rating the screen asks for the queue again, so a failed card comes back once its
    `due` passes, as a new showing with a new event.
  - Manual cards are created on the review screen through `POST /api/flashcards/`. A concept is
    required and a subtopic optional: with a subtopic the card belongs to it, otherwise to the
    concept (D-018). They are created active, with an empty label and a fresh Py-FSRS card
    (D-022). This slice has no edit or delete for them.
- Why: an event per card has the same grain as reading (one block, D-020) and practice (one
  answer, D-021): rating one card makes the day a session, and a session left halfway keeps what
  was done. The number keys follow Anki, which Diogo used before (spec 1), and sit under one
  hand. Creating cards where they are reviewed keeps the cycle in one place.
- Risk: a card shown and left without a rating stays as an event without `completed_at`, which
  the metric reads as abandoned, as with reading. A full day makes about 20 review events, which
  the metric counts once per day (spec 4.11.2). A card created while another is on screen shows
  up only after the next rating, so the card on screen and its event are never swapped.

### D-026: The home screen records each load, and a return session is a day's first 5 reviews

- Date: 2026-10-16. Source: home slice (S6); recommended options, taken under the implementation
  first rule.
- Context: spec 4.5.2 and 4.7 say what the home screen and the return session show, and Q2 that
  each load of the home screen records `app_opened`. The spec does not say how a load records the
  event, when a return session ends, how its 5 reviews reach the review screen, or which "next
  step" the home screen shows when there are several tracks.
- Decision:
  - The home screen loads through `POST /api/home/`, which records `app_opened` and returns what
    the screen shows in one request. It is a POST because it writes a history row; the screen
    sends it once per load, also under React's StrictMode.
  - A return session is on when at least 3 full Bahia days passed between the last day with a
    session and today. Before the first session ever, there is none. It ends when 5 distinct
    cards were reviewed today, or when an activity other than a card review is completed today
    (reading a block, an attempt). Card reviews end it by count, because each card rated
    completes its own review event (D-025). From then on the normal caps apply, with the reviews
    already done counting toward them (Q15).
  - During a return session the review cap is 5 (or the configured cap, when lower) for the home
    screen's N and for `GET /api/reviews/today/`, so the review screen gets at most 5 cards. New
    cards still take their slots first inside that cap (D-022).
  - The return session shows only "continue where I stopped" and the reviews; the next steps
    are left out, and no text mentions the absence.
  - "Continue where I stopped" is the latest reading event and the block reading resumes at
    (D-017). The next step is shown for each track that has one, with the concept's first
    subtopic not completed, or the Biblioteca when the concept has no subtopic yet.
  - "Início" is the default page.
- Why: one request ties the record to the load, so the Q2 metric cannot miss a load the screen
  showed. The return session is derived from events and review logs on every read, so it needs
  no stored state. One next step per track keeps programming and English both one click away
  without ranking them.
- Risk: reading a block before reviewing ends the return session, and that day's reviews then
  follow the normal cap. With fewer than 5 cards to review, the home screen keeps the return
  layout until another activity is completed that day.

### D-028: Backup layout, and how the 30-day retention reaches the vault

- Date: 2026-10-16. Source: backup slice (S7), on top of D-019; the vault side was left to S7.
- Context: D-019 puts the exports in a staging folder on `C:` and copies them to the vault with
  `robocopy`, but rules out a bare `robocopy /MIR`, which would wipe the vault folder if its path
  were wrong. The spec does not fix how an export is laid out either.
- Decision:
  - `python manage.py backup` writes one folder per export, `athenas-<UTC stamp>`, holding
    `data.json` (`dumpdata` of the three apps, the input of `loaddata`) and
    `markdown/<area>/<concept>/<subtopic>.md`, each name `<pk>-<slug>`. The folder is written
    as `.partial` and renamed when complete. It exports when the newest export is older than
    24 h (or with `--force`) and removes staging exports older than 30 days, never the newest.
  - `scripts/backup.py run` copies the staging folder with `robocopy /E`, which never deletes,
    excluding `*.partial` and the log. After a successful copy it deletes, inside the vault
    folder only, the subfolders whose name matches `athenas-<stamp>` exactly and whose stamp is
    older than 30 days, never the newest one. The age comes from the name, not from file dates,
    which Drive may change.
  - The vault folder must already exist: the task never creates it, so a wrong path or an
    unmounted `G:` is logged as a failure. Each run appends to `backup.log` in the staging folder
    and exits non-zero on failure.
  - `scripts/backup.py register` creates the hourly task with `schtasks`, under `pythonw` so no
    window opens. Restore is `flush` and then `loaddata` (README, Backup and restore).
- Why: a delete limited to an exact name pattern inside the configured folder can only remove
  old exports, whatever the path holds. Deriving the age from the name keeps both sides on the
  same 30-day rule.
- Risk: exports dropped into the vault by hand under the same name pattern age out like the
  others. If Drive changes file dates, `robocopy` recopies unchanged files every hour; the log
  then shows an odd copy exit code (1 or 3) on every run, not only after an export.


### D-027: Agent-written tests in `backend/tests/` count as v1 acceptance tests

- Date: 2026-10-17. Source: Diogo picked "Aceitar" on the card "Aceitar os testes do agente em
  backend/tests como critério de pronto da v1?", after the implementation first rule of
  2026-10-16 (`AGENTS.md`, How work flows).
- Context: spec 6.6 and 7 make the core acceptance tests in `tests/acceptance/`, written by
  Diogo, part of v1 done. Since 2026-10-16 the agent writes the core scenario tests in
  `backend/tests/` instead, so scenarios 1 to 15 and 19 to 25 had tests only there, and the
  spec contradicted the `v0.1.0` tag.
- Decision:
  - For v1, a spec section 8 scenario counts as covered when a test named after it passes,
    either in `tests/acceptance/` (Diogo's) or in `backend/tests/` (written by the agent).
    Both run in `make test` and in CI.
  - `docs/acceptance-coverage.md` maps each scenario to its tests. It was checked scenario by
    scenario before the tag, and the missing parts got tests in the same PR.
  - `tests/acceptance/` stays Diogo's: agents never create or edit files there.
- Why: the tag does not wait on Diogo rewriting by hand tests that already pass, and the core
  rules stay under automated tests from day 1.
- Cost: in `backend/tests/` the agent checks its own reading of the spec. The same reading wrote
  the code and the test, so a misread rule passes both and only real use shows it. The coverage
  map lowers that risk, since each test was read against the spec rule and not only its name,
  but it is the same reader. Diogo can still move or rewrite any scenario into
  `tests/acceptance/`; a rule found misread in use gets a fix and a new entry here.

### D-030: Claude Code builds a theme outside the app and saves it through the local API

- Date: 2026-10-17. Source: Diogo asked for Claude to fill a theme's roadmap, contents and
  questions, his only role being to name the theme, and picked "Na v1" on the card "Quando
  colocar a geração de conteúdo pela IA no Athenas?". This is the path the thread "Integração
  com o Claude" recommended. After asking for a screen in the app and for other AIs, he picked
  "Começar já" on the card "Escolher se o dia 1 começa já com o Claude Code ou espera a tela do
  Athenas?". D-029 stays reserved for the day 1 date.
- Context: spec 2.2 keeps integrated AI, automatic generation of activities and structured
  import out of v1, while spec 1 and D-001 already let Claude prepare content outside the app,
  and spec 4.1 makes the Markdown template its prompt. The REST API already creates areas,
  tracks, concepts, steps and subtopics, and saves a subtopic's Markdown through the import the
  screen uses (4.2). Inside the app, the documented path is an API key (Max plans include
  monthly API credits, Pro does not), the `anthropic` package and requests that run for
  minutes. Running Claude Code from the backend on Diogo's own subscription token
  (`claude setup-token`) is a case the Claude Code docs do not cover, and it stops working once
  `--bare`, which ignores that token, becomes the default for `claude -p`, as they announce.
- Decision:
  - The `athenas-tema` skill for Claude Code turns one line (a theme, optionally `: goal`) into
    `temas/<slug>/` (git-ignored): `tema.json` with the area, the track, and its concepts and
    subtopics in study order, plus one contract Markdown per subtopic, written from pages Claude
    opened in that run and listed under Fontes.
  - `scripts/theme.py check` validates the folder with the app's own parser: no errors or
    warnings, the ten headings and no other, state ready, `nivel` set, a URL under Fontes.
    `push` runs the same check, then creates through the existing endpoints only what is
    missing and saves each Markdown. On an instance with no concept it writes nothing without
    `--first`, because the first concept in use mode starts day 1 (D-016). Content that differs
    from what the app holds is re-imported only with `--replace`, which keeps history by label
    (spec 4.2.6).
  - Generated cards enter pending like any Markdown card (D-007, spec 4.3). Neither the skill
    nor the script approves, rejects, edits or deletes anything.
  - The generated Markdown carries `origem: claude` in its frontmatter. The parser ignores the
    key and the raw Markdown keeps it, so the backup and the day 28 verdict can tell generated
    content apart. (Superseded in part by D-032: the parser now reads the key and the app stores
    and shows it.)
  - Day 1 starts with this path, and spec 2.2 stays as it is in this change. A "Novo tema"
    screen follows during the month (S10 in `docs/plan.md`): it builds the request for any AI,
    Gemini Notebook (formerly NotebookLM) included, since that one has no API for personal
    accounts, and imports the pasted answer. S10 brings structured import into v1 and records it
    in its own entry. Calling an AI from the app stays out of v1; a button for it on that screen
    is left for after day 28.
- Why: it needs no API key, no new dependency and no app code, so day 1 waits only for this
  change. Claude Code runs on Diogo's subscription, opens the sources itself and repeats the
  check until every file passes, a loop that a single API call from the backend would have to
  rebuild. The app's parser stays the only gate, so generated content meets the same contract as
  pasted content.
- Risk: until S10, the theme is typed in Claude Code, not in the app. Diogo is learning the
  theme, so he cannot always judge a card when he approves it; the Fontes list and the `[!ia]`
  callouts are how he checks one. A large theme uses a visible part of the plan's usage window,
  and `push` resumes where a run stopped. The month measures studying with generated content,
  which the day 28 verdict states with the features of the month (D-010).

### D-029: Day 1 is 2026-10-17, on release `v0.1.1`

- Date: 2026-10-17. Source: release R1 of `docs/plan.md`, run with Diogo; the date follows from
  D-016.
- Context: D-016 sets day 1 as the first day use mode runs a tag that passes the M1 gate, with at
  least one concept registered. D-010 asks for the date to be recorded when it happens.
- Decision:
  - Day 1 is Saturday 2026-10-17 (Bahia). Use mode runs `v0.1.1` (770aabc: the M1 slices, the
    library and roadmap polish and the theme skill of D-030). `v0.1.0` (ee91aa8) was tagged and
    run the same day with an empty database and was replaced before any concept existed.
  - The first concepts came from `scripts/theme.py push --first` at 14:03 UTC (11:03 Bahia):
    the track "Engenharia de Agentes de IA", 5 concepts, 11 subtopics, 63 cards pending
    approval. Diogo reviewed the same folder on a disposable copy before it was pushed.
  - The D-010 window, in Bahia days: block 1 from 2026-10-17 to 10-23, block 2 from 10-24 to
    10-30, block 3 from 10-31 to 11-06, block 4 from 11-07 to 11-13. Day 28 is 2026-11-13.
  - Use mode runs from a separate checkout on a tag (`Projetos\Athenas-use`), not from the dev
    clone, so dev work never stops it. The hourly backup task points at that checkout, and
    exports reach the vault folder `07 - Assets\Athenas backup`.
- Release checklist (plan section 5), all before day 1:
  - `make lint` and `make test` on 770aabc: "All checks passed!", "101 passed", exit 0.
  - The by-hand step (study, practice and review) ran on a disposable copy of the tag, never in
    use mode, because its first concept would have started day 1 with test data.
  - Restore drill, twice, each on a separate disposable database with the README commands
    (`backup --force`, `flush`, `loaddata`): first with synthetic data on ee91aa8, then with the
    export of the reviewed theme (257 objects). Every table count matched before and after.
- Why: the verdict needs a fixed start, and recording how day 1 began keeps the first theme's
  origin and the checks behind the tag in one place.
- Risk: the first theme was saved before the parser kept `origem: claude` (D-030 says the raw
  Markdown keeps the key, so the origin can be recovered from it). Restore commands with
  `/backup/...` paths fail in Git Bash, which rewrites them; run them from PowerShell.

### D-031: The reading screen renders Markdown in-house and uses the sheet's full width

- Date: 2026-10-17. Source: Diogo, on day 1, reading a generated subtopic: the text showed
  `**` around bold words, and the sheet left half of a wide screen to the background.
- Decision:
  - Text segments render the Markdown subset study content uses: paragraphs with their line
    breaks, `###` headings, lists (nested), quotes as a highlighted card, tables, rules, images
    on their own line with the title or alt text as caption, and inline bold, italic, code,
    links and bare URLs. `frontend/src/ui/Markdown.jsx` builds React elements, so no HTML from
    the text reaches the page; links and images accept only `http(s)` or same-site paths.
  - No Markdown library: the subset is small, and a new production dependency needs Diogo's ok.
    Anything outside the subset shows as plain text, as it did before.
  - On the reading screen the sheet takes the whole width. The text column stays near 70
    characters per line; the extra space holds an outline of the blocks (each one opens that
    block, like Anterior) and, beside the text, the subtopic's sources and a Praticar link.
    Below 1600 px the sources go under the text.
- Why: lines much longer than about 75 characters read worse, so the width goes to navigation
  and support instead of to the text.
- Cost: images in the content are only as good as their source; storing them is the job of the
  content format, not of this screen. Practice and review still show their text as plain text.

### D-032: The app keeps and shows who wrote a subtopic's text

- Date: 2026-10-17. Source: the project goal Diogo updated on 2026-10-17 says agent-generated
  content carries `origem: claude`, Markdown cards stay pending until he approves them, and AI
  text never passes as correct because it reads well. D-030 left the key only in the raw
  Markdown, so the app showed a generated card exactly like one he pasted himself.
- Decision:
  - The frontmatter key `origem` (spec 4.1) is optional. The parser reads it lowercased and
    `Content.generated_by` stores it; no key means Diogo's own text and stores empty. A value
    over 30 characters is cut, with a warning, never dropped, so generated text never turns
    into Diogo's by accident.
  - The origin belongs to the document, not to each question or card, and follows the last
    save: re-importing without the key claims the text as Diogo's. Questions and cards read it
    from their subtopic's content.
  - `Flashcard.origin` keeps meaning how a card entered (`markdown` or `manual`); it is not
    reused for who wrote it.
  - The app shows a "Gerado por <origem>" badge in the import preview, above the pending card
    being approved, at the top of the reading, and next to the reference answer in practice.
  - `scripts/theme.py check` fails a file without `origem`, so the skill cannot push unmarked
    content.
  - The migration fills `generated_by` from the raw Markdown already saved, which keeps its
    frontmatter verbatim, so content pushed before this change is recovered. It writes only
    that column.
- Why: the mark sits where Diogo judges the text (approving a card, comparing an attempt with
  the reference answer), and one field on `Content` covers questions and cards without a
  migration on history tables. The same field serves S10's other AIs (`origem: gemini`).
- Cost: a suspended card or an archived question keeps showing its subtopic's current origin,
  not the one of the text it held when it left the Markdown. History of past origins is not
  kept, the same way past Markdown versions are not.

### D-033: Images in a subtopic live in the database, cited by name and credited

- Date: 2026-10-17. Source: Diogo, on day 1, asked that concepts come with images that help
  explain them, as a chat assistant shows them, instead of plain text only. The project goal
  says AI-made content never passes as correct because it looks good.
- Decision:
  - Two kinds of image. A diagram an AI drew (an SVG by hand, for a process or an
    architecture) carries `generated_by: claude` and the D-032 badge under it. A real picture
    comes from Wikimedia Commons with its page, author and license (public domain, CC0, CC BY
    or CC BY-SA); `scripts/theme.py download` fetches only from Wikimedia.
  - The bytes live in the database (`Image`, one row per unique name), not in files beside it:
    the app works offline, nothing is hotlinked, and the daily export (`dumpdata`, D-028)
    carries and restores them with no change to the backup or the restore. An image over
    512 KB is refused, and the type comes from the bytes (PNG, JPEG, GIF, WebP, SVG), never
    from the client.
  - The Markdown cites an image with a line of its own,
    `![legenda](/api/images/<nome>/ "título opcional")`, the syntax D-031's renderer already
    shows. The reading API cuts that line into an `image` segment with the caption and the
    credit, kept with the image so the text can never leave it out. A name with no stored
    image warns in the preview and shows only its caption.
  - The image is served with `Content-Security-Policy: default-src 'none'` and `nosniff`, so an
    SVG opened on its own runs no script and fetches nothing.
  - D-015's read mark compares a block's body without its image lines and blank lines.
    Adding images to a theme Diogo is already reading keeps his read marks and his position,
    since block order does not change. Any other text change still unmarks the block.
  - Images reach the app through `PUT /api/images/<nome>/` (JSON, base64), which
    `scripts/theme.py push` calls only for images the app lacks, or all of them with
    `--replace`. There is no upload screen in v1.
- Why: the database keeps backup and restore as they are, which the restore drill already
  covers. Files beside it would need a volume, a copy step in `scripts/backup.py` and a new
  restore drill. Credit stored with the image follows it to every text that cites it.
- Cost: every daily export repeats every image as base64. Measured on a dev export: three 960px
  Commons photos and one diagram added 540 KB (6 KB without them). A theme with ten photos adds
  about 2 MB per export, about 60 MB across the 30 exports the vault keeps. If that grows too
  much, the fix is writing images once into a shared folder of the export, not changing the
  Markdown. Images are not versioned: replacing one changes it in every text that cites it.

### D-034: Início, Roadmap, reading and Revisões follow Diogo's new mockups

- Date: 2026-10-17. Source: Diogo sent four mockups (Início, Roadmap, a subtopic's reading,
  Revisões) as the new design to implement. The project goal puts stability first during the
  month of use, so the screens change and the data and endpoints do not.
- Decision:
  - Início and Roadmap each sit on a sunset panorama from Diogo's frontend kit (`home-sunset`,
    `roadmap-sunset`, with 1280px copies up to 1440px windows), which runs under the navigation
    and fades to marble on the left. The opening lines sit on that light side and the rest on
    one opaque board. The out-of-focus bushes at the bottom right are cut from the same
    photograph into a full-size transparent layer drawn in front of the page, so they overlap
    the board as in the mockups; menus still open above them. Every other screen is plain
    marble with the kit's faint olive-leaf shadow in the top corner, behind the navigation only:
    the garden scene, its sheet and the old `home.webp` are removed.
    The board is drawn as a marble slab, as in the mockups: its top right corner steps down
    into a band that runs off the right edge of the window, and its thickness shows under it
    (CSS only: a pseudo-element with concave fillets and solid offset shadows, no image).
  - Roadmap picks the track with a select instead of tabs and shows the track as a numbered line
    on the board. Moving and removing a step, adding a concept and removing the track move into
    small menus (`Popover`); "Criar trilha" is the existing form.
  - Reading: "Bloco anterior" and "Próximo bloco" open a block without marking it read, as the
    outline already did. The sheet's own button marks the block read and opens the next one; on
    a block already read it says "Confirmar releitura". The outline becomes the block picker. The
    support column holds Praticar, the subtopic's "Marcado para revisar" flag (the same
    `review_needed` the Biblioteca edits, saved through `PATCH /api/subtopics/<id>/`, the box
    changing only after the save) and the sources. This replaces D-031's layout (outline at the
    left, sources and Praticar at the right).
  - Paragraphs in study text flow: lines wrapped in the Markdown source join with a space, as
    in CommonMark, and a line ending in two spaces or a backslash keeps its break. This
    replaces D-031's "paragraphs with their line breaks", which broke every hard-wrapped
    paragraph mid-sentence. Sources are lists in the contract, so they keep one per line.
  - Revisões keeps the manual card form behind a "Novo cartão" button, and the empty state
    sends back to Início.
  - The visual scale follows the mockups, not the v1 guide: type is larger and grows with the
    window (study text 18 to 24px, UI 16 to 18px), titles are near black and the opening
    lines, page titles and the open block use Cormorant Garamond 700 (a second weight file of
    the same family). Study text, the navigation and the breadcrumb links are navy ink; the
    primary action and the current page are forest green; the navigation line, its rings and
    the open block's tab are copper; the current crumb and the next block are rust. Button
    labels are regular weight, the owl emblem is copper, and the success and info tints are
    more saturated. Every text pair stays at 4.5:1 or more (`tokens.css` lists each ratio).
  - "Praticar este subtema" stays a link with a chevron to the right; the mockup draws it as a
    disclosure, but nothing would open under it.
  - Left out of the mockups: the "Objetivo" bookmark at the top right of Início (no function
    behind it yet), the leaf shadow on the internal screens and the new landscape on Início and
    Roadmap (neither file is in the repo; the current panorama stands in).
- Why: one screen per daily action, with the next step as the largest thing on it, is what the
  mockups ask for and what "começar e retomar sem esforço" needs.
- Cost: a long track scrolls sideways on the board. Text on the panorama depends on the fade:
  a new landscape needs a light left side, or its opening lines need a panel.

### D-037: Configurações edits the Settings row, and the pomodoro lives in the navigation

- Date: 2026-10-21. Source: slice S9 of `docs/plan.md` (M2). Spec 3.2 lists the settings and
  spec 4.9 the pomodoro, but neither says where they live, what values are accepted or what
  happens when a phase ends. D-035, D-036, D-038 and D-039 are held by the other M2 slices
  opened the same day.
- Decision:
  - "Configurações" is the secondary item at the foot of the navigation (design system 4) and
    opens `#/configuracoes`: one form with the review cap, the new card cap, the desired
    retention as a whole percentage and the two pomodoro durations, saved by one "Salvar"
    through the existing `PATCH /api/settings/`. "Configurações salvas." appears only after
    the answer; a refused save marks each field with the API's message and moves the focus to
    the first one.
  - The API takes a review cap from 1 to 200, a new card cap from 0 to 200 and never above the
    review cap (new cards take their slots inside it, D-022, so a larger number would do
    nothing), a desired retention from 0.70 to 0.97, a focus from 1 to 180 minutes and a break
    from 1 to 60, each refused with "Use um valor entre ..." in the field. Above 0.97 the
    number of reviews grows very fast; below 0.70 more than 30% of the cards would be
    forgotten by their review. The model's wider bounds stay, so no migration. A new card cap
    of 0 stops new cards; a review cap of 0 is refused, since it would empty the queue with no
    word on the screen. The cap rules themselves (spec 4.6, D-022, D-026) do not change: the
    queue reads the new value on its next build, so scenario 9 holds, and the return session
    keeps its 5.
  - A new desired retention counts from each card's next rating. Stored due dates are never
    rewritten (D-011), and the queue's order does not depend on it (retrievability does not).
  - The pomodoro sits in the navigation, above Configurações: "Iniciar foco", then the phase
    and the time left with "Parar", one button that keeps the focus when its label changes.
    The durations are read at each start, so a change counts from the next focus. When the
    focus ends its break starts on its own, and when the break ends the timer stops; there is
    no loop, pause or count of rounds. Each end gives one notice in the bottom right corner,
    in a live region, that never takes the focus and stays until closed or replaced: "Fim do
    foco. Pausa de N min." and "Fim da pausa.", which is also the notice when a sleep skipped
    the whole break. No sound and no browser notification. A button in the navigation leaves
    the folded menu open; only a link closes it.
  - The timer is an end time in `localStorage`, so it survives a reload or a closed tab and
    stays right in a background tab. A phase that ended while the app was closed settles with
    no notice: a running break shows as a break, and a timer whose break also passed is gone.
    Open tabs share it: a start or a stop in one shows in the others, and each tab gives its
    own notice when a phase ends.
  - On the screens without a panorama (reading, practice, reviews and the rest) the page gets
    room at its end while a notice shows, so the last action can be scrolled out from under
    it.
  - The pomodoro records no `SessionEvent`: it is not a study activity (spec 3.1, Activity) and
    the day 28 metric does not read it.
  - Over the panoramas of Início and Roadmap the foot of the navigation sits on the board's
    color, so its text never lies on the photograph (design system 6).
- Why: spec 4.9 asks for a timer that never blocks studying and never competes with the
  content; the navigation is beside every screen and outside the content, and a notice that
  does not take the focus leaves the reading or the answer where it was. Bounds on the caps
  catch a typo (2000 instead of 20) before it fills a day.
- Cost: with the window under 1200 px the navigation folds behind "Menu", so the time left is
  hidden until it opens; the notice still shows. Until it is closed, the notice covers what
  sits in the bottom right corner of the window: on a study screen that can be scrolled away,
  on Início and Roadmap it cannot.
