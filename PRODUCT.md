# Product

<!-- impeccable:product-schema 1 -->

Product record for design work (Impeccable). It summarizes and points to the repo's sources of
truth: `docs/spec.md` for behavior and scope, `DECISIONS.md` for decisions, and
`docs/design-system.md` for the visual system. Where this file and those disagree, they win.

## Platform

web

## Users

One person: Diogo, studying programming and English (spec 1). Typical use: evenings after
work, short sessions on the home PC. Diogo confirmed this as the working assumption on
2026-10-12.

No other audience in v1. The portfolio audience (recruiters) only enters after the first month
of use (D-002) and does not shape any v1 decision.

## Product Purpose

A personal study site that tests one hypothesis: with studying, practicing and reviewing in a
single place, studying becomes a habit. It serves four actions: know what to study, start with
little effort, check what was understood, and review what needs reinforcing (spec 1).

Success is measured over the first month, with a written verdict on day 28 (D-004, D-010,
spec 4.11).

## Positioning

The whole daily cycle happens inside Athenas. The previous system (Obsidian templates,
NotebookLM, Anki) stopped after one session because the tools were spread out. External AI
only prepares content, and cards that AI may have written go through Diogo's approval one by
one before entering the routine (D-001, D-006, D-007).

## Operating Context

- Content is one Markdown file per subtopic, prepared outside with NotebookLM or Claude and
  pasted in (spec 4.1, 4.2). The same file is exported to the Obsidian vault (spec 4.10).
- Runs locally on the desktop, in use mode that is always on, at `127.0.0.1`, with no login
  (D-008, spec 5.1).
- Reviews follow Py-FSRS with daily caps; the day follows Bahia time (D-005, spec 4.6).

## Capabilities and Constraints

- v1 scope, out of scope and constraints: spec 2. Any change to the out-of-scope list needs
  Diogo's ok.
- Desktop only. No phone or tablet screens; below 1200 px the navigation collapses behind a
  "Menu" button (spec 2.3, `docs/design-system.md`).
- No integrated AI in v1 (spec 2.2).
- Terminology: the glossary in spec 3.1. Interface copy is in Portuguese, as Diogo uses the
  terms.

## Brand Commitments

- Name: Athenas. The owl emblem is the identity, used at every size
  (`frontend/src/assets/brand/`).
- Voice (design system section 7): no pressure for missing a routine, no moralizing about
  discipline or productivity. Phrases such as "Continue de onde parou" and "Uma etapa de cada
  vez". Never claim a save before it is confirmed.
- Reviews never show overdue totals; a return after 3 or more days does not mention the
  absence (D-005, spec 4.7).

## Evidence on Hand

- Spec, decisions and design system in the repo, as listed above.
- No real usage data yet: the measurement month has not started. Do not invent metrics,
  testimonials or results.

## Product Principles

1. Starting must take little effort: the next step is always visible (spec 4.5).
2. One place for the whole cycle; nothing in the routine sends Diogo to another tool.
3. Review without pressure: the routine never accumulates guilt.
4. Diogo reviews what AI wrote before it counts.
5. Tool first: real use before portfolio polish.

## Accessibility & Inclusion

No personal accessibility need declared (Diogo, 2026-10-12). The baseline is the design
system's own checks in `docs/design-system.md` section 8 (contrast, keyboard, visible focus,
reduced motion).
