#!/usr/bin/env python3
"""Validate journey YAML and render self-contained HTML (boxes, arrows, modal per page).

Usage: render.py <journeys-dir-or-yaml> [--out-dir DIR]
Renders every *.yaml found to <out-dir>/<name>.html (default: next to the yaml)
and writes index.html when given a dir. Needs PyYAML (`uv run --with pyyaml ...`).
Exit 1 on validation error. Layout: BFS rows, top-down. Template: ../references/html-template.html
"""
import argparse, collections, glob, html, os, sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML missing: run with `uv run --with pyyaml python3 render.py ...`")

BW, BH, RS, CS, PAD = 220, 80, 140, 40, 40
PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "html-template.html")
E = html.escape


def validate(j):
    errs, warns = [], []
    pages, trans, entry = j.get("pages") or [], j.get("transitions") or [], j.get("entry")
    ids = [p.get("id") for p in pages]
    if not pages: errs.append("no pages")
    if len(set(ids)) != len(ids): errs.append("duplicate page ids")
    if entry not in ids: errs.append(f"entry '{entry}' is not a page id")
    if len(pages) > 12: errs.append(f"{len(pages)} pages > 12: split into two flows")
    if len(trans) > 30: errs.append(f"{len(trans)} transitions > 30: split into two flows")
    for t in trans:
        for k in ("from", "to"):
            if t.get(k) not in ids: errs.append(f"transition {k} '{t.get(k)}' is not a page id")
    if errs: return errs, warns
    adj = collections.defaultdict(list)
    touched = set()
    for t in trans:
        adj[t["from"]].append(t["to"]); touched |= {t["from"], t["to"]}
    seen, q = {entry}, collections.deque([entry])
    while q:
        for n in adj[q.popleft()]:
            if n not in seen: seen.add(n); q.append(n)
    for i in ids:
        if i not in seen: errs.append(f"page '{i}' unreachable from entry")
        if len(ids) > 1 and i not in touched: errs.append(f"page '{i}' is an orphan (no transitions)")
    if not any(p.get("success_state") for p in pages): warns.append("no page has success_state")
    if not any(p.get("error_state") for p in pages): warns.append("no page has error_state")
    return errs, warns


def layout(pages, trans, entry):
    adj = collections.defaultdict(list)
    for t in trans: adj[t["from"]].append(t["to"])
    depth, q = {}, collections.deque([(entry, 0)])
    while q:
        n, d = q.popleft()
        if n in depth: continue
        depth[n] = d
        q.extend((x, d + 1) for x in adj[n] if x not in depth)
    rows = collections.defaultdict(list)
    for p in pages: rows[depth[p["id"]]].append(p["id"])
    widest = max(len(r) for r in rows.values())
    w = widest * BW + (widest - 1) * CS + 2 * PAD
    h = (max(rows) * RS) + BH + 2 * PAD
    pos = {}
    for d, row in rows.items():
        x0 = (w - (len(row) * BW + (len(row) - 1) * CS)) // 2
        for i, pid in enumerate(row): pos[pid] = (x0 + i * (BW + CS), PAD + d * RS)
    return pos, w, h


