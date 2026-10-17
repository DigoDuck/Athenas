"""Push a study theme written by Claude into Athenas through its local API (DECISIONS.md D-030).

A theme is a folder with `tema.json` (area, track, and the concepts and subtopics in study order)
and one Markdown file per subtopic in the content contract (spec 4.1). The athenas-tema skill
writes the folder; this script is the only way its content reaches the app.

check:  validate the folder with the app's own parser, without network.
push:   check, then create only what is missing (area, track, concepts, steps, subtopics) and save
        each subtopic's Markdown. It never approves, rejects, edits or deletes anything else, so
        every card enters pending and waits for Diogo (spec 4.3).
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USE_MODE = "http://127.0.0.1:8470"


def repeated(names):
    return sorted({name for name in names if names.count(name) > 1})


def check(folder):
    """The theme and the problems that block a push; prints one line per file that passes."""
    sys.path.insert(0, str(ROOT / "backend"))
    from content.parser import KNOWN_HEADINGS, Target, parse_markdown  # pure: no Django

    theme = json.loads((folder / "tema.json").read_text(encoding="utf-8"))
    problems = []
    if not (theme.get("area") and theme.get("track") and theme.get("concepts")):
        problems.append("tema.json: needs area, track and at least one concept")
    concepts = theme.get("concepts", [])
    problems += [
        f"tema.json: concept repeated: {n}" for n in repeated([c["name"] for c in concepts])
    ]
    for concept in concepts:
        names = [s["name"] for s in concept.get("subtopics", [])]
        if not names:
            problems.append(f"tema.json: concept without subtopics: {concept['name']}")
        problems += [f"tema.json: subtopic repeated: {n}" for n in repeated(names)]
        for subtopic in concept.get("subtopics", []):
            if not subtopic.get("file"):
                continue  # planned only: the structure goes in, the content comes later
            path = folder / subtopic["file"]
            if not path.is_file():
                problems.append(f"{subtopic['file']}: file not found")
                continue
            target = Target(theme["area"], concept["name"], subtopic["name"])
            parsed = parse_markdown(path.read_text(encoding="utf-8"), target)
            found = parsed.errors + parsed.warnings
            kinds = [block.kind for block in parsed.blocks]
            if missing := KNOWN_HEADINGS - set(kinds):
                found.append(f"missing headings: {', '.join(sorted(missing))}")
            if "extra" in kinds:
                found.append("a heading outside the contract, or text before the first ##")
            if parsed.state != "ready":
                found.append("draft: needs Ideia central and a question with its reference answer")
            if parsed.level is None:
                found.append("frontmatter needs nivel")
            if not any(b.kind == "Fontes" and "http" in b.body for b in parsed.blocks):
                found.append("Fontes has no URL")
            problems += [f"{subtopic['file']}: {item}" for item in found]
            if not found:
                print(f"ok  {subtopic['file']}: {len(parsed.questions)} questions, "
                      f"{len(parsed.cards)} cards")  # fmt: skip
    return theme, problems


def api(base, method, path, body=None):
    request = urllib.request.Request(
        base + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def call(base, method, path, body=None, expect=200):
    status, data = api(base, method, path, body)
    if status != expect:
        sys.exit(f"{method} {path}: HTTP {status} {data}")
    return data


def push(folder, base, first, replace):
    theme, problems = check(folder)
    if problems:
        print("\n".join(problems))
        return 1
    areas = {a["name"]: a for a in call(base, "GET", "/api/areas/")}
    tracks = {t["name"]: t for t in call(base, "GET", "/api/tracks/")}
    concepts = {(c["area"], c["name"]): c for c in call(base, "GET", "/api/concepts/")}
    subtopics = {(s["concept"], s["name"]): s for s in call(base, "GET", "/api/subtopics/")}
    if not concepts and not first:
        print(
            f"{base} has no concept yet. In use mode the first concept starts day 1 of the "
            "experiment (DECISIONS.md D-016). Nothing was written. Run again with --first once "
            "Diogo confirms."
        )
        return 2

    def create(path, body, label):
        data = call(base, "POST", path, body, expect=201)
        print(f"created {label}")
        return data

    name = theme["area"]
    area = areas.get(name) or create("/api/areas/", {"name": name}, f"area {name}")
    name = theme["track"]
    track = tracks.get(name) or create("/api/tracks/", {"name": name}, f"track {name}")
    in_track = {step["concept"] for step in track["steps"]}
    saved, unchanged, kept, pending = 0, 0, [], 0
    for item in theme["concepts"]:
        name = item["name"]
        concept = concepts.get((area["id"], name)) or create(
            "/api/concepts/",
            {"area": area["id"], "name": name, "objective": item.get("objective", "")},
            f"concept {name}",
        )
        if concept["id"] not in in_track:
            create("/api/steps/", {"track": track["id"], "concept": concept["id"]}, f"step {name}")
        for entry in item["subtopics"]:
            name = entry["name"]
            subtopic = subtopics.get((concept["id"], name)) or create(
                "/api/subtopics/", {"concept": concept["id"], "name": name}, f"subtopic {name}"
            )
            if not entry.get("file"):
                continue
            text = (folder / entry["file"]).read_text(encoding="utf-8")
            url = f"/api/subtopics/{subtopic['id']}/content/"
            status, current = api(base, "GET", url)
            if status == 200 and current["raw_markdown"] == text:
                unchanged += 1
                continue
            if status == 200 and not replace:
                # Diogo may have edited it in the app. A re-import keeps history by label (4.2.6),
                # but it only happens on purpose.
                kept.append(entry["file"])
                continue
            call(base, "PUT", url, {"markdown": text})
            saved += 1
            query = f"/api/flashcards/?subtopic={subtopic['id']}&state=pending"
            pending += len(call(base, "GET", query))

    print(f"saved {saved} contents ({pending} cards pending approval), {unchanged} up to date")
    if kept:
        print("left untouched, the app has other content (use --replace):", ", ".join(kept))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["check", "push"])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--base", default=USE_MODE, help=f"API address, default {USE_MODE}")
    parser.add_argument("--first", action="store_true", help="allow the first concept (day 1)")
    parser.add_argument("--replace", action="store_true", help="re-import changed content")
    args = parser.parse_args()
    if args.command == "check":
        problems = check(args.folder)[1]
        print("\n".join(problems) or "all files pass")
        return 1 if problems else 0
    try:
        return push(args.folder, args.base.rstrip("/"), args.first, args.replace)
    except urllib.error.URLError as error:
        sys.exit(f"Athenas did not answer at {args.base}: {error.reason}. Is it running?")


if __name__ == "__main__":
    sys.exit(main())
