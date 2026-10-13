#!/usr/bin/env python3
"""Render a screen inventory as grayscale HTML wireframes.

Usage:
  python3 -B -I render_wireframes.py --inventory <dir>/screen-inventory.json --out <dir> --round N

Copies references/wireframe.css into <dir>. Writes index.html and <id>.html.
Re-running replaces the shell and keeps data-slot inner HTML byte for byte.
"""
import argparse, datetime, html, json, re, sys
from pathlib import Path

CSS_SRC = Path(__file__).resolve().parent.parent / "references" / "wireframe.css"
_OPEN = re.compile(
    r"""<(?P<tag>[A-Za-z][\w:-]*)\b(?P<before>[^>]*?)\bdata-slot\s*=\s*(?P<q>["'])(?P<slot>frame-desktop|frame)(?P=q)(?P<after>[^>]*)>""",
    re.DOTALL,
)
_TOKEN = re.compile(
    r"<!--.*?-->|<(?P<slash>/?)(?P<name>[A-Za-z][\w:-]*)\b(?P<rest>[^>]*)>",
    re.DOTALL,
)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def esc(text):
    return html.escape(str(text), quote=True)


def safe_id(sid):
    if not isinstance(sid, str) or not sid or sid in {".", "..", "index"}:
        return False
    if Path(sid).name != sid:
        return False
    return "\0" not in sid


