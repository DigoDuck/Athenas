# Athenas v1 specification

Status: draft for review, open questions answered on 2026-10-12. Source: `Athenas.md` (project Library, 2026-10-12). Where the
"Decisões do interrogatório" table and the original briefing disagree, the table wins.
Once merged, this file and `DECISIONS.md` are the source of truth; in a conflict, the repo
wins over the Library.

References in brackets point to the source:

- `[D1]`..`[D9]`: interrogation decisions; `[D10]`: the day 28 rule. All recorded in `DECISIONS.md`.
- `[R1]`..`[R7]`: review rules ("Regras de revisão").
- `[C1]`..`[C5]`: content contract rules ("Contrato do conteúdo").
- `[V1]`: the "V1" table; `[Medição]`: the "Medição e veredito" section; `[briefing]`: the original
  briefing, used only where the decisions table is silent.
- `[Q1]`..`[Q17]`: questions the source left open, answered by Diogo on 2026-10-12. Section 9
  lists each answer.

## 1. Purpose

Athenas is a personal study site for one person (Diogo), used for programming and English.
It tests one hypothesis: with studying, practicing and reviewing in a single place, studying
becomes a habit. The previous system (Obsidian templates, NotebookLM, Anki) stopped after one
session, and the stated cause was tools spread across places.

It serves four actions: know what to study, start with little effort, check what was
understood, and review what needs reinforcing.

In the daily routine, studying, practicing and reviewing happen only in Athenas. External
tools (NotebookLM, Claude) are used only to prepare content `[D1]`.

## 2. Scope

### 2.1 In scope for v1

Each item at its minimum `[D3]`:

| Item | v1 minimum |
| --- | --- |
| Organization | Areas, concepts and subtopics. Level, perceived difficulty, study status and review need as separate fields. |
| Roadmap | Ordered list per track, with status and next step. The home screen opens on "continue where I stopped". |
| Content | Paste the Markdown template, see a preview, save incomplete. |
| Study | Reading in blocks, and notebook mode. |
| Practice | "Explain in my words" and questions with a reference answer. Self-assessment: right, partial, wrong. Attempts saved. |
| Review | Manual flashcards and flashcards from the Markdown, Py-FSRS, daily caps. |
| Pomodoro | Adjustable focus and break, one discreet notice. |
| Backup | Daily export in JSON and Markdown to the vault folder. |
| Measurement | Session event table, no screen of its own. |

### 2.2 Out of scope for v1

Integrated AI, automatic generation of activities, structured import (except the "Novo tema"
screen, which imports a pasted AI answer, `DECISIONS.md` D-040), history-based
recommendations, mobile screens, deploy, login, drag-to-reorder, prerequisite graphs,
configurable completion criteria, rich text editor, restore through the UI, metrics dashboard,
folders deeper than three levels, multi-user. Any change to this list needs Diogo's ok.

### 2.3 Constraints

- Tool first; portfolio work only after the first month of use. Standard stack, no
  exceptions: Django 5 + DRF + Py-FSRS, React + Vite, PostgreSQL, Docker Compose `[D2]`.
- Desktop only, local, with use mode always on, data separate from development, and backup to
  the vault `[D8]`.
- Automated tests only for the core (section 7) until the end of the first month of use.
- Does not use ZEUZ `[D9]`.

## 3. Domain

### 3.1 Glossary

| Term (EN) | Term (PT, as Diogo uses it) | Meaning |
| --- | --- | --- |
| Area | Área | Top-level field of study, such as Programação or Inglês. |
| Concept | Conceito | A unit of learning inside an area, such as Orientação a objetos. Has a central page listing its subtopics. Can exist before any content (planning). |
| Subtopic | Subtema | A part of a concept, such as Encapsulamento. Holds exactly one Markdown document. |
| Track | Trilha | An ordered sequence of concepts: the roadmap. |
| Step | Etapa | One concept's position in a track. |
| Content | Conteúdo | The Markdown document of a subtopic, parsed into blocks. |
| Block | Bloco | One `##` section of the content. |
| Practice question | Pergunta | A question labeled `P<n>` with an optional reference answer. |
| Explanation | Explicar com minhas palavras | Free text where Diogo explains a subtopic as if teaching it. |
| Attempt | Tentativa | One saved answer to a question or one explanation, with a self-assessment. |
| Flashcard | Cartão | Front and back. Either manual or declared in the Markdown with label `C<n>`. |
| Review | Revisão | One rating of one flashcard, fed to Py-FSRS. |
| Activity | Atividade | A unit of work recorded for measurement: reading, notebook, question, explanation, review session. |
| Session | Sessão | At least one completed activity `[Medição]`, that is, an event with `completed_at` set `[Q1]`. The success metric counts distinct days with a session `[D10]`. |
| AI complement | Complemento da IA | A `> [!ia]` callout in the content. |

