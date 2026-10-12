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
