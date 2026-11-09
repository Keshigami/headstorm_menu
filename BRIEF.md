---
title: MenuSync AI
group: portfolio
role: Computer Vision
port: 8118
status: working
one_liner: Turns a restaurant menu image into category, item and price rows with EasyOCR plus spatial line grouping, with a batch engine that writes JSON and CSV and scores itself against ground truth.
---
# MenuSync AI

## Demo
<!-- demo:auto -->
![demo](demo/demo.gif)

Full walkthrough with captions: [demo/demo.mp4](demo/demo.mp4) (67 s, 1280x800, animated intro and end card). Run it yourself: `just setup && just up`, then open http://localhost:8118/.

Two-minute walkthrough:
1. Menu digitisation: pick the first sample menu; one click parses it
2. Parsed items: category, item, price, confidence
3. The annotated image: title, categories, items and prices found by OCR
4. Structured JSON for the pricing database
5. The batch engine over every sample menu
6. Files processed, items and prices found, and the accuracy against ground truth
<!-- /demo:auto -->

## Brief
A hospitality-tech client wants competitor pricing across more than a thousand restaurants, and the menus arrive as
images. Typing them in does not scale. This pipeline reads a menu image and returns structured rows (restaurant,
category, item, price) plus an annotated picture, and a batch engine does the same over a folder with an error log
for the unreadable ones. "Solved" means a CSV a pricing analyst can load, with a measured accuracy next to it.

## Tech stack
| Layer | Choice | Why |
|---|---|---|
| Language and runtime | Python 3.11 via uv | easyocr/torch pin cleanly |
| Model or core logic | EasyOCR (CRAFT detector + CRNN recogniser, English) and pure-Python spatial parsing | OCR is the only learned part; the layout rules are testable without it |
| Interface | Gradio 5 Blocks on FastAPI (shared theme in `common/gradio_theme.py`) | Image in, table + annotated image + JSON out, batch button, `/health` |
| Data | `menusync/samples.py` draws 5 menus (one two-column) with `samples/ground_truth.json` | Makes extraction accuracy measurable |
| Tests | pytest (11 tests) | 6 on the parser with hand-made OCR tuples, 5 with real OCR on the samples (skip with reason if the model cannot load) |

## Libraries used
`easyocr` (text boxes with confidence), `opencv-python-headless` (image loading, grayscale, bilateral filter),
`pillow` (drawing the synthetic menus, annotation overlay), `numpy`, `pandas` (the table in the UI), `gradio` (UI),
`fastapi` + `uvicorn` (health and server), `ruff`, `pytest`.

## How it was built
1. Read the original three scripts: `menu_parser.py` had the line-grouping idea (sort by y, join within 15 px, split
   categories on all-caps, price if it has `$` or a dot) but a fixed pixel threshold and no column handling;
   `generate_samples.py` drew one menu; `batch_engine.py` was a sleep loop printing a fake 98% success rate.
2. Rewrote the parser as pure functions on OCR tuples (`group_lines`, `structure`, `parse_price`, `split_columns`)
   so the rules are unit-tested without EasyOCR: the line tolerance scales with the median text height, the price
   regex accepts EasyOCR's `S` for `$`, and the first non-category line is the restaurant.
3. Drew five varied menus (fonts, paper colours, tilt, one two-column) and saved the ground truth with them, then
   wrote the evaluation (fuzzy item match, exact price match, category recall).
4. First measured run: 87% item recall, 92% price accuracy; the two-column menu merged rows across columns. Added the
   column splitter (a centre-first scan for a box-free vertical band with prices on both sides).
5. Second run: 100% items, 84.5% prices; the misses were `$` read as `8` in one serif font. Added the page-level
   currency-glyph rule. Third run: 100% on all four measures.
6. Batch engine with per-file try/except into `errors.log`, JSON + CSV + summary + eval outputs; Gradio UI with
   one-click samples, annotated overlay, table, JSON and a batch button.

## Results
`output/eval.json` on this machine, five synthetic menus, 71 ground-truth items:

| Measure | Value |
|---|---|
| Item recall | 1.00 |
| Price accuracy on found items | 1.00 |
| Category recall | 1.00 |
| Files failed | 0 of 5 |
| Seconds per menu (CPU) | 8.1 average (first file includes model load), 4-6 steady |

The original write-up claimed 94% item-price association; on these clean renders the pipeline is at 100%, which is
the ceiling for the synthetic set and not a number to expect on photographs. A good number on real menu photos would
be 85-90% with the error log catching the rest.

## Demo details
- Run: `just headstorm_menu-setup && just headstorm_menu-up`, open `http://127.0.0.1:8118/`.
- Two-minute walkthrough: (1) click sample menu_02, read the headline and table; (2) click menu_05 (two columns)
  and check the JSON says `"columns": 2`; (3) open the Batch accordion, press "Run batch", read the accuracy line;
  (4) drop a real menu photo to see where it breaks.
- Video clip: `demo/clips/portfolio__headstorm_menu.webm` (recorded by `just demo-video`).
- Sample inputs: `samples/menu_01.png` to `menu_05.png`; menu_02 gives "Harbor Grill: 13 items, 13 with a price,
  5 categories, 33 OCR boxes".

## Limits and next steps
- Synthetic menus only; photographed menus (shadows, curved pages, decorative fonts, multi-line descriptions) are
  untested and will be worse.
- Two columns are handled, three or more and boxed layouts are not; LayoutLM-style document models are the next step.
- The currency-glyph fix is a page-level heuristic; a real menu where most prices start with 8 and no `$` is shown
  would be mis-corrected (prices >= 80 only).
- No dedupe or normalisation across restaurants ("Fries" vs "French Fries"); that is the competitive-database step.
- Throughput is about 8 s per menu on CPU; 1,000 menus is hours, not the 30 minutes claimed, until batched on a GPU.
