# Athenas for three testers: plan

Status: proposed, 2026-10-30. Diogo opened this phase on 2026-10-30 (`DECISIONS.md` D-042): a
hosted Athenas for him and three testers, with AI filling the data and the mechanics of the
Brazilian exam prep sites ("sites de concurso"). `docs/spec.md` stays the record of v1 and
`docs/plan.md` the record of how v1 was built. This file orders the next work. Where it
disagrees with the spec, D-042 and the decision entries each slice adds win.

Every choice below has a recommended option. Section 9 lists the ones only Diogo can make; until
he answers, slices follow the recommendation.

## 1. Where things stand

- v1 runs only on Diogo's PC (use mode on `127.0.0.1:8470`, D-008), for one person, with no
  login. Every table assumes one owner: `Area`, `Track` and `Image` names are unique across the
  database, `Settings` is one row and `DailyReviewQueue` one row per day.
- The month of use started on 2026-10-17 (D-029) and its window closes on 2026-11-13 (D-038).
- The hourly backup task put one export per day in the vault on Google Drive up to
  `athenas-20261027-193803`. Nothing reached it on 10-28, 10-29 or 10-30, so use mode has most
  likely been off since 2026-10-28. That export is the latest copy of Diogo's data reachable
  without the PC.
- Diogo is away from his computer for an open period and follows the work on GitHub only. No step
  in this plan may need his PC.

## 2. What the testers' version is, and what it is not

Minimal version for the testers (release "T", slices T1 to T4 and T7 below):

1. Each person signs in and sees only their own data.
2. A tester types a subject ("assunto"), its discipline ("disciplina") and the exam board style
   ("banca"), and the app asks the AI for objective questions: five options (A to E) or right and
   wrong (Certo/Errado, the Cebraspe style). Each one comes with the answer key, a short
   explanation and the legal or textbook basis it rests on.
3. A question bank screen with filters (discipline, subject, board style, difficulty, not
   answered, answered wrong), one question at a time, the key and the explanation right after
   answering, and a "gabarito errado" report.
4. Everything v1 already does (reading, practice, flashcards with Py-FSRS, home screen,
   pomodoro) keeps working per person.
5. A backup that does not depend on the PC, with a restore drill done before the first tester
   signs in.

After the first week of tester use, only if they ask: performance by discipline and subject (T8),
mock exams ("simulado", T9), and theory generated inside the app (T6).

Left out, on purpose: real exam questions from the boards, user ranking, comments and forums,
video, PDF upload, automatic study cycle or schedule (the roadmap plus the pomodoro cover the
minimum), saved question notebooks (the filter lives in the URL), email (password reset goes
through Diogo), payments, and AI inside study, practice or review (no tutor chat, no AI grading
of open answers).

## 3. Decisions the plan rests on (recommended options)

### 3.1 The month of use and its verdict

Recommended: keep D-010 and D-038 as written. The window closes on 2026-11-13 and the verdict is
written with `day28` on 2026-11-14 or later. The days without the computer go into the verdict
under "sessions lost to being away from the computer", which D-010 already provides for. The
command is read-only and takes `--today`, so it runs on a disposable database restored from the
latest export, in the thread's container, with no PC. The work in this plan is listed under
"features that shipped that month".

- One rule changes, in D-042: D-010 says a result of 0 or 1 of 4 blocks needs a written diagnosis
  before any new feature. Diogo chose to build before the verdict, so the diagnosis is still
  written, but it no longer blocks this plan.
- If Diogo's data reaches the hosted app (T5) before 2026-11-13 and he studies there, those days
  count: same `SessionEvent` table, same Bahia day.
- Not recommended: pausing the window (D-010 counts consecutive days, and changing the rule after
  seeing the numbers is the bias D-038 guards against), or ending it early as "inconclusive"
  (the rule has no such reading).

### 3.2 Hosting

Recommended: Railway, one origin. Three services from what already exists: `web` (the nginx image
from `frontend/Dockerfile`, which already proxies `/api/` to the backend), `backend` (target `use`
of `backend/Dockerfile`, gunicorn) and a managed PostgreSQL 16. Railway builds from the GitHub
repo on each push and can open one environment per pull request, which is the preview Diogo needs.

