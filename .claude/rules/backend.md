---
paths:
  - "backend/**"
  - "tests/**"
---

# Backend rules

- Run Django and pytest inside the dev container: `make test`, or
  `docker compose -f docker-compose.dev.yml run --rm backend <command>`.
- New logic goes into the app's `services.py`; views stay thin (see `content/services.py` and
  `content/views.py`).
- A write that touches several rows runs inside `transaction.atomic()`, as `import_content` does.
- History (`Attempt`, `ReviewLog`, `SessionEvent`) is create-only: no update or delete endpoint,
  and nothing reaches it through `CASCADE`. The one exception: a `SessionEvent` is completed once
  through its `complete` action (D-020).
- A product day comes from `django.utils.timezone.localdate()` (`TIME_ZONE` is `America/Bahia`),
  never from the UTC date.
- Py-FSRS state is stored as `Card.to_dict()` and `ReviewLog.to_dict()` give it, plus the indexed
  `due` column, all written by one service function (D-018). Tests that check due dates build the
  scheduler with `enable_fuzzing=False`.
- `tests/acceptance/` is Diogo's: read it to know the target, never edit it.
- Read every generated migration before committing it; one that drops or renames a column waits
  for Diogo's ok.
