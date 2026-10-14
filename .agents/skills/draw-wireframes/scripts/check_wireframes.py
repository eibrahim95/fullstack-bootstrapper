#!/usr/bin/env python3
"""Check rendered wireframe HTML against a screen inventory.

Usage:
  python3 -B -I check_wireframes.py --inventory <dir>/screen-inventory.json --dir <dir>

Prints `ok screens=N` and exits 0, or one `path: reason` line per failure and exits 1.

Inventory: every story in `stories` is covered by some screen; labels are short; notes, covers,
proposed are well formed. Pages: slots match the inventory, no `data-todo` left, every note is
pinned, proposed regions are marked, no sentence-length text on a frame, shell matches chrome.
It does not judge layout quality: screenshot and look.
"""
import argparse, hashlib, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

CSS_SRC = Path(__file__).resolve().parent.parent / "references" / "wireframe.css"
_CLASS = re.compile(r"\.([_A-Za-z][_A-Za-z0-9-]*)")
MAX_LABEL_WORDS = 6
MAX_TEXT_WORDS = 14
MAX_FRAME_WORDS = 150
_FORBIDDEN = ("<style", "style=", "<script", "http://", "https://", "javascript:", "data:")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def css_classes(text):
    return set(_CLASS.findall(text))


def load_inventory(path, errors):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"{path}: {e}")
        return {}, []
    screens = data.get("screens") if isinstance(data, dict) else None
    if not isinstance(screens, list):
        errors.append(f"{path}: screens must be a list")
        return {}, []
    return data, screens


def int_list(val):
    return isinstance(val, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in val)


def words(text):
    return len(text.split())


def check_inventory(data, screens, inv, errors):
    stories = data.get("stories")
    if not int_list(stories) or not stories:
        errors.append(f"{inv}: stories must be a non-empty list of spec story numbers")
        stories = []
    covered = set()
    for screen in screens:
        if not isinstance(screen, dict):
            continue
        sid = screen.get("id")
        covers = screen.get("covers", [])
        if not int_list(covers):
            errors.append(f"{inv}: screen {sid!r} covers must be a list of story numbers")
            covers = []
        if not covers and screen.get("grounded") != "no":
            errors.append(f"{inv}: screen {sid!r} covers no story; set grounded no if the spec does not ask for it")
        for c in covers:
            if stories and c not in stories:
                errors.append(f"{inv}: screen {sid!r} covers {c} which is not in stories")
        covered.update(covers)
        for key in ("regions", "variants"):
            for label in screen.get(key) or []:
                if isinstance(label, str) and words(label) > MAX_LABEL_WORDS:
                    errors.append(
                        f"{inv}: screen {sid!r} {key[:-1]} {label!r} has over {MAX_LABEL_WORDS} words; "
                        "name the UI part and move the sentence to notes"
                    )
        notes = screen.get("notes", [])
        if not isinstance(notes, list):
            errors.append(f"{inv}: screen {sid!r} notes is not a list")
            notes = []
        for n, note in enumerate(notes, 1):
            if not isinstance(note, dict) or not isinstance(note.get("text"), str) or not note["text"].strip():
                errors.append(f"{inv}: screen {sid!r} note {n} needs text")
                continue
            if "covers" in note and not int_list(note["covers"]):
                errors.append(f"{inv}: screen {sid!r} note {n} covers must be story numbers")
            else:
                covered.update(note.get("covers", []))
        proposed = screen.get("proposed", [])
        regions = screen.get("regions") or []
        if not isinstance(proposed, list) or any(p not in regions for p in proposed):
            errors.append(f"{inv}: screen {sid!r} proposed must list some of its regions")
    for story in stories:
        if story not in covered:
            errors.append(f"{inv}: story {story} is covered by no screen")


def string_list(screen, key, inv, errors):
    sid = screen.get("id")
    val = screen.get(key)
    if not isinstance(val, list) or not all(isinstance(item, str) for item in val):
        errors.append(f"{inv}: screen {sid!r} {key} is not a list of strings")
        return None
    return val