- One origin means the browser sees one site, so Django's own session login works with no CORS
  setup and no token library. This supersedes the "SimpleJWT, Railway and Vercel" line of spec
  5.3.
- Alternatives: Render (similar, previews are a paid feature); Vercel for the frontend plus
  Railway for the API, as spec 5.3 said (two origins: CORS, cross-site cookies or JWT, more code).
- Plan details (price, previews and volume backups on the cheapest plan) are checked when the
  account exists, in T1. Public sources say the Hobby plan is US$5 per month with US$5 of usage
  included and daily backups for services with a volume; three small services may go over that.

### 3.3 Login and data per person

Recommended: Django's built-in auth with session cookies; DRF `SessionAuthentication` (which also
enforces CSRF) and `IsAuthenticated` on every endpoint; Django admin at `/admin/` for Diogo to
create the testers' accounts from his phone. No sign-up page and no password reset by email.

Every piece of data has an owner. `owner` goes on the roots (`Area`, `Track`, `Image`,
`Settings`), on `SessionEvent` and on `DailyReviewQueue`; everything else reaches its owner
through them. Unique names become unique per owner. A migration assigns all existing rows to
Diogo's account. Alternative not recommended: a shared question bank across users (cheaper AI
calls, but it needs a second ownership model, moderation, and one tester's bad report hides a
question from everyone; at four people the cost difference is cents).

### 3.4 AI inside the app (what changes in D-001)

Changes: the app itself calls the AI, on request, to prepare content (questions now, theory
later).

Stays:

- Content generated by AI carries its origin (`generated_by`, D-032) and the screen says so.
- Flashcards from Markdown still enter pending and are approved one at a time (D-007).
- Studying, practicing and reviewing happen without AI in the loop.
- The AI gets only the text the user typed for that request, never another user's data.

New rule for objective questions (recommended): they enter the bank without one-by-one approval,
which would bury the testers in admin work, but only after an automatic second check. A separate
call answers the question without seeing the key. When it disagrees with the key, or the
question is malformed, the question is discarded and counted, never shown. Each saved question
shows "gerada por IA" and its basis, and a "gabarito errado" report hides it for that user and
keeps it for review. Alternative: the D-007 rule for questions too (pending, one by one).

Provider (recommended): the Claude API, through the official `anthropic` Python SDK, which is a
new production dependency and needs Diogo's ok. Model: Claude Opus 5.5 for both generation and
the check, because a wrong answer key is the costliest failure for someone studying for an exam.
The key lives only in the host's variables. Every user has a daily quota, and the Anthropic
Console account has a monthly spend limit.

Cost, as a rough estimate to replace with the first measured batch: at US$4 per million input
tokens and US$20 per million output tokens, one question plus its check is in the range of
US$0.02 to 0.05. 2,000 questions (four people, about 500 each) are US$40 to 100. Claude Sonnet 5.5
costs half, and Claude Haiku 5.5 about a fortieth, with more wrong keys expected.

### 3.5 Exam questions and copyright

Recommended: no real exam questions. No scraping of QConcursos, TEC or any other site (their terms
forbid it, and their banks are their product), and no prompt that asks the AI to reproduce a real
question. The AI writes original questions "no estilo da banca", never labeled with a real exam,
year or position. A tester may paste a question from their own material into their own bank,
private to them. This is a cautious reading, not legal advice; licensing a real bank is the only
safe route to real questions and is out of this phase.

### 3.6 Phone screens

Recommended: sign in, the question bank and answering a question work from 360 px wide; the rest
stays desktop. People studying for exams solve questions on the phone, and Diogo, without a
computer, can only look at previews on his. Alternatives: desktop only (the testers' first
complaint is likely to be this), or every screen responsive (several large slices).

## 4. Slices

One slice is one branch and one draft PR. Sizes: S is one sitting, M two or three, L more. CORE
follows `AGENTS.md`: the agent writes the scenario tests in `backend/tests/`.

