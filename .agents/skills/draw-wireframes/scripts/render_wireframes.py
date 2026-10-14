#!/usr/bin/env python3
"""Render a screen inventory as grayscale HTML wireframes.

Usage:
  python3 -B -I render_wireframes.py --inventory <dir>/screen-inventory.json --out <dir> --round N [--fills <dir>/fills.html] [--reset-slots]

Copies references/wireframe.css into <dir>. Writes index.html (overview) and <id>.html per screen.
The script draws the shell (app bar, tab bar, sidebar), the phone and desktop frames, the notes
panel, and the desktop mirror. The agent fills three slots: frame (screen content), states
(one mini frame per variant), frame-desktop (only when the wide layout differs).
An empty frame slot is seeded from references/layouts/<layout>.html; an empty states slot gets
one seeded mini frame per variant. Re-running keeps slot inner HTML byte for byte, unless
--reset-slots is passed, which re-seeds every slot.
--fills names a file of <template data-screen="<id>" data-fill="<slot>">...</template> blocks
(format: fixtures/filled-slots.html). A block replaces that slot; it wins over the page and the seed.
"""
import argparse, datetime, html, json, re, sys
from typing import NoReturn
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "references"
CSS_SRC = REF / "wireframe.css"
LAYOUT_DIR = REF / "layouts"
CHROMES = ("app", "focus", "none")
PLATFORMS = ("phone", "desktop", "both")
KEPT = ("frame", "frame-desktop", "states")
_OPEN = re.compile(
    r"""<(?P<tag>[A-Za-z][\w:-]*)\b(?P<before>[^>]*?)\bdata-slot\s*=\s*(?P<q>["'])(?P<slot>frame-desktop|frame-mirror|frame|states)(?P=q)(?P<after>[^>]*)>""",
    re.DOTALL,
)
_FILL = re.compile(r'<template data-screen="([^"]+)" data-fill="([^"]+)">\n?(.*?)\n?</template>', re.DOTALL)
_TOKEN = re.compile(
    r"<!--.*?-->|<(?P<slash>/?)(?P<name>[A-Za-z][\w:-]*)\b(?P<rest>[^>]*)>",
    re.DOTALL,
)


def die(msg) -> NoReturn:
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


def layouts():
    return sorted(p.stem for p in LAYOUT_DIR.glob("*.html"))