class Node:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = {key: (val if val is not None else "") for key, val in attrs}
        self.children = []
        self.texts = []

    def classes(self):
        return [token for token in self.attrs.get("class", "").split() if token]

    def visible_text(self):
        parts = list(self.texts)
        for child in self.children:
            parts.append(child.visible_text())
        return "".join(parts)


class Tree(HTMLParser):
    _VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", [])
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag.lower() not in self._VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        want = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag.lower() == want:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].texts.append(data)


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


SLOTS = {"frame", "frame-desktop", "frame-mirror", "states"}


def slot_name(node):
    name = node.attrs.get("data-slot")
    return name if name in SLOTS else None


def boxed(node):
    return "frame" in node.classes() or "state" in node.classes() or slot_name(node)


def count_primary(node):
    count = 1 if "primary" in node.classes() else 0
    for child in node.children:
        if boxed(child):
            continue
        count += count_primary(child)
    return count


def own_texts(node):
    for item in walk(node):
        if "pin" in item.classes():
            continue
        for text in item.texts:
            if text.strip():
                yield text.strip()


def link_target(href, page, root):
    if href is None or href.strip() == "":
        return None
    bare = href.split("#", 1)[0].strip()
    if bare == "" or "://" in bare or bare.startswith("//"):
        return None
    target = (page.parent / bare).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    if not target.is_file():
        return None
    return target


def parse_tree(raw):
    tree = Tree()
    tree.feed(raw)
    tree.close()
    return tree.root


def marked(root, attr):
    return [node.attrs[attr] for node in walk(root) if attr in node.attrs]


def check_attrs(path, root, errors):
    hrefs = []
    stylesheets = []
    classes = []
    for node in walk(root):
        classes.extend(node.classes())
        for key, val in node.attrs.items():
            low_key = key.lower()
            low_val = val.lower()
            if low_key.startswith("on"):
                errors.append(f"{path}: attribute {key} is not allowed")
            if "javascript:" in low_val:
                errors.append(f"{path}: attribute {key} uses javascript:")
            if low_key in {"src", "srcset", "action"}:
                errors.append(f"{path}: attribute {key} is not allowed")
        if "href" in node.attrs:
            hrefs.append(node.attrs["href"])
        rel = node.attrs.get("rel", "")
        if node.tag.lower() == "link" and "stylesheet" in rel.split():
            stylesheets.append(node.attrs.get("href"))
    return hrefs, stylesheets, classes


def check_primaries(path, node, label, errors):
    count = count_primary(node)
    if count > 1:
        errors.append(f"{path}: {count} elements with class primary in {label}")
    for child in walk(node):
        if child is node or not ("frame" in child.classes() or "state" in child.classes()):
            continue
        nested = count_primary(child)
        if nested > 1:
            errors.append(f"{path}: {nested} elements with class primary in a variant frame")