| Slice | Type | What | Depends on | Needs from Diogo | Size |
| --- | --- | --- | --- | --- | --- |
| T0 | docs | This plan and D-042 | none | merge | S |
| T1 | PLUMBING | Railway config for `web`, `backend` and Postgres; nginx reads the backend address from the environment (the official image's template feature); production settings from the environment (`DEBUG` off, hosts, CSRF trusted origins, secure cookies); migrations on deploy; a synthetic demo seed for preview environments only. No production environment yet | T0 | Railway account, repo connected, PR environments on | M |
| T2 | CORE | Login: session auth and CSRF on every endpoint, login and logout screen, `/admin/`, Diogo's superuser created on deploy from host variables, the frontend sends the CSRF header | T1 | his password, set in the host's variables | M |
| T3 | CORE | Data per person (3.3): `owner` and per-owner unique names, a migration that gives existing rows to Diogo, every queryset and service filtered by the signed-in user, `day28` and the support metrics take a user. An isolation test calls every endpoint as a second user against the first user's ids and expects 404 | T2 | ok for the migration (it changes unique constraints, drops no column) | L |
| T4 | PLUMBING | Backup and restore off the PC: the host's daily database backup, plus "baixar meus dados" (the existing JSON export, filtered to the user). Restore drill into a preview environment, counts compared as in D-029, recorded in the slice's decision entry. Production is created only after this drill passes | T3 | turn on backups in the host, if the plan needs it | M |
| T5 | ops | Diogo's data into production: the latest export from Drive loaded under his account, counts compared, the old use mode read-only from then on | T4 | ok to write his data into production | S |
| T7 | CORE | Objective question bank (2.2 and 3.4): `ObjectiveQuestion` (subject as a concept, kind, statement, options, key, explanation, basis, board style, difficulty, `generated_by`, status) and an append-only `ObjectiveAnswer`; generation with structured output and the blind check; daily quota; the bank screen with filters, answer, key and report; a session event per answer, so it counts as a day of use; phone width if 3.6 holds | T3 | API key and spend limit; ok for the `anthropic` dependency | L |
| L1 | launch | Accounts for the three testers, a first-login note on what is stored and how to ask for deletion, and the tester reading fixed in a decision entry before anyone starts (section 7) | T4, T7 | names and emails; he sends the invitations | S |
| T8 | PLUMBING | Performance: answered and accuracy per discipline and subject, last 7 and 30 days; no ranking, nothing about what is late | T7 | none | M |
| T9 | PLUMBING | Mock exam: pick filters, size and an optional timer; keys hidden until the end; result per discipline; answers reuse `ObjectiveAnswer` | T7 | none | M |
| T6 | CORE | Theory with AI inside the app: the "Novo tema" screen (S10) sends the request it already builds to the backend, which calls the AI and fills the answer box; the existing check and import do the rest, cards pending as today | T3, and the T7 AI client | none beyond T7 | S |

Order: T0, T1, T2, T3, T4, then T7 and T5 in either order, L1, and T8, T9 and T6 by the testers'
feedback. T2 and T3 must both be on `main` before production holds anyone's data, and production
does not exist until T4's drill passes.

Why T7 before T6: the question bank is what the sites the testers know are built around, and T7
creates the discipline and subject when they do not exist yet, so a tester can start without
organizing a library first ("pouco tempo administrando material").

## 5. How each PR is tested before the merge

Diogo cannot run anything, so the thread proves each PR and posts the evidence in it:

1. `pytest` on the container's PostgreSQL 16, with its summary line and exit code; `ruff check`,
   `ruff format --check` and `eslint`. `make lint` and `make test` themselves need Docker, which
   the cloud container lacks; CI runs them.
2. CI green on the PR.
3. Playwright through the changed flows on a local `runserver` and Vite, with screenshots in the
   thread.
4. From T1 on: the PR's preview environment deployed, and the same Playwright smoke test (health,
   sign in, one study step, one question) against the preview URL.
5. A migration also runs once on a disposable database restored from the latest export, deleted
   afterwards. That is a copy, never the live data, and it is how D-029's drills worked.

Still Diogo's, typed in the PR or in the chat: merge, force push, CI changes, a migration that
drops or renames a column, a new production dependency, and anything that writes real data (T5).
Railway deploys through its own GitHub app, so no slice needs a CI change.

## 6. What Diogo creates or pays