def load_inventory(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        die(f"{path}: {e}")
    if isinstance(data, list):
        return {}, "Wireframes", data, None
    if not isinstance(data, dict):
        die(f"{path}: inventory must be an object or a list of screens")
    screens = data.get("screens")
    title = data.get("title") or "Wireframes"
    if not isinstance(title, str):
        die(f"{path}: title must be a string")
    if not isinstance(screens, list):
        die(f"{path}: screens must be a list")
    return data, title, screens, data.get("sections")


def index_screens(screens, inv):
    by_id = {}
    errors = []
    for s in screens:
        if not isinstance(s, dict):
            errors.append(f"{inv}: screen is not an object")
            continue
        sid = s.get("id")
        if not safe_id(sid):
            errors.append(f"{inv}: bad screen id {sid!r}")
            continue
        if sid in by_id:
            errors.append(f"{inv}: duplicate screen id {sid!r}")
            continue
        by_id[sid] = s
    return by_id, errors


def derive_sections(screens):
    """Hubs, then cross-cutting, then one section per other journey. Each screen once."""
    assigned = set()
    out = []

    hubs = []
    for s in screens:
        sid = s.get("id")
        if isinstance(sid, str) and sid.startswith("hub-") and sid not in assigned:
            hubs.append(sid)
            assigned.add(sid)
    if hubs:
        out.append({
            "key": "hubs",
            "title": "Shared hubs (defined once, reused by journeys)",
            "subtitle": "",
            "ids": hubs,
        })

    cross = []
    for s in screens:
        sid = s.get("id")
        if s.get("journey") == "cross-cutting" and sid not in assigned and isinstance(sid, str):
            cross.append(sid)
            assigned.add(sid)
    if cross:
        out.append({
            "key": "cross",
            "title": "Cross-cutting screens",
            "subtitle": "Used by several journeys",
            "ids": cross,
        })

    seen = []
    for s in screens:
        sid = s.get("id")
        journey = s.get("journey")
        if sid in assigned or not journey or journey == "cross-cutting":
            continue
        if journey not in seen:
            seen.append(journey)
    for journey in seen:
        ids = []
        for s in screens:
            sid = s.get("id")
            if s.get("journey") == journey and sid not in assigned and isinstance(sid, str):
                ids.append(sid)
                assigned.add(sid)
        if ids:
            out.append({"key": journey, "title": f"Journey {journey}", "subtitle": "", "ids": ids})
    return out


def resolve_sections(sections, screens, by_id, inv):
    errors = []
    if sections is None or sections == []:
        chosen = derive_sections(screens)
    elif not isinstance(sections, list):
        return [], [f"{inv}: sections is not a list"]
    else:
        chosen = sections

    seen = []
    seen_set = set()
    for sec in chosen:
        if not isinstance(sec, dict):
            errors.append(f"{inv}: section is not an object")
            continue
        ids = sec.get("ids", [])
        if not isinstance(ids, list):
            errors.append(f"{inv}: section {sec.get('key', sec.get('title', ''))!r} ids is not a list")
            continue
        for sid in ids:
            if sid not in by_id:
                errors.append(f"{inv}: section id {sid!r} is not a screen")
                continue
            if sid in seen_set:
                errors.append(f"{inv}: screen {sid!r} is listed more than once")
                continue
            seen.append(sid)
            seen_set.add(sid)
    for s in screens:
        sid = s.get("id")
        if sid in by_id and sid not in seen_set:
            errors.append(f"{inv}: no section for screen {sid!r}")
    return chosen, errors


def check_links(screens, by_id, inv):
    errors = []
    for s in screens:
        sid = s.get("id")
        if sid not in by_id:
            continue
        for field in ("entry_from", "exit_to"):
            vals = s.get(field, [])
            if not isinstance(vals, list):
                errors.append(f"{inv}: screen {sid!r} {field} is not a list")
                continue
            for val in vals:
                if val not in by_id:
                    errors.append(f"{inv}: screen {sid!r} {field} {val!r} is not a screen id")
    return errors


def _close_span(html, start, tag):
    depth = 1
    want = tag.lower()
    for m in _TOKEN.finditer(html, start):
        name = m.group("name")
        if name is None or name.lower() != want:
            continue
        rest = m.group("rest") or ""
        if m.group("slash"):
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
        elif not rest.rstrip().endswith("/"):
            depth += 1
    return None


def find_slots(html):
    found = []
    for m in _OPEN.finditer(html):
        tag = m.group("tag")
        after = m.group("after") or ""
        if after.rstrip().endswith("/"):
            found.append({
                "name": m.group("slot"),
                "elem_start": m.start(),
                "elem_end": m.end(),
                "inner_start": m.end(),
                "inner_end": m.end(),
                "inner": "",
            })
            continue
        closed = _close_span(html, m.end(), tag)
        if closed is None:
            return None, m.group("slot")
        inner_end, elem_end = closed
        found.append({
            "name": m.group("slot"),
            "elem_start": m.start(),
            "elem_end": elem_end,
            "inner_start": m.end(),
            "inner_end": inner_end,
            "inner": html[m.end():inner_end],
        })
    return found, None


def slots_from(html, path):
    """Return (frame_inner, desktop_inner or None). A desktop slot nested in the phone slot is lifted out."""
    found, unclosed = find_slots(html)
    if unclosed:
        die(f"{path}: unclosed data-slot={unclosed!r}")
    names = [item["name"] for item in found]
    if names.count("frame") == 0:
        die(f"{path}: existing page has no data-slot=\"frame\"")
    if names.count("frame") > 1:
        die(f"{path}: more than one data-slot=\"frame\"")
    if names.count("frame-desktop") > 1:
        die(f"{path}: more than one data-slot=\"frame-desktop\"")
    frame = next(item for item in found if item["name"] == "frame")
    desktop = next((item for item in found if item["name"] == "frame-desktop"), None)
    if desktop is None:
        return frame["inner"], None
    inside = frame["inner_start"] <= desktop["elem_start"] and desktop["elem_end"] <= frame["inner_end"]
    if not inside:
        return frame["inner"], desktop["inner"]
    rel_start = desktop["elem_start"] - frame["inner_start"]
    rel_end = desktop["elem_end"] - frame["inner_start"]
    stripped = frame["inner"][:rel_start] + frame["inner"][rel_end:]
    return stripped, desktop["inner"]


def banner(round_n):
    day = datetime.date.today().isoformat()
    return f"Wireframe, not the product. Round {round_n}. {day}."


def document(title, banner_text, body):
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>" + esc(title) + "</title>\n"
        "<link rel=\"stylesheet\" href=\"wireframe.css\">\n"
        "</head>\n"
        "<body>\n"
        "<p class=\"banner\">" + esc(banner_text) + "</p>\n"
        "<p><a href=\"index.html\">Index</a></p>\n"
        + body +
        "</body>\n"
        "</html>\n"
    )


