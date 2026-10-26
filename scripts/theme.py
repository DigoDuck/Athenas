"""Push a study theme written by Claude into Athenas through its local API (DECISIONS.md D-030).

A theme is a folder with `tema.json` (area, track, the concepts and subtopics in study order, and
the images with their credit) and one Markdown file per subtopic in the content contract (spec
4.1). The athenas-tema skill writes the folder; this script is the only way its content reaches
the app.

check:     validate the folder with the app's own parser and image rules, without network.
push:      check, upload the images the app lacks, then create only what is missing (area, track,
           concepts, steps, subtopics) and save each subtopic's Markdown. It never approves,
           rejects, edits or deletes anything else, so every card enters pending and waits for
           Diogo (spec 4.3).
download:  save one Wikimedia Commons file into the theme folder (DECISIONS.md D-033).
"""

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USE_MODE = "http://127.0.0.1:8470"
CREDIT = ("generated_by", "source_url", "author", "license")
# Commons only: its file pages state author and license, so every credit can be checked (D-033).
DOWNLOADS = ("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/")
sys.path.insert(0, str(ROOT / "backend"))  # for the app's pure modules: no Django


def repeated(names):
    return sorted({name for name in names if names.count(name) > 1})


def theme_images(folder, theme):
    """(name, path, credit) for each image in tema.json; the name is the file name's stem."""
    found = []
    for image in theme.get("images", []):
        path = folder / image.get("file", "")
        found.append((path.stem, path, {key: image.get(key, "") for key in CREDIT}))
    return found


def check(folder):
    """The theme and the problems that block a push; prints one line per file that passes."""
    from content import images
    from content.parser import Target, contract_gaps, parse_markdown

    theme = json.loads((folder / "tema.json").read_text(encoding="utf-8"))
    problems = []
    declared = set()
    for name, path, credit in theme_images(folder, theme):
        label = path.relative_to(folder).as_posix()
        if not path.is_file():
            problems.append(f"tema.json: image not found: {label}")
            continue
        if not images.NAME_RE.fullmatch(name):
            problems.append(f"{label}: name it with lowercase letters, digits and -")
        problems += [f"{label}: {item}" for item in images.problems(path.read_bytes(), **credit)]
        declared.add(name)
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
            # The same gaps the "Novo tema" screen lists, so both paths share one contract (D-040).
            found = parsed.errors + parsed.warnings + contract_gaps(parsed)
            if not parsed.generated_by:
                # Without it the app shows generated text as Diogo's own (DECISIONS.md D-032).
                found.append("frontmatter needs origem: claude")
            found += [f"image not in tema.json: {n}" for n in parsed.images if n not in declared]
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


def image_bytes(base, name):
    """The stored image's bytes, or None when the app has no image by that name."""
    try:
        with urllib.request.urlopen(f"{base}/api/images/{name}/", timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        sys.exit(f"GET /api/images/{name}/: HTTP {error.code}")


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

    # --replace names the files it may overwrite: as one flag for the whole run it also overwrote
    # every subtopic Diogo had edited in the app (DECISIONS.md D-039).
    files = {path.relative_to(folder).as_posix() for _, path, _ in theme_images(folder, theme)}
    files |= {s["file"] for c in theme["concepts"] for s in c["subtopics"] if s.get("file")}
    if unknown := sorted(set(replace) - files):
        print("--replace names files that are not in tema.json:", *unknown)
        return 1

    images_saved, images_kept = 0, []
    for name, path, credit in theme_images(folder, theme):
        data = path.read_bytes()
        stored = image_bytes(base, name)
        file = path.relative_to(folder).as_posix()
        if stored == data and file not in replace:
            continue
        if stored is not None:
            if file not in replace:
                # Another theme or an earlier push owns this name: replacing it is on purpose.
                images_kept.append(file)
                continue
            # Named: sent even with the same bytes, so a corrected credit reaches the app.
            print(f"replaced image {name}")
        body = {"data": base64.b64encode(data).decode(), **credit}
        status, answer = api(base, "PUT", f"/api/images/{name}/", body)
        if status not in (200, 201):
            sys.exit(f"PUT /api/images/{name}/: HTTP {status} {answer}")
        images_saved += 1

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
            if status not in (200, 404):
                # A 502 while the backend restarts is not "no content": never overwrite on it.
                sys.exit(f"GET {url}: HTTP {status} {current}")
            if status == 200 and current["raw_markdown"] == text:
                unchanged += 1
                continue
            if status == 200 and entry["file"] not in replace:
                # Diogo may have edited it in the app. A re-import keeps history by label (4.2.6),
                # but it only happens on purpose.
                kept.append(entry["file"])
                continue
            if status == 200:
                # The app keeps no past Markdown: its copy stays beside the file, one per replace.
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
                copy = folder / f"{entry['file']}.app-{stamp}.md"
                copy.write_text(current["raw_markdown"], encoding="utf-8")
                print(f"replaced {entry['file']} (the app's copy is in {copy.name})")
            call(base, "PUT", url, {"markdown": text})
            saved += 1
            query = f"/api/flashcards/?subtopic={subtopic['id']}&state=pending"
            pending += len(call(base, "GET", query))

    print(f"saved {images_saved} images")
    if images_kept:
        print("images left untouched, the app has other bytes (--replace <file>):", *images_kept)
    print(f"saved {saved} contents ({pending} cards pending approval), {unchanged} up to date")
    if kept:
        print("left untouched, the app has other content (--replace <file>):", ", ".join(kept))
    return 0


def download(url, file):
    from content import images

    if not url.startswith(DOWNLOADS):
        sys.exit(f"download takes only Wikimedia URLs: {', '.join(DOWNLOADS)} (D-033)")
    # Wikimedia refuses requests without a User-Agent that names the client.
    request = urllib.request.Request(url, headers={"User-Agent": "Athenas/0.1 (personal study)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(images.MAX_BYTES + 1)
    if len(data) > images.MAX_BYTES:
        sys.exit(f"over {images.MAX_BYTES // 1024} KB: pick a smaller thumbnail (800px wide)")
    if images.media_type(data) is None:
        sys.exit("not a PNG, JPEG, GIF, WebP or SVG file")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)
    print(f"saved {file} ({len(data) // 1024} KB)")
    return 0


def main():
    # The check quotes document lines, emoji included; a Windows pipe writes cp1252.
    sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["check", "push", "download"])
    parser.add_argument("folder", type=Path, help="the theme folder; for download, the file")
    parser.add_argument("--url", help="download: a Wikimedia file or thumbnail address")
    parser.add_argument("--base", default=USE_MODE, help=f"API address, default {USE_MODE}")
    parser.add_argument("--first", action="store_true", help="allow the first concept (day 1)")
    parser.add_argument(
        "--replace",
        nargs="+",
        default=[],
        metavar="FILE",
        help="re-import these files (paths as in tema.json) even if the app has other content",
    )
    args = parser.parse_args()
    if args.command == "download":
        if not args.url:
            sys.exit("download needs --url")
        return download(args.url, args.folder)
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