| What | Why | Cost | When |
| --- | --- | --- | --- |
| Railway account, signed in with GitHub, connected to `DigoDuck/Athenas`, PR environments on | Hosting and previews | Hobby around US$5 per month with US$5 of usage; expect US$5 to 15 with three services (checked in T1) | Before T1 |
| Host variables: `DJANGO_SECRET_KEY` (Railway can generate it), `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_ALLOWED_HOSTS` | Production settings and his account | none | T1 and T2 |
| Anthropic Console account, prepaid credit, a monthly spend limit, an API key saved only as the host variable `ANTHROPIC_API_KEY` | Question generation | Suggested start: US$20 credit and a US$20 monthly limit | Before T7 |
| The testers' names and emails, and the invitations | Accounts and launch | none | L1 |

No secret is ever pasted in a chat, a PR or the repo. A custom domain is optional; the host's
default address works.

## 7. How the testers' phase is read

The same rule as D-010 and D-038, written before anyone starts so the numbers cannot bend it:
four blocks of 7 days per tester from their first sign-in, a day of use being a Bahia day with a
completed activity. Recommended reading: the phase works if at least 2 of the 3 testers have 3 or
more days of use in at least 3 of their 4 blocks. Each tester also answers five short questions at
the end (what they used, what they missed, what they used instead). `day28` gains a `--user`
option in T3 and computes this with no new code beyond that.

Before T7, Diogo asks the three testers which exam, which board and what they use today. If they
mostly want real past questions, the AI bank loses to the free tier of the big sites, and the plan
should know that before its largest slice.

## 8. Risks

1. **Scope against three testers.** The big sites have years of real questions and teachers'
   comments. Athenas cannot win on volume; its case is one place for theory, questions and spaced
   review, with no effort to restart. If the testers do not value that, more features will not
   change it. Mitigation: the minimal version above, the questions to the testers, the reading in
   section 7.
2. **Wrong answer keys.** Generated questions can have a wrong key, a law that changed after the
   model's training, or a trick the board would never use. A tester who learns a wrong key is
   worse off than one who did not study. Mitigation: the basis on every question, the blind
   check, the report, the "gerada por IA" mark, and the discarded rate kept per batch so the
   model choice can be revisited with numbers.
3. **First time on the internet.** The app was built for `127.0.0.1` (D-039 relied on that). Now
   login, CSRF, admin and every endpoint face the public internet. Django has no login rate
   limit built in: passwords are long and generated, and the admin has only Diogo. Each user's
   SVG images are shown only to that user.
4. **Personal data of other people (LGPD).** Names, emails and study history of three people.
   Store only that, say so at first sign-in, delete on request; the host's region is noted in
   T1.
5. **AI cost.** Quotas per user per day and the Console spend limit cap it; the first batch is
   measured before any quota is raised.
6. **Nobody at a computer during an incident.** A broken deploy is fixed by the thread through a
   new PR; Diogo can roll back from the host's dashboard on his phone ("redeploy" of the previous
   deployment), and T1 writes down where that button is.
7. **Rules that still say "local only".** `AGENTS.md` and `CLAUDE.md` say no login and no deploy.
   Cloud sessions cannot commit to those files (the automatic permission mode blocks it), and
   Diogo has no PC to apply a patch. Until he can, D-042 and this file are the reference, and each
   slice's PR says so.
8. **Two copies of Diogo's data.** After T5, studying on the PC's use mode would split his
   history. From T5 on, use mode is read-only history.
9. **The day's time zone.** Every product day is a Bahia calendar day (UTC-3, same as Brasília).
   Testers elsewhere in Brazil see their day change one or two hours off; acceptable for this
   phase.

## 9. Questions only Diogo answers

Each has a recommended option; slices follow it until he answers.

1. **Month of use:** keep the window and the verdict as written, with the days without the
   computer recorded as lost (recommended); or end it now; or pause it.
2. **Hosting:** Railway with one origin (recommended); Render; Vercel plus Railway.
3. **AI model:** Claude Opus 5.5 for generation and check (recommended); Claude Sonnet 5.5, half
   the cost; Claude Haiku 5.5, much cheaper with more wrong keys. And ok to add the `anthropic`
   SDK.
4. **Gate for generated questions:** automatic blind check plus mark plus report (recommended); or
   pending and approved one by one, as cards are.
5. **Bank ownership:** each person's own bank (recommended); or one shared bank.
6. **Phone:** sign-in and the question bank on the phone (recommended); desktop only; everything
   responsive.
7. **Real exam questions:** none, only original questions in the board's style plus what a tester
   pastes for themselves (recommended); or look for a licensed source.