def check_page(path, raw, allowed, root, errors, screen=None, inv=None):
    low = raw.lower()
    for token in _FORBIDDEN:
        if token in low:
            errors.append(f"{path}: contains {token!r}")
    try:
        tree = parse_tree(raw)
    except Exception as e:
        errors.append(f"{path}: {e}")
        return
    hrefs, stylesheets, classes = check_attrs(path, tree, errors)
    if len(stylesheets) != 1 or stylesheets[0] != "wireframe.css":
        errors.append(f"{path}: expected one stylesheet link to wireframe.css")
    unknown = sorted({token for token in classes if token not in allowed})
    for token in unknown:
        errors.append(f"{path}: class {token!r} is not in wireframe.css")
    for href in hrefs:
        if link_target(href, path, root) is None:
            errors.append(f"{path}: link {href!r} does not resolve to a file in {root}")
    slots = [node for node in walk(tree) if slot_name(node)]
    for node in slots:
        if node.attrs["data-slot"] == "frame-mirror":
            continue
        label = node.attrs["data-slot"]
        check_primaries(path, node, label, errors)
        if label == "frame-desktop" and node.visible_text().strip():
            if not any("why" in item.classes() for item in walk(node)):
                errors.append(f"{path}: filled desktop frame has no class why")
    if screen is None:
        return
    check_screen(path, tree, slots, screen, errors)
    outside = [
        node for node in walk(tree)
        if ("data-region" in node.attrs or "data-variant" in node.attrs)
        and not any(slot_name(parent) for parent in ancestors(tree, node))
    ]
    if outside:
        errors.append(f"{path}: data-region or data-variant outside a slot")
    regions = string_list(screen, "regions", inv, errors)
    variants = string_list(screen, "variants", inv, errors)
    frame = next((node for node in slots if node.attrs["data-slot"] == "frame"), None)
    if regions is not None and frame is not None:
        missing = sorted(set(regions) - set(marked(frame, "data-region")))
        if missing:
            errors.append(f"{path}: data-region not in the main frame {missing!r}")
    if regions is not None:
        found, expected = set(marked(tree, "data-region")), set(regions)
        if found != expected:
            errors.append(
                f"{path}: data-region missing {sorted(expected - found)!r} extra {sorted(found - expected)!r}"
            )
        for region in regions:
            if "TBD" not in region:
                continue
            texts = [node.visible_text() for node in walk(tree) if node.attrs.get("data-region") == region]
            if not texts or any("TBD" not in text for text in texts):
                errors.append(f"{path}: visible text for region {region!r} does not contain TBD")
    if variants is not None:
        found, expected = set(marked(tree, "data-variant")), set(variants)
        if found != expected:
            errors.append(
                f"{path}: data-variant missing {sorted(expected - found)!r} extra {sorted(found - expected)!r}"
            )
        for variant in variants:
            if "TBD" not in variant:
                continue
            texts = [node.visible_text() for node in walk(tree) if node.attrs.get("data-variant") == variant]
            if not texts or any("TBD" not in text for text in texts):
                errors.append(f"{path}: visible text for variant {variant!r} does not contain TBD")