def render(j, src):
    pages, trans, entry = j["pages"], j.get("transitions") or [], j["entry"]
    pos, w, h = layout(pages, trans, entry)
    title_of = {p["id"]: p.get("title", p["id"]) for p in pages}
    personas = list(j.get("personas") or [])
    boxes, arrows = [], []
    for p in pages:
        pid, (x, y) = p["id"], pos[p["id"]]
        cx, per = x + BW // 2, p.get("persona") or ""
        pa = f' data-persona="{E(per)}"' if per else ""
        pt = f'<tspan class="page-persona" x="{cx}" dy="18">{E(per)}</tspan>' if per else ""
        boxes.append(f'<g class="page-box" id="page-{E(pid)}" data-page-id="{E(pid)}"{pa} tabindex="0" role="button" aria-label="Open details for {E(title_of[pid])}">'
                     f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="8"/><text x="{cx}" y="{y + BH // 2 - (8 if per else 0)}" text-anchor="middle" dominant-baseline="middle">'
                     f'<tspan class="page-title" x="{cx}">{E(title_of[pid])}</tspan>{pt}</text></g>')
    for t in trans:
        (fx, fy), (tx, ty) = pos[t["from"]], pos[t["to"]]
        x1, y1, x2, y2 = fx + BW // 2, fy + BH, tx + BW // 2, ty
        if t["from"] == t["to"]:
            x1, y1, x2, y2 = fx + BW, fy + BH // 2, fx + BW, fy + BH // 2 + 20
            d = f"M{x1},{y1} C{x1 + 70},{y1 - 20} {x1 + 70},{y2 + 20} {x2},{y2}"; lx, ly = x1 + 60, (y1 + y2) // 2
        elif y2 <= y1:
            if fy == ty: x1, y1, x2, y2 = fx + BW, fy + BH // 2, tx, ty + BH // 2
            else: y1, y2 = fy + BH // 2, ty + BH // 2; x1, x2 = fx + BW, tx + BW
            mx = max(x1, x2) + 60
            d = f"M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}"; lx, ly = mx, (y1 + y2) // 2
        else:
            my = (y1 + y2) // 2
            d = f"M{x1},{y1} C{x1},{my} {x2},{my} {x2},{y2}"; lx, ly = (x1 + x2) // 2, my
        arrows.append(f'<path class="transition-arrow" d="{d}" marker-end="url(#arrowhead)"/>')
        if t.get("trigger"):
            arrows.append(f'<text class="transition-label" x="{lx}" y="{ly}" text-anchor="middle">{E(str(t["trigger"]))}</text>')
    inc, out = collections.defaultdict(list), collections.defaultdict(list)
    for t in trans: out[t["from"]].append(t); inc[t["to"]].append(t)
    modals = []
    for p in pages:
        pid, e = p["id"], E(p["id"])
        pill = f'<span class="persona-pill">{E(p["persona"])}</span>' if p.get("persona") else ""
        c = p.get("contents") or []
        contents = "<ul>" + "".join(f"<li>{E(str(i))}</li>" for i in c) + "</ul>" if c else "<p><em>No contents specified.</em></p>"
        st = lambda k, lbl: f'<section><h3>{lbl}</h3><p>{E(str(p[k]))}</p></section>' if p.get(k) else ""
        li_in = "".join(f'<li>from <strong>{E(title_of[t["from"]])}</strong> on {E(str(t.get("trigger", "")))}</li>' for t in inc[pid]) or "<li><em>None (entry page).</em></li>"
        li_out = "".join(f'<li>to <strong>{E(title_of[t["to"]])}</strong> on {E(str(t.get("trigger", "")))}</li>' for t in out[pid]) or "<li><em>None (terminal page).</em></li>"
        img = f'<section><h3>Reference image</h3><img src="{E(p["image"])}" alt=""></section>' if p.get("image") else ""
        modals.append(f'<div class="modal" id="modal-{e}" role="dialog" aria-modal="true" aria-labelledby="modal-title-{e}" hidden>'
                      f'<div class="modal-backdrop" data-close-modal="{e}"></div><div class="modal-content">'
                      f'<div class="modal-head"><h2 id="modal-title-{e}">{E(title_of[pid])}</h2>{pill}<button class="modal-close" data-close-modal="{e}" aria-label="Close">&times;</button></div>'
                      f'<section><p>{E(p.get("description", ""))}</p></section><section><h3>Page contents</h3>{contents}</section>'
                      f'{st("success_state", "Success state")}{st("error_state", "Error / edge state")}'
                      f'<section><h3>Transitions in</h3><ul>{li_in}</ul></section><section><h3>Transitions out</h3><ul>{li_out}</ul></section>{img}</div></div>')
    pcss = "\n".join(f'.page-box[data-persona="{E(p)}"] rect {{ stroke: {PALETTE[i % 5]}; }}' for i, p in enumerate(personas))
    vals = {"TITLE": E(j.get("title") or j.get("flow") or j.get("feature") or "Journey"), "PROJECT": E(str(j.get("project", ""))),
            "DESCRIPTION": E(str(j.get("description", ""))), "GENERATED": E(str(j.get("generated_at", ""))), "WIDTH": str(w), "HEIGHT": str(h),
            "ARROWS": "".join(arrows), "BOXES": "".join(boxes), "MODALS": "".join(modals), "SOURCE": E(src),
            "NOTES": E(str(j.get("notes") or "").strip()), "PERSONA_CSS": pcss}
    doc = open(TEMPLATE, encoding="utf-8").read()
    for k, v in vals.items(): doc = doc.replace("{{" + k + "}}", v)
    return doc


def index_html(items):
    lis = "".join(f'<li><a href="{E(n)}.html">{E(t)}</a> <small>{np} pages, {nt} transitions</small></li>' for n, t, np, nt in items)
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>User journeys</title><style>body{font-family:system-ui,sans-serif;margin:32px;color:#1f2937;background:#f9fafb}li{margin:8px 0}small{color:#6b7280}</style></head>'
            f'<body><h1>User journeys</h1><ul>{lis}</ul></body></html>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--out-dir")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.path, "*.yaml"))) if os.path.isdir(a.path) else [a.path]
    if not files: sys.exit("no yaml files")
    items, bad = [], False
    for f in files:
        j = yaml.safe_load(open(f, encoding="utf-8"))
        errs, warns = validate(j if isinstance(j, dict) else {})
        name = os.path.splitext(os.path.basename(f))[0]
        for m in warns: print(f"WARN {name}: {m}")
        for m in errs: print(f"ERROR {name}: {m}"); bad = True
        if errs: continue
        od = a.out_dir or os.path.dirname(os.path.abspath(f)); os.makedirs(od, exist_ok=True)
        open(os.path.join(od, name + ".html"), "w", encoding="utf-8").write(render(j, name + ".yaml"))
        items.append((name, j.get("title") or name, len(j["pages"]), len(j.get("transitions") or [])))
        print(f"OK {name}: {items[-1][2]} pages, {items[-1][3]} transitions")
    if items and os.path.isdir(a.path):
        open(os.path.join(a.out_dir or a.path, "index.html"), "w", encoding="utf-8").write(index_html(items))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
