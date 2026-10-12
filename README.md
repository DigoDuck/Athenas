# Athenas

Personal study platform (Django + DRF, React + Vite, PostgreSQL). The v1 scope is in
`docs/spec.md`; decisions are in `DECISIONS.md`.

Requirements: Docker Desktop (set to start with Windows), `make`, Python 3 (only for the
use-mode helper).

## Dev mode

Hot reload, own database and volume (`athenas-dev`).

```bash
make dev-up      # frontend on http://127.0.0.1:5470, API on http://127.0.0.1:8471
make dev-down
make lint        # ruff + eslint, inside containers
make test        # pytest against the dev Postgres
```

## Use mode

Always on, listens on `127.0.0.1:8470` only, no login, own database and volume (`athenas`).
It only runs a clean, tagged commit.

```bash
make use-init    # once: creates .env.use with generated secrets (git-ignored)
git checkout v0.1.0
make use-up      # builds and starts with restart: unless-stopped
make use-down
```

Bookmark `http://127.0.0.1:8470`. Containers come back after a reboot as long as Docker
Desktop starts with Windows.

## Ports

| Port | What |
| --- | --- |
| 8470 | use mode (nginx, serves the build and proxies `/api`) |
| 8471 | dev API |
| 5470 | dev Vite |

The databases are not published to the host.
