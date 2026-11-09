# How it was built

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

## Tech stack
| Layer | Choice | Why |
|---|---|---|
| Language and runtime | Python 3.11 via uv | easyocr/torch pin cleanly |
| Model or core logic | EasyOCR (CRAFT detector + CRNN recogniser, English) and pure-Python spatial parsing | OCR is the only learned part; the layout rules are testable without it |
| Interface | Gradio 5 Blocks on FastAPI (shared theme in `common/gradio_theme.py`) | Image in, table + annotated image + JSON out, batch button, `/health` |
| Data | `menusync/samples.py` draws 5 menus (one two-column) with `samples/ground_truth.json` | Makes extraction accuracy measurable |
| Tests | pytest (11 tests) | 6 on the parser with hand-made OCR tuples, 5 with real OCR on the samples (skip with reason if the model cannot load) |

## Libraries
`easyocr` (text boxes with confidence), `opencv-python-headless` (image loading, grayscale, bilateral filter),
`pillow` (drawing the synthetic menus, annotation overlay), `numpy`, `pandas` (the table in the UI), `gradio` (UI),
`fastapi` + `uvicorn` (health and server), `ruff`, `pytest`.
