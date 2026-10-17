# Athenas

Personal study platform (Django + DRF, React + Vite, PostgreSQL). The v1 scope is in
`docs/spec.md`; decisions are in `DECISIONS.md`.

Requirements: Docker Desktop (set to start with Windows), `make`, Python 3 (only for the
use-mode helper and the backup task).

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

## Backup and restore

The backend exports into a staging folder on `C:`, and an hourly Windows task copies it to the
vault (`DECISIONS.md` D-019, D-028). Set both folders in `.env.use` as absolute paths:
`BACKUP_STAGING` on `C:` and `BACKUP_VAULT`, which must already exist in the vault. Then, once:

```bash
python scripts/backup.py register   # hourly task "Athenas backup"
python scripts/backup.py run        # one run now; check backup.log in the staging folder
```

Restore replaces everything in use mode with one export. Make a fresh export first, and copy
the export folder back from the vault into `BACKUP_STAGING` if it is no longer there:

```bash
docker compose --env-file .env.use exec backend python manage.py backup --force
docker compose --env-file .env.use exec backend python manage.py flush --noinput
docker compose --env-file .env.use exec backend python manage.py loaddata /backup/athenas-YYYYMMDD-HHMMSS/data.json
```

## Ports

| Port | What |
| --- | --- |
| 8470 | use mode (nginx, serves the build and proxies `/api`) |
| 8471 | dev API |
| 5470 | dev Vite |

The databases are not published to the host.
