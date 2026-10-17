---
name: athenas-tema
description: Build a whole study theme in Athenas from one line (tema, trilha, roadmap). Writes the track's concepts and subtopics and one contract Markdown per subtopic, with questions and cards, from sources opened in the run, and pushes them with scripts/theme.py. Use when Diogo asks to create, generate or fill a tema, trilha or roadmap in Athenas.
argument-hint: "<tema>[: objetivo]"
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Bash(python scripts/theme.py *)
---

# Athenas theme

Turn `$ARGUMENTS` into a track in Athenas (DECISIONS.md D-030). Diogo gives only the theme,
optionally followed by `: objetivo`. Do not ask him anything except the day 1 confirmation in
step 7. When the goal or the level is missing, assume a practical foundation at `iniciante` and
say so in the summary.

## Never

- Reach Athenas any other way than `python scripts/theme.py`.
- Approve, reject, edit or delete anything in the app. Cards enter pending and Diogo approves them
  one by one (spec 4.3): that review is the only guard against a wrong card being scheduled for
  months.
- Write a URL you did not open with WebFetch in this run.
- Use the em dash.

## Steps

1. Read `docs/spec.md` sections 4.1 and 4.2: the contract and the import rules.
2. Plan the track. Area: `Programação` or `Inglês` (spec 1); another one only when the theme fits
   neither. Track: the theme's name, short. Three to five concepts in study order, two to four
   subtopics each, at most twelve subtopics; a larger theme becomes a second run with its own
   track. Names are short, in pt-BR, and unique: a concept with the same name in the same area is
   reused, so pick a distinct name unless it really is the same concept.
3. Research each concept before writing it: WebSearch for the official documentation or another
   primary source (for English, a dictionary or a grammar reference), and WebFetch every page you
   rely on.
4. Write the folder `temas/<slug>/` at the repo root (git-ignored): `tema.json` and one
   `NN-<slug>.md` per subtopic.

   ```json
   {
     "area": "Programação",
     "track": "Docker",
     "concepts": [
       {
         "name": "Imagens e containers",
         "objective": "One sentence: what Diogo can do after this concept.",
         "subtopics": [
           {"name": "Imagem e container", "file": "01-imagem-e-container.md"}
         ]
       }
     ]
   }
   ```

   A subtopic without `file` is created empty, as a planned step.
5. Write each Markdown to the contract:
   - Frontmatter: `area`, `conceito` and `subtema` with the exact names in `tema.json`, `nivel`
     (iniciante, intermediário, avançado or especialista) and `origem: claude`.
   - The ten `##` headings of spec 4.1, in that order, and no other `##` heading.
   - Ideia central: two to four sentences that stand alone.
   - Explicação: what the sources say, in your words, 300 to 700 words.
   - Exemplo: concrete. Code for programming; sentences in context for English.
   - Confusões comuns: two to four misconceptions, each with its correction.
   - Prática: two to four `### P<n>: <question>`, each followed by
     `Resposta de referência: <answer>`. At least one asks to apply, not only to recall.
   - Resumo para o caderno: four to eight short lines to copy by hand.
   - Fontes: the URLs you fetched, one per line.
   - Flashcards: three to six `- C<n>: <front> :: <back>`, one fact per card, one line each, no
     `::` inside the text.
   - A statement your sources do not back goes in a `> [!ia]` callout, with `Fonte: <url>` when
     you have one; the app marks the callouts without a source.
   - pt-BR for everything Diogo reads; code, commands and identifiers stay as they are. One
     subtopic fits a session of 20 to 40 minutes.
6. Run `python scripts/theme.py check temas/<slug>` and fix every line it reports until it
   passes.
7. Run `python scripts/theme.py push temas/<slug>`. It writes to use mode (`127.0.0.1:8470`)
   unless `--base` says otherwise; to try this skill, use a disposable copy
   (`--base http://127.0.0.1:8472`), never use mode. If push answers that the instance has no
   concept yet, stop and tell Diogo that in use mode this push starts day 1 of the experiment
   (D-016). Run it again with `--first` only after he says yes in this conversation.
8. Tell Diogo, in Portuguese: the track and its concepts, how many subtopics got content, how many
   cards wait for his approval, and every assumption you made.

## Resuming and fixing

`push` only creates what is missing and skips content that is already identical, so running this
skill again on the same theme resumes after a stop (a usage limit, a closed terminal). To fix a
document, edit its file, keep the existing `P` and `C` labels (they carry Diogo's attempts and
review history, spec 4.2.6) and push with `--replace`.
