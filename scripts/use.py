"""Use mode helper: creates .env.use, starts only from a clean, tagged commit (spec 5.1)."""

import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env.use"
# .env.use also fills ${BACKUP_STAGING} in docker-compose.yml.
COMPOSE = ["docker", "compose", "--env-file", str(ENV)]


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def init():
    if ENV.exists():
        print(".env.use already exists, left untouched.")
        return 0
    ENV.write_text(
        "POSTGRES_DB=athenas\n"
        "POSTGRES_USER=athenas\n"
        f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}\n"
        f"DJANGO_SECRET_KEY={secrets.token_urlsafe(50)}\n"
        "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost\n"
        "DJANGO_SUPERUSER_USERNAME=diogo\n"
        f"DJANGO_SUPERUSER_PASSWORD={secrets.token_urlsafe(18)}\n"
        f"BACKUP_STAGING={Path.home() / 'AthenasBackup'}\n"
        "BACKUP_VAULT=\n",
        encoding="utf-8",
    )
    print("Created .env.use with generated secrets. Set BACKUP_VAULT before `make use-up`.")
    return 0


def up():
    if not ENV.exists():
        print("Missing .env.use. Run `make use-init` first.")
        return 1
    code, tag = git("describe", "--exact-match", "--tags", "HEAD")
    if code != 0:
        print("Use mode only runs a tagged version. Check out a tag first (git checkout vX.Y.Z).")
        return 1
    if git("status", "--porcelain")[1]:
        print("Working tree is not clean. Use mode must match the tag exactly.")
        return 1
    print(f"Starting use mode at {tag}.")
    return subprocess.run(COMPOSE + ["up", "-d", "--build"], cwd=ROOT).returncode


def down():
    return subprocess.run(COMPOSE + ["down"], cwd=ROOT).returncode


if __name__ == "__main__":
    commands = {"init": init, "up": up, "down": down}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit("usage: use.py init|up|down")
    sys.exit(commands[sys.argv[1]]())
