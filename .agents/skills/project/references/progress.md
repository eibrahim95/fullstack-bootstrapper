# progress diagram
Draw on Excalidraw canvas. Not in chat. Not in a file.
Tools: mcp__excalidraw__*. Load schemas via ToolSearch `select:` first. None found: use fallback.

## layout
Per project one row. Ids stable, so later runs update, not redraw.
Coordinates relative to origin (x0, y0). Row y = y0 + 120.
- title text `prj-NN-title` at (x0, y0): `NN <title>: <state>`, fontSize 24.
- 7 rectangles `prj-NN-<step id>`, 160x64, text = step id, fontSize 18.
  Sequential row: idea, validation, spec, journeys, wireframes at x = x0 + i*220 (i = 0..4), y = row y.
  Parallel column, x = x0 + 1160 (gap 120 after wireframes, room for the fork): html-prototype y = row y - 72, bootstrap y = row y + 72. Same x, 80 gap between them, centred on the row line: a fork, never in line with the row.
- text `prj-NN-par` at (x0 + 1160, row y - 104): `parallel`, fontSize 14, strokeColor #868e96.
- 6 arrows `prj-NN-a1`..`a6`: a1-a4 neighbours in the row, a5 wireframes -> html-prototype, a6 wireframes -> bootstrap. Both start at wireframes right edge middle, split up and down. No arrow between html-prototype and bootstrap. Bound start/end.
- Running step: text `prj-NN-run` under it, its `thread` value, fontSize 14.
- Failed step: text `prj-NN-fail`, under that rectangle, its `result` line, fontSize 14.

## colors
| status | backgroundColor | strokeColor | strokeStyle | strokeWidth |
|---|---|---|---|---|
| done | #b2f2bb | #2f9e44 | solid | 2 |
| next | #ffffff | #1971c2 | solid | 4 |
| failed | #ffc9c9 | #e03131 | solid | 2 |
| running | #fff3bf | #f08c00 | solid | 3 |
| skipped | #e9ecef | #868e96 | dashed | 2 |
| pending | #ffffff | #adb5bd | solid | 2 |
next = first pending step after last done step. None pending: no next. html-prototype and bootstrap both pending after wireframes: both next.

## run
1. `describe_scene`. Find `prj-NN-title`: `query_elements` type text, match id.
2. Exists: origin = title position. `update_element` per rectangle (colors, strokeStyle, strokeWidth, x, y per layout) and title text. Missing id (user deleted it, or `prj-NN-par` from older drawing): create again with batch.
   New: origin x = 0, y = scene bounding box bottom + 120 (0 if empty). `batch_create_elements` all elements one call.
3. Failed step: create or update `prj-NN-fail`. Not failed: delete it if present. Same for `prj-NN-run` and running steps.
4. `set_viewport` with `scrollToElementIds` = this project's rectangles.
5. Say in one line: `progress drawn on excalidraw: NN <state>`. No dump of status.json.

## rules
Never clear the canvas. Never touch elements without prefix `prj-`. It may hold other diagrams.
Elements for done steps never deleted.
Tool error (no canvas server): say once, use fallback, go on. Never block pipeline on the diagram.

## fallback
No excalidraw tools: print one mermaid block, tell user `/ensure-mcp excalidraw` for the canvas version.
```mermaid
flowchart LR
  idea --> validation --> spec --> journeys --> wireframes
  wireframes --> html-prototype
  wireframes --> bootstrap
  classDef done fill:#b2f2bb,stroke:#2f9e44
  classDef next fill:#fff,stroke:#1971c2,stroke-width:3px
  classDef failed fill:#ffc9c9,stroke:#e03131
  classDef running fill:#fff3bf,stroke:#f08c00,stroke-width:3px
  classDef skipped fill:#e9ecef,stroke:#868e96,stroke-dasharray:4 3
  classDef pending fill:#fff,stroke:#adb5bd
  class idea,validation done
  class spec next
  class journeys,wireframes,html-prototype,bootstrap pending
```
Class per step from status. Title line above: `NN <title>: <state>`.
