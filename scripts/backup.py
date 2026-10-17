"""Hourly backup task on the Windows host (DECISIONS.md D-019 and D-028).

run:       export inside the use-mode container, copy the staging folder to the vault with
           robocopy, then remove vault exports older than 30 days.
register:  create the hourly Windows scheduled task that calls `run`.

Both folders come from .env.use: BACKUP_STAGING (on C:, bind-mounted into the container) and
BACKUP_VAULT (the folder inside the Obsidian vault on G:). Each run appends to backup.log in the
staging folder and exits non-zero on failure, which Task Scheduler shows as the last run result.
"""

import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env.use"
TASK = "Athenas backup"
LOG = "backup.log"
# Same name and age rules as backend/organization/management/commands/backup.py.
EXPORT = re.compile(r"^athenas-(\d{8}-\d{6})$")
KEEP = timedelta(days=30)
# The task runs under pythonw, without a console; this keeps docker and robocopy from opening one.
QUIET = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def read_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.lstrip().startswith("#"):
            values[key.strip()] = value.strip()
    return values


def expired(names, now):
    """Export folder names older than 30 days; other names and the newest export never appear."""
    stamps = []
    for name in names:
        if match := EXPORT.match(name):
            try:
                when = datetime.strptime(match[1], "%Y%m%d-%H%M%S").replace(tzinfo=UTC)
            except ValueError:  # a hand-made name with an impossible date
                continue
            stamps.append((when, name))
    return [name for when, name in sorted(stamps)[:-1] if now - when > KEEP]


def run():
    env = read_env()
    staging = Path(env.get("BACKUP_STAGING", ""))
    vault = Path(env.get("BACKUP_VAULT", ""))
    # An empty value would become the current folder, so robocopy would write to the wrong place.
    if not (staging.is_absolute() and vault.is_absolute()):
        print("Set BACKUP_STAGING and BACKUP_VAULT in .env.use as absolute paths.")
        return 1
    lines = []
    failed = False

    export = subprocess.run(
        ["docker", "compose", "--env-file", ENV, "exec", "-T", "backend",
         "python", "manage.py", "backup"],
        cwd=ROOT, capture_output=True, text=True, creationflags=QUIET,
    )  # fmt: skip
    lines.append(f"export exit {export.returncode}: {(export.stdout + export.stderr).strip()}")
    failed |= export.returncode != 0

    # The copy runs even when the export failed or was skipped: it catches up on exports made
    # while Drive was not running. An absent vault folder (Drive not mounted, wrong path) is a
    # failure, never a folder for robocopy to create.
    if not vault.is_dir():
        lines.append(f"copy skipped: {vault} is not a folder")
        failed = True
    else:
        copy = subprocess.run(
            ["robocopy", staging, vault, "/E", "/XD", "*.partial", "/XF", LOG,
             "/R:2", "/W:10", "/NP", "/NJH", "/NDL", "/NFL"],
            capture_output=True, encoding="oem", errors="replace", creationflags=QUIET,
        )  # fmt: skip
        # robocopy: 0 to 7 mean success (bit 1 = files copied), 8 or more mean a failure.
        lines.append(f"copy exit {copy.returncode}")
        if copy.returncode >= 8:
            lines.append(" ".join(copy.stdout.split()))
            failed = True
        else:
            old = expired((p.name for p in vault.iterdir() if p.is_dir()), datetime.now(UTC))
            for name in old:
                try:
                    shutil.rmtree(vault / name)
                    lines.append(f"removed from the vault: {name}")
                except OSError as error:  # Drive may hold a lock; the next run retries
                    lines.append(f"could not remove {name}: {error}")
                    failed = True

    if staging.is_dir():
        with open(staging / LOG, "a", encoding="utf-8") as log:
            log.write(f"{datetime.now(UTC):%Y-%m-%d %H:%M:%S} UTC\n")
            log.writelines(f"  {line}\n" for line in lines)
    return 1 if failed else 0


def register():
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    python = pythonw if pythonw.exists() else Path(sys.executable)
    action = f'"{python}" "{Path(__file__).resolve()}" run'
    return subprocess.run(
        ["schtasks", "/Create", "/F", "/SC", "HOURLY", "/TN", TASK, "/TR", action]
    ).returncode


if __name__ == "__main__":
    commands = {"run": run, "register": register}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit("usage: backup.py run|register")
    sys.exit(commands[sys.argv[1]]())
