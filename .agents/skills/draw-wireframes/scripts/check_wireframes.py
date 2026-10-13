#!/usr/bin/env python3
"""Check rendered wireframe HTML against a screen inventory.

Usage:
  python3 -B -I check_wireframes.py --inventory <dir>/screen-inventory.json --dir <dir>

Prints `ok screens=N` and exits 0, or one `path: reason` line per failure and exits 1.
"""
import argparse, hashlib, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

CSS_SRC = Path(__file__).resolve().parent.parent / "references" / "wireframe.css"
_CLASS = re.compile(r"\.([_A-Za-z][_A-Za-z0-9-]*)")
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
        return []
    screens = data if isinstance(data, list) else data.get("screens") if isinstance(data, dict) else None
    if not isinstance(screens, list):
        errors.append(f"{path}: screens must be a list")
        return []
    return screens


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


def slot_name(node):
    name = node.attrs.get("data-slot")
    return name if name in {"frame", "frame-desktop"} else None


def count_primary(node):
    count = 1 if "primary" in node.classes() else 0
    for child in node.children:
        if "frame" in child.classes() or slot_name(child):
            continue
        count += count_primary(child)
    return count


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
        if child is node or "frame" not in child.classes():
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
        label = node.attrs["data-slot"]
        check_primaries(path, node, label, errors)
        if label == "frame-desktop" and node.visible_text().strip():
            if not any("why" in item.classes() for item in walk(node)):
                errors.append(f"{path}: filled desktop frame has no class why")
    if screen is None:
        return
    outside = [
        node for node in walk(tree)
        if ("data-region" in node.attrs or "data-variant" in node.attrs)
        and not any(slot_name(parent) for parent in ancestors(tree, node))
    ]
    if outside:
        errors.append(f"{path}: data-region or data-variant outside a slot")
    regions = string_list(screen, "regions", inv, errors)
    variants = string_list(screen, "variants", inv, errors)
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
    screens = load_inventory(inv, errors)
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
        html_files = sorted(p for p in root.glob("*.html") if p.is_file())
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
