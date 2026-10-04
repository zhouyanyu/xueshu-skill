"""Read-only checks for xueshu coverage and standard inline Markdown links.

No third-party dependencies. Structural checks do not establish reading quality.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def outside_code(text):
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return re.sub(r"(`+).*?\1", "", "\n".join(lines))


def anchors(text):
    result = re.findall(r'<a\s+[^>]*(?:id|name)=[\"\']([^\"\']+)[\"\']', text)
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.M):
        heading = re.sub(r"\s+#+\s*$", "", heading)
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.append(slug if number == 0 else f"{slug}-{number}")
    return result


def check(root, require_complete=False):
    root = Path(root).resolve()
    errors, progress = [], []

    def error(message):
        errors.append(message)

    def local_file(value, label):
        if not isinstance(value, str) or not value.strip():
            error(f"{label}: missing file path")
            return None
        path = (root / value).resolve()
        if not path.is_relative_to(root):
            error(f"{label}: path outside Wiki")
            return None
        if not path.is_file() or not path.read_bytes().strip():
            error(f"{label}: missing or empty file: {value}")
            return None
        return path

    local_file("阅读首页.md", "home")
    try:
        data = json.loads((root / "coverage.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return errors + [f"coverage.json: {exc}"], progress
    if not isinstance(data, dict) or not isinstance(data.get("units"), list) or not data["units"]:
        return errors + ["coverage.json: units must be a nonempty list"], progress
    ids = set()
    for unit in data["units"]:
        if not isinstance(unit, dict):
            error("unit must be an object")
            continue
        ident = unit.get("id")
        if not isinstance(ident, str) or not ident or ident in ids:
            error(f"invalid or duplicate unit id: {ident}")
        else:
            ids.add(ident)
        status = unit.get("status")
        if status not in {"pending", "partial", "completed", "blocked"}:
            error(f"{ident}: invalid status")
        if status != "completed":
            progress.append(f"{ident}: {status}")
            if require_complete:
                error(f"{ident}: not completed")
        paths = {}
        for key in ("source", "note"):
            if unit.get(key) or status == "completed":
                paths[key] = local_file(unit.get(key), f"{ident}/{key}")
        count = unit.get("paragraphs")
        ranges = unit.get("read_ranges", [])
        if not isinstance(ranges, list):
            error(f"{ident}: read_ranges must be a list")
            ranges = []
        if type(count) is not int or count < 1:
            if count is not None or status == "completed" or ranges or paths.get("source"):
                error(f"{ident}: paragraphs must be a positive integer")
            continue
        covered = set()
        for pair in ranges:
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(type(v) is not int for v in pair)
                    or not 1 <= pair[0] <= pair[1] <= count):
                error(f"{ident}: invalid read range: {pair}")
                continue
            covered.update(range(pair[0], pair[1] + 1))
        if ranges and not paths.get("note"):
            error(f"{ident}: reading ranges have no note")
        if status == "completed" and len(covered) != count:
            error(f"{ident}: completed but covered {len(covered)}/{count} paragraphs")
        source = paths.get("source")
        if source:
            found = anchors(outside_code(source.read_text(encoding="utf-8-sig")))
            expected = {f"p{i:04d}" for i in range(1, count + 1)}
            extras = unit.get("extra_anchors", [])
            if not isinstance(extras, list) or any(not isinstance(v, str) for v in extras):
                error(f"{ident}: invalid extra_anchors")
                extras = []
            missing = (expected | set(extras)) - set(found)
            if missing:
                error(f"{ident}: missing anchors: {', '.join(sorted(missing))}")
            actual = {v for v in found if re.fullmatch(r"p\d{4,}", v)}
            if actual - expected:
                error(f"{ident}: paragraph count omits source anchors")
            if len(found) != len(set(found)):
                error(f"{ident}: duplicate source anchors")
        elif ranges or status == "completed":
            error(f"{ident}: no source for reading coverage")

    for file in root.rglob("*.md"):
        text = outside_code(file.read_text(encoding="utf-8-sig"))
        # Standard inline links, with angle-wrapped paths for spaces.
        for match in re.finditer(r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[\"\'][^\n]*[\"\'])?\s*\)", text):
            value = match[1].strip("<>")
            parts = urlsplit(value)
            if parts.scheme or parts.netloc:
                continue
            target = (file.parent / unquote(parts.path)).resolve() if parts.path else file
            label = str(file.relative_to(root))
            if not target.is_relative_to(root):
                error(f"{label}: link outside Wiki: {value}")
                continue
            if not target.is_file() or not target.read_bytes().strip():
                error(f"{label}: missing or empty link target: {value}")
            elif parts.fragment and target.suffix.lower() == ".md":
                found = anchors(outside_code(target.read_text(encoding="utf-8-sig")))
                if unquote(parts.fragment) not in found:
                    error(f"{label}: missing link anchor: {value}")
    return errors, progress


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    try:
        errors, progress = check(args.root, args.require_complete)
    except (OSError, UnicodeError, ValueError) as exc:
        errors, progress = [str(exc)], []
    for item in progress:
        print(f"PROGRESS: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} structural errors; content needs review.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