def link_line(label, ids):
    if not ids:
        return "<p>" + label + "</p>\n"
    links = ", ".join(
        "<a href=\"" + esc(i) + ".html\">" + esc(i) + "</a>" for i in ids
    )
    return "<p>" + label + " " + links + "</p>\n"


def device(kind, slot, inner):
    return (
        "<div class=\"" + kind + "\">\n"
        "<div data-slot=\"" + slot + "\">" + inner + "</div>\n"
        "</div>\n"
    )


def screen_body(screen, frame_inner, desktop_inner):
    name = screen.get("name") or screen["id"]
    parts = [
        "<p class=\"title\">" + esc(name) + "</p>\n",
        "<p class=\"note\">" + esc(screen["id"]) + "</p>\n",
        link_line("From", screen.get("entry_from") or []),
        link_line("To", screen.get("exit_to") or []),
        device("phone", "frame", frame_inner),
    ]
    platform = screen.get("platform") or "both"
    if desktop_inner is not None or platform == "both":
        parts.append(device("desktop", "frame-desktop", desktop_inner or ""))
    return "".join(parts)


def index_body(title, screens, sections):
    by_id = {s["id"]: s for s in screens}
    count = len(screens)
    label = "1 screen" if count == 1 else f"{count} screens"
    parts = [
        "<p class=\"title\">" + esc(title) + "</p>\n",
        "<p class=\"text\">" + label + "</p>\n",
    ]
    for sec in sections:
        parts.append("<section>\n")
        heading = sec.get("title") or sec.get("key") or "Screens"
        parts.append("<p class=\"title\">" + esc(heading) + "</p>\n")
        subtitle = sec.get("subtitle") or ""
        if str(subtitle).strip():
            parts.append("<p class=\"note\">" + esc(subtitle) + "</p>\n")
        for sid in sec.get("ids", []):
            name = by_id[sid].get("name") or ""
            line = "<p><a href=\"" + esc(sid) + ".html\">" + esc(sid) + "</a>"
            if name:
                line += " " + esc(name)
            parts.append(line + "</p>\n")
        parts.append("</section>\n")
    return "".join(parts)


def read_existing(out, screens):
    found = {}
    for s in screens:
        sid = s["id"]
        path = out / (sid + ".html")
        if not path.exists():
            found[sid] = ("", None)
            continue
        if not path.is_file():
            die(f"{path}: not a file")
        try:
            html_text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as e:
            die(f"{path}: {e}")
        found[sid] = slots_from(html_text, path)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", required=True, type=int)
    args = ap.parse_args()
    if args.round < 1:
        die("--round must be >= 1")
    inv = Path(args.inventory)
    out = Path(args.out)
    _data, title, screens, sections = load_inventory(inv)
    by_id, errors = index_screens(screens, inv)
    chosen, sec_errors = resolve_sections(sections, screens, by_id, inv)
    errors.extend(sec_errors)
    errors.extend(check_links(screens, by_id, inv))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if not CSS_SRC.is_file():
        die(f"{CSS_SRC}: missing wireframe.css")
    existing = read_existing(out, screens)
    out.mkdir(parents=True, exist_ok=True)
    (out / "wireframe.css").write_bytes(CSS_SRC.read_bytes())
    text = banner(args.round)
    (out / "index.html").write_bytes(
        document(title, text, index_body(title, screens, chosen)).encode("utf-8")
    )
    for s in screens:
        frame_inner, desktop_inner = existing[s["id"]]
        page = document(
            s["id"] + " " + str(s.get("name") or ""),
            text,
            screen_body(s, frame_inner, desktop_inner),
        )
        (out / (s["id"] + ".html")).write_bytes(page.encode("utf-8"))
    print(f"screens={len(screens)} round={args.round} out={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
