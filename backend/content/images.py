"""Rules for a stored image (DECISIONS.md D-033). Pure, so scripts/theme.py checks the same ones."""

import re

NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,79}")
# Every export carries every image as base64 (D-028), so each one stays small.
MAX_BYTES = 512 * 1024
LICENSE_HINT = "CC0, domínio público, CC BY ou CC BY-SA"


def media_type(data: bytes) -> str | None:
    """The type the bytes really are, never the one a client claims."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    head = data[:2048].lstrip(b"\xef\xbb\xbf").lstrip()
    if (head.startswith((b"<svg", b"<?xml")) and b"<svg" in head) and b"<!ENTITY" not in data:
        return "image/svg+xml"
    return None


def problems(data: bytes, *, generated_by="", source_url="", author="", license="") -> list[str]:
    """Why this image cannot be stored; empty when it can. Messages are pt-BR UI copy."""
    found = []
    if len(data) > MAX_BYTES:
        found.append(f"Imagem com {len(data) // 1024} KB; o limite é {MAX_BYTES // 1024} KB")
    if media_type(data) is None:
        found.append("Formato não aceito: use PNG, JPEG, GIF, WebP ou SVG")
    # A real picture names where it came from; a drawn one names who drew it (D-033).
    if not generated_by and not (source_url and author and license):
        found.append(
            "Imagem sem origem: informe generated_by, ou source_url, author e license "
            f"({LICENSE_HINT})"
        )
    return found