def check_screen(path, tree, slots, screen, errors):
    by_name = {node.attrs["data-slot"]: node for node in slots}
    frame = by_name.get("frame")
    if frame is None:
        errors.append(f"{path}: no data-slot frame")
        return
    for node in slots:
        if node.attrs["data-slot"] == "frame-mirror":
            continue
        if any("data-todo" in item.attrs for item in walk(node)):
            todos = sorted({item.attrs["data-todo"] for item in walk(node) if "data-todo" in item.attrs})
            errors.append(f"{path}: template placeholder left in {node.attrs['data-slot']}: {todos!r}")
    for node in slots:
        if node.attrs["data-slot"] == "frame-mirror":
            continue
        for text in own_texts(node):
            if words(text) > MAX_TEXT_WORDS:
                errors.append(f"{path}: sentence on a frame ({words(text)} words), move it to notes: {text[:60]!r}")
    total = sum(words(t) for t in own_texts(frame))
    if total > MAX_FRAME_WORDS:
        errors.append(f"{path}: {total} words in the main frame (max {MAX_FRAME_WORDS}); use labels, lines, notes")
    notes = screen.get("notes") or []
    pins = [item for item in walk(frame) if "data-note" in item.attrs]
    pinned = {item.attrs["data-note"] for item in pins}
    for n in range(1, len(notes) + 1):
        if str(n) not in pinned:
            errors.append(f"{path}: note {n} has no pin (data-note=\"{n}\") in the main frame")
    for item in pins:
        if "pin" not in item.classes():
            errors.append(f"{path}: data-note {item.attrs['data-note']!r} element needs class pin")
        if item.attrs["data-note"] not in {str(n) for n in range(1, len(notes) + 1)}:
            errors.append(f"{path}: pin {item.attrs['data-note']!r} has no note")
    for label in screen.get("proposed") or []:
        nodes = [item for item in walk(tree) if item.attrs.get("data-region") == label]
        if any("proposed" not in item.classes() for item in nodes):
            errors.append(f"{path}: proposed region {label!r} needs class proposed")
    chrome = screen.get("chrome")
    shells = {item.attrs.get("data-shell") for item in walk(tree) if "data-shell" in item.attrs}
    nav_bar = "sidebar" if screen.get("platform") == "desktop" else "tabbar"
    want = {"app": {"appbar", nav_bar}, "focus": {"appbar"}, "none": set()}.get(chrome)
    if want is None:
        errors.append(f"{path}: chrome {chrome!r} is not app, focus or none")
    elif not want <= shells or (chrome != "app" and shells & {"tabbar", "sidebar"}):
        errors.append(f"{path}: shell does not match chrome {chrome!r}; rerun the render script")
    mirror = by_name.get("frame-mirror")
    if mirror is not None and marked(mirror, "data-region") != marked(frame, "data-region"):
        errors.append(f"{path}: desktop mirror is stale; rerun the render script")
    desk = by_name.get("frame-desktop")
    platform = screen.get("platform") or "both"
    if platform == "both" and mirror is None and (desk is None or not desk.visible_text().strip()):
        errors.append(f"{path}: platform both has no desktop view; rerun the render script")
    variants = screen.get("variants") or []
    shown = set(marked(frame, "data-variant"))
    if "states" in by_name:
        shown |= set(marked(by_name["states"], "data-variant"))
    for v in variants:
        if v not in shown:
            errors.append(f"{path}: variant {v!r} is not in the main frame or the states slot")


def ancestors(root, target):
    found = []

    def walk_to(node, chain):
        if node is target:
            found.extend(chain)
            return True
        for child in node.children:
            if walk_to(child, chain + [node]):
                return True
        return False

    walk_to(root, [])
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--dir", required=True, dest="directory")
    args = ap.parse_args()
    inv = Path(args.inventory)
    root = Path(args.directory)
    errors = []
    data, screens = load_inventory(inv, errors)
    if data:
        check_inventory(data, screens, inv, errors)
    if not CSS_SRC.is_file():
        errors.append(f"{CSS_SRC}: missing wireframe.css")
        allowed = set()
    else:
        allowed = css_classes(CSS_SRC.read_text(encoding="utf-8"))
    css_copy = root / "wireframe.css"
    if not css_copy.is_file():
        errors.append(f"{css_copy}: missing wireframe.css")
    elif CSS_SRC.is_file() and digest(css_copy) != digest(CSS_SRC):
        errors.append(f"{css_copy}: hash does not match {CSS_SRC}")

    by_id = {}
    for screen in screens:
        if not isinstance(screen, dict) or not isinstance(screen.get("id"), str):
            errors.append(f"{inv}: screen missing id")
            continue
        sid = screen["id"]
        if sid in by_id:
            errors.append(f"{inv}: duplicate screen id {sid!r}")
            continue
        by_id[sid] = screen
        page = root / (sid + ".html")
        if not page.is_file():
            errors.append(f"{page}: no file for inventory id {sid!r}")

    if root.is_dir():
        html_files = sorted(p for p in root.glob("*.html") if p.is_file() and p.name != "fills.html")
    else:
        html_files = []
        errors.append(f"{root}: not a directory")
    for path in html_files:
        if path.name == "index.html":
            screen = None
        elif path.stem in by_id:
            screen = by_id[path.stem]
        else:
            errors.append(f"{path}: no inventory id for this file")
            screen = None
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            errors.append(f"{path}: {e}")
            continue
        check_page(path, raw, allowed, root.resolve(), errors, screen=screen, inv=inv)

    if errors:
        print("\n".join(errors))
        return 1
    print(f"ok screens={len(by_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