def load_inventory(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        die(f"{path}: {e}")
    if not isinstance(data, dict):
        die(f"{path}: inventory must be an object")
    screens = data.get("screens")
    title = data.get("title") or "Wireframes"
    if not isinstance(title, str):
        die(f"{path}: title must be a string")
    if not isinstance(screens, list):
        die(f"{path}: screens must be a list")
    return data, title, screens, data.get("sections")


def load_shell(data, inv):
    shell = data.get("shell") or {}
    errors = []
    if not isinstance(shell, dict):
        return {}, [f"{inv}: shell must be an object"]
    nav = shell.get("nav", [])
    if not isinstance(nav, list) or not all(isinstance(item, str) and item for item in nav):
        errors.append(f"{inv}: shell nav must be a list of strings")
        nav = []
    brand = shell.get("brand") or data.get("title") or ""
    proposed = shell.get("proposed", [])
    if not isinstance(proposed, list) or not all(item in nav for item in proposed):
        errors.append(f"{inv}: shell proposed must list nav items")
        proposed = []
    return {"brand": str(brand), "nav": nav, "proposed": proposed}, errors


def index_screens(screens, inv, shell, known_layouts):
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
        if s.get("layout") not in known_layouts:
            errors.append(f"{inv}: screen {sid!r} layout {s.get('layout')!r} is not one of {known_layouts}")
        if s.get("chrome") not in CHROMES:
            errors.append(f"{inv}: screen {sid!r} chrome {s.get('chrome')!r} is not one of {list(CHROMES)}")
        if (s.get("platform") or "both") not in PLATFORMS:
            errors.append(f"{inv}: screen {sid!r} platform {s.get('platform')!r} is not one of {list(PLATFORMS)}")
        nav = s.get("nav")
        if nav is not None and nav not in shell["nav"]:
            errors.append(f"{inv}: screen {sid!r} nav {nav!r} is not in shell nav")
        if s.get("chrome") == "app" and not shell["nav"]:
            errors.append(f"{inv}: screen {sid!r} chrome app needs shell nav")
        notes = s.get("notes", [])
        if not isinstance(notes, list) or not all(isinstance(n, dict) and isinstance(n.get("text"), str) for n in notes):
            errors.append(f"{inv}: screen {sid!r} notes must be a list of objects with text")
        variants = s.get("variants", [])
        if not isinstance(variants, list) or not all(isinstance(v, str) for v in variants):
            errors.append(f"{inv}: screen {sid!r} variants must be a list of strings")
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


def _close_span(text, start, tag):
    depth = 1
    want = tag.lower()
    for m in _TOKEN.finditer(text, start):
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


def find_slots(text):
    found = []
    pos = 0
    while True:
        m = _OPEN.search(text, pos)
        if m is None:
            return found, None
        after = m.group("after") or ""
        if after.rstrip().endswith("/"):
            found.append({"name": m.group("slot"), "inner": ""})
            pos = m.end()
            continue
        closed = _close_span(text, m.end(), m.group("tag"))
        if closed is None:
            return None, m.group("slot")
        inner_end, elem_end = closed
        found.append({"name": m.group("slot"), "inner": text[m.end():inner_end]})
        # Slots never nest: continue after this one so a mirror copy inside is not read twice.
        pos = elem_end


def slots_from(text, path):
    """Return {slot name: inner} for the kept slots. The mirror is derived, never kept."""
    found, unclosed = find_slots(text)
    if unclosed:
        die(f"{path}: unclosed data-slot={unclosed!r}")
    out = {}
    for item in found:
        name = item["name"]
        if name == "frame-mirror":
            continue
        if name in out:
            die(f"{path}: more than one data-slot=\"{name}\"")
        out[name] = item["inner"]
    if "frame" not in out:
        die(f"{path}: existing page has no data-slot=\"frame\"")
    return out


def seed_frame(layout):
    return "\n" + (LAYOUT_DIR / (layout + ".html")).read_text(encoding="utf-8")


def seed_states(variants):
    parts = ["\n"]
    for v in variants:
        parts.append(
            "<div class=\"state\" data-variant=\"" + esc(v) + "\">"
            "<p class=\"trigger\">" + esc(v) + "</p>"
            "<span class=\"lines\" data-todo=\"draw this state\"></span>"
            "</div>\n"
        )
    return "".join(parts)


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
        return "<p>" + label + " none</p>\n"
    links = ", ".join(
        "<a href=\"" + esc(i) + ".html\">" + esc(i) + "</a>" for i in ids
    )
    return "<p>" + label + " " + links + "</p>\n"


def appbar(screen):
    name = esc(screen.get("name") or screen["id"])
    chrome = screen.get("chrome")
    if chrome == "app":
        return "<div class=\"appbar\" data-shell=\"appbar\"><span>" + name + "</span><span class=\"spacer\"></span><i class=\"icon\">⋯</i></div>\n"
    if chrome == "focus":
        return "<div class=\"appbar\" data-shell=\"appbar\"><span class=\"back\">←</span><span>" + name + "</span></div>\n"
    return ""


def nav_class(base, item, screen, shell):
    cls = base
    if item == screen.get("nav"):
        cls += " on"
    if item in shell["proposed"]:
        cls += " proposed"
    return cls


def tabbar(screen, shell):
    if screen.get("chrome") != "app":
        return ""
    items = "".join(
        "<span class=\"" + nav_class("tab-item", item, screen, shell) + "\">" + esc(item) + "</span>"
        for item in shell["nav"]
    )
    return "<div class=\"tabbar\" data-shell=\"tabbar\">" + items + "</div>\n"


def sidebar(screen, shell):
    if screen.get("chrome") != "app":
        return ""
    items = "".join(
        "<p class=\"" + nav_class("nav-item", item, screen, shell) + "\">" + esc(item) + "</p>"
        for item in shell["nav"]
    )
    return "<div class=\"sidebar\" data-shell=\"sidebar\"><p class=\"brand\">" + esc(shell["brand"]) + "</p>" + items + "</div>\n"


def frame_class(kind, screen):
    return kind + (" proposed" if screen.get("grounded") == "no" else "")


def phone(screen, shell, slot, inner):
    return (
        "<div class=\"" + frame_class("phone", screen) + "\"><div class=\"screen\">\n"
        + appbar(screen)
        + "<div class=\"content\" data-slot=\"" + slot + "\">" + inner + "</div>\n"
        + tabbar(screen, shell)
        + "</div></div>\n"
    )


def desktop(screen, shell, body):
    return (
        "<div class=\"" + frame_class("desktop", screen) + "\"><div class=\"screen\">\n"
        + sidebar(screen, shell)
        + "<div class=\"frame-wrap\">\n" + appbar(screen)
        + "<div class=\"content\">" + body + "</div>\n"
        + "</div>\n</div></div>\n"
    )


def device(caption, frame):
    return "<div class=\"device\"><p class=\"caption\">" + esc(caption) + "</p>\n" + frame + "</div>\n"


def notes_panel(screen):
    notes = screen.get("notes") or []
    if not notes:
        return ""
    items = []
    for n in notes:
        stories = n.get("covers") or []
        tail = ""
        if stories:
            tail = " <span class=\"small\">Story " + esc(", ".join(str(x) for x in stories)) + "</span>"
        items.append("<li>" + esc(n["text"]) + tail + "</li>\n")
    return "<div class=\"device\"><p class=\"caption\">Notes (numbers match the pins)</p>\n<ol class=\"notes\">\n" + "".join(items) + "</ol>\n</div>\n"


def meta_line(screen):
    parts = [
        "Layout " + str(screen.get("layout")),
        "chrome " + str(screen.get("chrome")),
        "platform " + str(screen.get("platform") or "both"),
    ]
    covers = screen.get("covers") or []
    if covers:
        parts.append("stories " + ", ".join(str(c) for c in covers))
    if screen.get("grounded") == "no":
        parts.append("proposed screen, not in the spec")
    return "<p class=\"note\">" + esc(" · ".join(parts)) + "</p>\n"


def screen_body(screen, shell, slots):
    name = screen.get("name") or screen["id"]
    frame_inner = slots.get("frame", "")
    desk_inner = slots.get("frame-desktop", "")
    states_inner = slots.get("states", "")
    platform = screen.get("platform") or "both"
    parts = [
        "<p class=\"title\">" + esc(name) + "</p>\n",
        "<p class=\"note\">" + esc(screen["id"]) + "</p>\n",
        meta_line(screen),
        link_line("From", screen.get("entry_from") or []),
        link_line("To", screen.get("exit_to") or []),
        "<div class=\"board\">\n",
    ]
    if platform == "desktop":
        body = "<div data-slot=\"frame\">" + frame_inner + "</div>"
        parts.append(device("Desktop · 1024 px", desktop(screen, shell, body)))
        parts.append(notes_panel(screen))
    else:
        parts.append(device("Phone · 390 px", phone(screen, shell, "frame", frame_inner)))
        parts.append(notes_panel(screen))
        if platform == "both":
            body = "<div data-slot=\"frame-desktop\">" + desk_inner + "</div>"
            if desk_inner.strip():
                caption = "Desktop · 1024 px · own layout"
            else:
                caption = "Desktop · 1024 px · same content, wide layout"
                body += "<div class=\"mirror\" data-slot=\"frame-mirror\">" + frame_inner + "</div>"
            parts.append(device(caption, desktop(screen, shell, body)))
    parts.append("</div>\n")
    if states_inner.strip():
        parts.append("<p class=\"title\">States</p>\n")
    parts.append("<div class=\"states\" data-slot=\"states\">" + states_inner + "</div>\n")
    return "".join(parts)


def thumb(screen, shell, frame_inner):
    return (
        "<div class=\"thumb\"><div class=\"thumb-in\">"
        + phone(screen, shell, "thumb", frame_inner).replace(" data-slot=\"thumb\"", "")
        + "</div><p><a href=\"" + esc(screen["id"]) + ".html\">" + esc(screen["id"]) + "</a> "
        + esc(screen.get("name") or "") + "</p></div>\n"
    )


def index_body(title, screens, sections, shell, frames):
    by_id = {s["id"]: s for s in screens}
    count = len(screens)
    label = "1 screen" if count == 1 else f"{count} screens"
    parts = [
        "<p class=\"title\">" + esc(title) + "</p>\n",
        "<p class=\"text\">" + label + ". Phone view of each screen. Arrows follow a journey's order. Open a screen for desktop, states, and notes.</p>\n",
    ]
    if shell["proposed"]:
        parts.append("<p class=\"note\">Dashed nav items are proposed, not in the spec: " + esc(", ".join(shell["proposed"])) + ".</p>\n")
    for sec in sections:
        parts.append("<section class=\"overview\">\n")
        heading = sec.get("title") or sec.get("key") or "Screens"
        parts.append("<p class=\"title\">" + esc(heading) + "</p>\n")
        subtitle = sec.get("subtitle") or ""
        if str(subtitle).strip():
            parts.append("<p class=\"note\">" + esc(subtitle) + "</p>\n")
        parts.append("<div class=\"thumbs\">\n")
        ids = sec.get("ids", [])
        journeys = {by_id[sid].get("journey") for sid in ids}
        flow = len(journeys) == 1 and "cross-cutting" not in journeys and not any(sid.startswith(("hub-", "X-")) for sid in ids)
        for n, sid in enumerate(ids):
            if n and flow:
                parts.append("<span class=\"arrow\">→</span>\n")
            parts.append(thumb(by_id[sid], shell, frames[sid]))
        parts.append("</div>\n</section>\n")
    return "".join(parts)


def load_fills(path, by_id):
    fills = {}
    errors = []
    text = Path(path).read_text(encoding="utf-8")
    for sid, slot, inner in _FILL.findall(text):
        if sid not in by_id:
            errors.append(f"{path}: data-screen {sid!r} is not a screen")
        elif slot not in KEPT:
            errors.append(f"{path}: data-fill {slot!r} is not one of {list(KEPT)}")
        elif slot in fills.get(sid, {}):
            errors.append(f"{path}: {sid} {slot} filled twice")
        else:
            fills.setdefault(sid, {})[slot] = "\n" + inner + "\n"
    if text.count("<template") != len(_FILL.findall(text)):
        errors.append(f"{path}: a <template> block is not of the form <template data-screen=\"id\" data-fill=\"slot\">")
    return fills, errors


def read_existing(out, screens, reset, fills):
    found = {}
    for s in screens:
        sid = s["id"]
        path = out / (sid + ".html")
        slots = {}
        if path.exists() and not reset:
            if not path.is_file():
                die(f"{path}: not a file")
            try:
                text = path.read_bytes().decode("utf-8")
            except UnicodeDecodeError as e:
                die(f"{path}: {e}")
            slots = slots_from(text, path)
        slots.update(fills.get(sid, {}))
        if not slots.get("frame", "").strip():
            slots["frame"] = seed_frame(s["layout"])
        if not slots.get("states", "").strip():
            # Variants already drawn as tags in the frame need no mini frame.
            drawn = set(html.unescape(v) for v in re.findall(r'data-variant="([^"]*)"', slots["frame"]))
            missing = [v for v in s.get("variants") or [] if v not in drawn]
            slots["states"] = seed_states(missing) if missing else ""
        found[sid] = slots
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", required=True, type=int)
    ap.add_argument("--reset-slots", action="store_true", help="re-seed every slot not given by --fills")
    ap.add_argument("--fills", help="file of <template data-screen data-fill> blocks that replace slots")
    args = ap.parse_args()
    if args.round < 1:
        die("--round must be >= 1")
    inv = Path(args.inventory)
    out = Path(args.out)
    data, title, screens, sections = load_inventory(inv)
    shell, errors = load_shell(data, inv)
    by_id, screen_errors = index_screens(screens, inv, shell, layouts())
    errors.extend(screen_errors)
    chosen, sec_errors = resolve_sections(sections, screens, by_id, inv)
    errors.extend(sec_errors)
    errors.extend(check_links(screens, by_id, inv))
    fills = {}
    if args.fills and not errors:
        fills, fill_errors = load_fills(args.fills, by_id)
        errors.extend(fill_errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if not CSS_SRC.is_file():
        die(f"{CSS_SRC}: missing wireframe.css")
    existing = read_existing(out, screens, args.reset_slots, fills)
    out.mkdir(parents=True, exist_ok=True)
    (out / "wireframe.css").write_bytes(CSS_SRC.read_bytes())
    text = banner(args.round)
    frames = {sid: slots["frame"] for sid, slots in existing.items()}
    (out / "index.html").write_bytes(
        document(title, text, index_body(title, screens, chosen, shell, frames)).encode("utf-8")
    )
    for s in screens:
        page = document(
            s["id"] + " " + str(s.get("name") or ""),
            text,
            screen_body(s, shell, existing[s["id"]]),
        )
        (out / (s["id"] + ".html")).write_bytes(page.encode("utf-8"))
    print(f"screens={len(screens)} round={args.round} out={out}" + (" reset-slots" if args.reset_slots else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