### 3.2 Entities

```
Area 1──* Concept 1──* Subtopic 1──1 Content 1──* Block
                         │                      ├──* PracticeQuestion 1──* Attempt
                         │                      └──* Flashcard (from Markdown) 1──* ReviewLog
                         ├──* Attempt (explanation)
                         └──* Flashcard (manual) 1──* ReviewLog
Track 1──* Step *──1 Concept
SessionEvent (standalone, references the activity's subject when there is one)
Settings (single row)
```

**Area**: name. Unique by name.

**Concept**: area, name, optional objective. A concept may have no subtopics and no content
yet (planned) `[briefing]`.

**Subtopic**: concept, name, order inside the concept, and the four classification fields,
which are independent of each other `[briefing]`:

| Field | Values | Set by |
| --- | --- | --- |
| Level | iniciante, intermediário, avançado, especialista | Markdown frontmatter `nivel`, editable |
| Perceived difficulty | easy, hard, unset | Diogo, any time |
| Study status | not started, in progress, completed | Rules in 4.4 |
| Review need | flag on or off | Diogo, any time `[Q5]` |

A completed subtopic can still need review; a beginner subtopic can be hard. The UI never
merges these fields into one indicator. Next to the review need flag, the UI shows an
automatic "has cards due" indicator; the two are never merged `[Q5]`.

Concepts do not store these fields. A concept's study status is derived from its subtopics
(4.4) `[Q4]`.

**Track**: name, ordered list of steps. Each step points to one concept. Order is changed
without drag and drop (for example, move up and move down).

**Content**: the raw Markdown as pasted (always kept), the parsed blocks, a state:
`draft` or `ready` (rules in 4.2), and who generated the text (frontmatter `origem`, empty for
Diogo's own text, `DECISIONS.md` D-032).

**Block**: kind (one of the known headings in 4.1, or `extra`), heading text, body, order.

**Image**: a picture a block shows, stored in the app with its name, its bytes and its credit:
who drew it (an AI) or where it came from (page, author, license) (`DECISIONS.md` D-033).

**PracticeQuestion**: subtopic, label (`P1`, `P2`, ...), prompt, reference answer, archived
flag. The label is the identity `[C2]`.

**Attempt**: subtopic, kind (`question` or `explanation`), question (when kind is
`question`), text, self-assessment (`right`, `partial`, `wrong`), created at. Attempts are
never edited or deleted by the app; they are kept for comparison between attempts.

**Flashcard**: subtopic (Markdown cards), or subtopic or concept (manual cards) `[Q6]`,
origin (`markdown` or `manual`), label (`C<n>` for Markdown cards, empty for manual), front,
back, approval state, and the Py-FSRS card state (stored as given by the library, in UTC). The
field layout is in `DECISIONS.md` D-018.

| Approval state | Meaning | In the review queue |
| --- | --- | --- |
| pending | Declared in the Markdown, not yet reviewed by Diogo | No |
| active | Approved, or created manually | Yes |
| suspended | Its label was removed from the Markdown | No |
| rejected | Diogo refused it during approval `[Q7]` | No |

**ReviewLog**: flashcard, rating (`again`, `hard`, `good`), reviewed at (UTC), and the
Py-FSRS review log as given by the library.

**SessionEvent**: one row per activity: started at, ended at, `completed_at`, activity type,
and the subject (subtopic, question or review session) when there is one `[Medição]`, never a
block (`DECISIONS.md` D-017).
`completed_at` is set when the activity is finished and stays empty when it is abandoned (for
example, the browser was closed) `[Q1]`. An `app_opened` event is recorded on each load of the
home screen, so the "time between opening and starting" metric can be computed `[Q2]`.

**Settings**: daily review cap (default 20), daily new card cap (default 5), desired retention
(default 0.9, the library's default) `[Q10]`, pomodoro focus and break durations. The backup
folders live in `.env.use`, not here (`DECISIONS.md` D-019).

### 3.3 Invariants

1. Every subtopic belongs to exactly one concept; every concept to exactly one area.
2. Labels are unique per subtopic: no two questions share a `P` label, no two cards share a
   `C` label.
3. A pending, suspended or rejected card is never shown in a review session and never
   counted in "reviews today".
4. Py-FSRS works in UTC. Every "day" in the product (caps, return session, measurement)
   is a calendar day in `America/Bahia` (UTC-3, no daylight saving) `[R7]`, starting at
   midnight `[Q9]`.
5. Rating or editing a card never erases its review history. Editing question text never
   erases its attempts `[C2]`.

## 4. Behavior

### 4.1 Content contract

One Markdown document per subtopic `[D6]`. The same file serves as the prompt template for
NotebookLM and Claude and as the export format for the vault.

```markdown
---
area: Programação
conceito: Orientação a objetos
subtema: Encapsulamento
nivel: iniciante
origem: claude
---

## Objetivo
## Pré-requisitos
## Ideia central
## Explicação
## Exemplo
## Confusões comuns
## Prática
### P1: Qual problema o encapsulamento resolve?
Resposta de referência: ...
## Resumo para o caderno
## Fontes
## Flashcards
- C1: O que o encapsulamento esconde? :: O estado interno do objeto; o acesso passa por métodos.

> [!ia] Complemento sugerido pela IA
> Texto do complemento. Fonte: <link verificável>
```

Headings are matched by their Portuguese text exactly as above. They are part of the contract,
not UI copy. `origem` is optional: it names the AI that wrote the text, and Diogo's own text has
none (`DECISIONS.md` D-032). An image is a line of its own,
`![<legenda>](/api/images/<nome>/ "<título opcional>")`, naming an image stored in the app
(`DECISIONS.md` D-033).

### 4.2 Import rules

1. Diogo pastes the Markdown, sees a preview of the parsed blocks, questions, cards and
   warnings, then saves. Saving incomplete content is allowed.
2. Content is `ready` only when it has a non-empty "Ideia central" and at least one question
   under "Prática" `[C1]`. A question without a reference answer does not count `[Q11]`.
   Otherwise it is saved as `draft`.
3. A `##` heading not in the contract becomes an `extra` block, kept in its original
   position. Content is never discarded `[C3]`. Text before the first `##` becomes an `extra`
   block with an empty heading (`DECISIONS.md` D-014).
4. Questions are `### P<n>: <prompt>` under "Prática", followed by an optional line
   starting with `Resposta de referência:`.
5. Cards are list items `- C<n>: <front> :: <back>` under "Flashcards".
6. On re-import of the same subtopic, identity follows the label `[C2]`:
   - Same label, changed text: the text is updated; attempts and review history are kept.
   - Label no longer present: the question is archived (its attempts are kept), the card is
     suspended.
   - New label: a new question, or a new card in `pending` `[C5]`.
   - A removed label that comes back restores the archived question or the suspended card,
     with its history `[Q8]`.
7. Duplicate labels in one document block the save, with a message naming the label.
8. A `[!ia]` callout without a source is shown marked "complemento sem fonte" `[C4]`. A
   source is a `Fonte:` followed by a URL `[Q12]`.
9. If the frontmatter `area`, `conceito` or `subtema` does not match the subtopic the
   Markdown is being saved into, the preview shows a warning and the save goes into the
   subtopic being edited `[Q13]`.
10. Content with an `origem` shows "Gerado por <origem>" in the preview, while its pending
    cards are approved, in the reading and next to each reference answer (`DECISIONS.md`
    D-032).
11. An image line shows the stored image with its caption and credit. A name with no stored
    image shows a warning in the preview and its caption in the reading. Adding, moving or
    removing an image line keeps a block's read mark (`DECISIONS.md` D-033).
12. The "Novo tema" screen builds a request for any AI and imports its pasted answer: one
    document per subtopic, each named by its frontmatter, into the track chosen on the screen.
    It creates only what is missing, never changes a subtopic that already has text, marks every
    document with the AI named on the screen and, like any import, leaves every card pending
    (`DECISIONS.md` D-040).

### 4.3 Pending card approval

1. Cards declared in the Markdown enter as `pending`, outside the review queue `[D7]`.
2. Approval is one card at a time, with keyboard shortcuts. There is no "approve all" `[C5]`.
3. An approved card becomes `active` and new; the daily new card cap applies to it `[C5]`.
4. Diogo can also reject a pending card. A rejected label stays rejected on later re-imports
   until it is removed from the Markdown and added again, which makes it pending `[Q7]`.
5. Manual cards are created `active` (they are Diogo's own and need no approval).

### 4.4 Study status and completion

1. Study status values: not started, in progress, completed `[briefing]`.
2. The app may suggest completion; the decision is always Diogo's `[briefing]`.
3. Completing a step ends that study cycle. Reviews stay available afterwards `[briefing]`.
4. Configurable completion criteria are out of scope `[V1]`, so v1 has fixed suggestion
   criteria `[Q3]`:
   - A subtopic is suggested complete when all its blocks were read and it has at least one
     attempt rated right or partial.
   - A concept is complete when all its subtopics are complete.
5. A subtopic moves from not started to in progress when its first block is opened `[Q4]`.
6. A concept's status is derived from its subtopics `[Q4]`: not started while all are not
   started, completed when all are completed, in progress otherwise. A concept with no
   subtopics is not started.

### 4.5 Roadmap and home screen

1. A track is an ordered list of concepts, each showing its status. The next step is the
   first concept in the track that is not completed.
2. The home screen leads with "continue where I stopped": the last subtopic and block Diogo
   was on. Then the next suggested step and "revisões de hoje: N" `[R2]`.
3. If 3 or more days passed without a session, the home screen opens in a return session
   instead (4.7) `[R4]`.
4. A concept can be added to a track before it has content.

### 4.6 Review scheduling (Py-FSRS)

1. Algorithm: Py-FSRS (`fsrs` on PyPI, MIT). Desired retention is configurable `[R5]`.
   Optimizing parameters from Diogo's history is a later phase.
2. Three rating buttons: errei = Again, parcial = Hard, acertei = Good. There is no Easy
   `[R6]`.
3. Two adjustable daily caps: reviews per day (default 20) and new cards per day
   (default 5) `[R1]`.
4. The home screen shows only "revisões de hoje: N", within the caps. Never the overdue
   total, never days overdue `[R2]`.
5. Cards due beyond the cap are redistributed silently, lowest estimated retention first
   `[R3]`: when the day's queue is built, due cards are ordered by current retrievability,
   ascending, and the cap takes the first ones. The ones left out stay due and compete again
   the next day. Stored due dates are never rewritten (`DECISIONS.md` D-011).
6. The review cap counts distinct cards per day. A card failed and shown again the same day
   (Py-FSRS learning and relearning steps) does not use another slot `[Q14]`.

### 4.7 Return session

After 3 or more days without a session, the app opens a return session: the point where Diogo
stopped and at most 5 reviews. No text mentions the absence `[R4]`.

"3 or more days without a session" means at least 3 full Bahia calendar days with no completed
activity between the last day with a session and today. Example: last session on Monday, the
return session opens from Friday on.

After the return session, the normal caps apply for the rest of the day, and the return
session's reviews count toward them `[Q15]`.

### 4.8 Study, notebook mode and practice

1. Study shows the content one block at a time, in the document's order, which the template
   keeps in contract order, with extra blocks in their original position (`DECISIONS.md` D-020,
   D-023).
2. Notebook mode is a separate presentation for copying into a paper notebook: clear titles,
   short definitions, essential points, selected examples. It can end with one
   "explain in my words" prompt or one question to answer without looking `[briefing]`.
   It shows, in order: Objetivo, Ideia central, Exemplo, Resumo para o caderno, then one
   practice prompt `[Q16]`.
3. Practice offers questions with a reference answer, and "explain in my words". The
   reference answer is shown only after Diogo submits. Diogo then rates the attempt: right,
   partial or wrong. Previous attempts are visible for comparison.
4. Interrupting any activity does not lose progress `[briefing]`: a draft answer and the
   current block survive closing the browser.

### 4.9 Pomodoro

Optional. Adjustable focus and break durations. When time is up, one discreet notice. It never
blocks studying and never competes visually with the content.

### 4.10 Backup

1. Daily export of all content and history, in JSON (complete) and Markdown (one file per
   subtopic, in the content contract format), written to a folder inside the Obsidian vault,
   which syncs to Google Drive `[D8]`.
2. The folder is configured, not hard-coded.
3. If the computer was off at the scheduled time, the export runs at startup when the last
   one is older than 24 hours `[Q17]`.
4. Exports are kept for 30 days `[Q17]`.
5. Restore through the UI is out of scope. A documented restore command exists, and it is
   tried once before day 1 `[Q17]`.

### 4.11 Measurement

1. Session events are recorded for every activity. There is no screen for them in v1.
2. Primary success metric `[D10]`: at least 3 distinct days with a completed activity, in at
   least 3 of 4 blocks of 7 consecutive days counted from day 1, in Bahia time. Several sessions
   on the same day count once.
3. Support metrics: time between opening the app and starting an activity; fraction of the
   day's reviews done; accuracy on cards from concepts completed more than 14 days earlier.
4. Day 28: a verdict written in `DECISIONS.md` with, in this order, the numbers per block, the
   features that shipped that month, the sessions lost to being away from the computer, and the
   pre-written reading that applies `[D4]`, `[D10]`.
5. Day 1 is the first day use mode runs a release that passes the M1 gate of `docs/plan.md`,
   with at least one concept registered (`DECISIONS.md` D-016). Its date is recorded in
   `DECISIONS.md` when it happens.

## 5. Environments

### 5.1 Use mode

- Docker starts with Windows. The compose file uses `restart: unless-stopped`.
- The built frontend is served by a container. Access is through a browser bookmark.
- Listens only on `127.0.0.1`. No login.
- Its database and volumes are separate from dev mode.
- Use mode only moves to a tagged version.

### 5.2 Dev mode

- Vite with hot reload, its own database and volume.

### 5.3 Debts for the portfolio deploy (not v1)

Login (SimpleJWT), deploy on Railway and Vercel, mobile screens.

## 6. Definition of done for v1

v1 is done when all of the following hold in use mode on Diogo's computer:

1. Full cycle: pick a concept in the roadmap, paste its Markdown, study it, answer a question
   or explain it, rate the attempt, and come back to review its cards on a later day.
2. Review runs on Py-FSRS with both daily caps, never shows overdue totals, and opens a return
   session after 3 or more full days away.
3. Markdown import follows section 4.2: blocks, fixed `P`/`C` labels across re-imports,
   pending cards with one-by-one approval, unsourced AI callouts marked.
4. Use mode starts with Windows, listens on `127.0.0.1`, keeps its data apart from dev, and
   writes the daily JSON and Markdown backup to the vault folder.
5. Session events are recorded for every activity, enough to compute the day 28 metrics.
6. The core acceptance tests pass: every section 8 scenario has a passing test in
   `tests/acceptance/` or in `backend/tests/` (`DECISIONS.md` D-027, mapped in
   `docs/acceptance-coverage.md`), and `make lint` and `make test` pass.

## 7. Core and acceptance tests

The core is: review scheduling and caps, status and completion rules, and Markdown import
(blocks, labels, pending cards, callouts). Only the core gets automated tests until the end of
the first month of use.

Acceptance tests live in `tests/acceptance/` and are written by Diogo. Nothing else writes or
edits files there. For v1, a scenario also counts as covered by a passing test named after it in
`backend/tests/`, written by the agent (`DECISIONS.md` D-027). Section 8 proposes scenario titles,
and `docs/acceptance-coverage.md` maps each one to its tests.

## 8. Proposed acceptance scenario titles

Titles only, for Diogo to accept, change or drop.

### Scheduling and caps

1. Rating a card Again, Hard or Good updates it through Py-FSRS and saves a review log.
2. There is no Easy rating.
3. With 30 cards due and a cap of 20, today's queue has 20 cards.
4. The 20 cards picked are the ones with the lowest retrievability.
5. Cards left out by the cap are still due the next day, with their stored due date unchanged.
6. With 8 approved new cards and a new card cap of 5, today's queue introduces 5.
7. Pending, suspended and rejected cards never enter the queue.
8. "Reviews today" never exceeds the remaining cap and never shows overdue counts.
9. Changing the review cap changes today's remaining count.
10. A review at 22:30 in Bahia counts toward that Bahia day, not the UTC day.
11. A card failed and shown again the same day does not use another slot of the cap.
12. With the last session on Monday, opening the app on Friday starts a return session with at
    most 5 reviews.
13. With the last session on Monday, opening the app on Thursday does not start a return
    session.
14. Reviews done in the return session count toward that day's cap.
15. An activity abandoned without `completed_at` does not count as a session.

### Status and completion

16. Content without "Ideia central" is saved as draft.
17. Content whose only question has no reference answer is saved as draft.
18. Content with "Ideia central" and one question with a reference answer is ready.
19. Opening the first block moves a subtopic from not started to in progress.
20. A subtopic's level, perceived difficulty, study status and review need change
    independently.
21. A subtopic with all blocks read and one attempt rated partial is suggested complete.
22. A subtopic with all blocks read and only wrong attempts is not suggested complete.
23. A suggested completion changes the status only when Diogo confirms it.
24. A concept is completed when all its subtopics are, and in progress when only some are.
25. Completing a concept keeps its cards in review.

### Markdown import

26. Each known `##` heading becomes its own block, in order.
27. An unknown `##` heading becomes an extra block in its original position.
28. `P1` with its reference answer becomes a question.
29. `C1: front :: back` becomes a pending card.
30. Re-importing with changed text under `P1` keeps the attempts of `P1`.
31. Re-importing with changed text under `C1` keeps the review history of `C1`.
32. Re-importing without `P2` archives `P2` and keeps its attempts.
33. Re-importing without `C2` suspends `C2`.
34. Re-importing with `C2` back restores it with its review history.
35. A new `C3` on re-import enters as pending.
36. Two `C1` labels in one document block the save.
37. A `[!ia]` callout without a `Fonte:` URL is marked "complemento sem fonte".
38. A `[!ia]` callout with a `Fonte:` URL is not marked.
39. A frontmatter naming another subtopic shows a warning and saves into the subtopic being
    edited.
40. Approving a pending card makes it active and subject to the new card cap.
41. There is no way to approve all pending cards at once.
42. A rejected card stays rejected when the same Markdown is imported again.

## 9. Answered questions

Questions the source left open, answered by Diogo on 2026-10-12 by accepting the suggestions in
the first draft of this spec (`DECISIONS.md` D-013).

| # | Question | Answer |
| --- | --- | --- |
| Q1 | How is a completed activity recorded, and what is day 1? | A `completed_at` field per session event, empty when the activity is abandoned. Day 1 as written in D-010. |
| Q2 | Is "app opened" an event? | Yes, one `app_opened` event per load of the home screen. |
| Q3 | What are the fixed completion suggestion criteria? | Subtopic: all blocks read and at least one attempt rated right or partial. Concept: all subtopics completed. |
| Q4 | Where do status and the classification fields live, and what starts "in progress"? | On the subtopic. Concept status is derived from its subtopics. A subtopic is in progress once its first block is opened. |
| Q5 | What is "review need"? | A manual flag, shown next to an automatic "has cards due" indicator. |
| Q6 | Can a manual card belong to a concept without a subtopic? | Yes: concept or subtopic. |
| Q7 | Is there a reject action in approval? | Yes. A rejected label stays rejected until removed from the Markdown and added again. |
| Q8 | Does a removed label that comes back restore its history? | Yes. |
| Q9 | When does the Bahia day start? | At midnight. |
| Q10 | Default desired retention? | 0.9. |
| Q11 | Does a question without a reference answer count toward ready? | No. |
| Q12 | What counts as a source in a `[!ia]` callout? | A `Fonte:` followed by a URL. |
| Q13 | What if the frontmatter names another area, concept or subtopic? | A warning in the preview; the save goes into the subtopic being edited. |
| Q14 | Does a same-day repeat of a failed card use another cap slot? | No: the cap counts distinct cards per day. |
| Q15 | Do the normal caps apply after a return session? | Yes, and the return session's reviews count toward them. |
| Q16 | Which blocks does notebook mode use? | Objetivo, Ideia central, Exemplo, Resumo para o caderno, then one practice prompt. |
| Q17 | Backup catch-up, retention and restore? | Run at startup if the last export is older than 24 h; keep 30 days; a documented restore command, tried once before day 1. |
