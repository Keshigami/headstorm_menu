<!-- public-top -->
# MenuSync AI

Turns a restaurant menu image into category, item and price rows with EasyOCR plus spatial line grouping, with a batch engine that writes JSON and CSV and scores itself against ground truth. Portfolio, Computer Vision.

**Watch it first:** [the 90-second film](demo/film.mp4) (what it does, how it is built, the proof, the answer) or the [60-second cut](demo/film-60s.mp4). The plain walkthrough with captions is [demo/demo.mp4](demo/demo.mp4).

## Try it in three commands

```bash
git clone https://github.com/Keshigami/headstorm_menu.git && cd headstorm_menu
just setup        # creates the venv with uv (Python 3.11)
just up           # http://127.0.0.1:8118/  (just down to stop)
```

You need [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just) (`brew install uv just` on a Mac). Everything the app needs is in the repo (synthetic sample data where a dataset is used). No API key is needed anywhere in this project. `just test` runs the lint and the offline tests.

Step by step: [docs/Getting-Started.md](docs/Getting-Started.md), then [how it was built](docs/How-It-Was-Built.md), [results](docs/Results.md), [limits](docs/Limits-and-Next-Steps.md) and [the film](docs/The-Film.md). The same pages are on the [wiki](https://github.com/Keshigami/headstorm_menu/wiki).
<!-- /public-top -->
# MenuSync AI: Intelligent Menu Digitization

## Demo walkthrough
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

Restaurant menu images in, structured items and prices out: EasyOCR, then spatial line grouping that pairs each item
with the price on its row, a column splitter for two-column layouts, and a batch engine with per-file error logging.
Gradio demo on port **8118**.

## 1. Problem statement and business impact
- **The problem**: a hospitality-tech client wants competitor pricing across 1,000+ restaurants. Typing menus in by
  hand does not scale.
- **Goal**: turn unstructured menu images into a database of category / item / price with > 90% extraction accuracy.
- **Original claims**: "94% item-price association accuracy", "1,000 menus in under 30 minutes". Measured here:
  100% on five synthetic menus (71 items) and 8 s per menu on CPU, which would be about 2.3 hours per 1,000 on one
  core, not 30 minutes. The batch in the original repo was a sleep loop printing fake success counts; it is gone.

## 2. Technical solution
1. **Preprocessing**: grayscale + bilateral filter (`parser.preprocess`).
2. **OCR**: EasyOCR English, boxes with confidence (`menusync/ocr.py`, one reader per process).
3. **Layout detection**: `split_columns` scans candidate cuts in the middle third of the page, nearest the centre
   first; a cut crossed by at most one box (the centred title) with names and prices on both sides is a column gap.
4. **Line grouping**: boxes sorted by vertical centre; a box within 60% of the median text height of the current line
   joins it; lines are sorted left to right (`group_lines`).
5. **Structure**: an all-caps line is a category; the rightmost price-looking token on a line is the price and the
   rest is the item name; the first line before any category is the restaurant. Prices accept `$12.99`, `S12.99`
   (EasyOCR's usual reading of `$`) and `12,99`. A page-level rule turns `88.00` into `$8.00` when most prices on the
   page show a currency glyph or that same `8` prefix (`_fix_currency_glyph`).
6. **Batch engine**: every image in `samples/` -> `output/menus.json`, `output/menus.csv`, `output/errors.log`,
   `output/summary.json`, and `output/eval.json` when `samples/ground_truth.json` exists.

Stack: Python 3.11 via uv, easyocr (torch underneath), opencv-python-headless, pillow (sample drawing), pandas,
Gradio 5 on FastAPI, pytest.

## 3. Results on this machine
`just headstorm_menu-batch` over the five synthetic menus (`output/eval.json`):

| Measure | Value |
|---|---|
| Files processed / failed | 5 / 0 |
| Items in ground truth | 71 |
| Item recall (fuzzy name match >= 0.8) | 100% |
| Price accuracy on found items | 100% |
| Category recall | 100% |
| Time per menu (CPU, first file includes model load) | 8.1 s average, 4-6 s steady |

Before the column splitter and the currency-glyph rule the same run scored 87% item recall and 92% price accuracy,
with the two-column menu at 27% price accuracy; those two rules are what the "spatial alignment" in the original
description now means in code. These menus are clean renders with four system fonts; photographed menus with shadows,
curved pages and decorative type will score lower, and the batch engine's error log is where those land.

## 4. How to run
```bash
just headstorm_menu-setup     # uv sync, draw samples/menu_01..05.png + ground_truth.json
just headstorm_menu-test      # ruff + pytest (11 tests: 6 pure parsing, 5 with real OCR; OCR tests skip with reason if EasyOCR cannot load)
just headstorm_menu-batch     # output/menus.json, menus.csv, errors.log, eval.json
just headstorm_menu-up        # http://127.0.0.1:8118/
just headstorm_menu-down
```

## 5. Two-minute interviewer walkthrough
1. Open http://127.0.0.1:8118/. Click sample **menu_02**: in a few seconds the headline reads "Harbor Grill: 13 items,
   13 with a price, 5 categories", the table lists category / item / price / confidence, the annotated image boxes the
   title (teal), categories (rose), items (white) and prices (amber).
2. Click **menu_05**, the two-column menu: still one item per row, each with its own column's price. The JSON shows
   `"columns": 2`.
3. Open the **Batch engine** accordion and press **Run batch**: five files, item recall and price accuracy against the
   ground truth, and the paths of the JSON and CSV it wrote.
4. Drop a photo of a real menu to see where it breaks (the honest part of the demo).

## 6. What is real and what is simulated
Real: OCR, the layout and parsing rules, the batch outputs, the evaluation against ground truth. Simulated: the menus
(`menusync/samples.py` draws them with PIL from a fixed item list, with random fonts, colours and a slight tilt) and the
"1,000 menus" scale, which is not run here. The original `batch_engine.py` never opened a file; this one does.

## Standalone repo

Exported from Max's `caltech-capstone` workspace. `common/` is vendored (LLM door, UI tokens). Run: `just setup && just test && just up`.
LLM-backed features read `ANTHROPIC_API_KEY` (or `LLM_PROVIDER` + `OPENAI_API_KEY` / `GOOGLE_API_KEY`); with no key they run in a deterministic offline mode.
Film: `demo/film.mp4` (90 s, what it does, how it is built, the proof, the answer) and `demo/film-60s.mp4` (60 s cut); `demo/demo.mp4` is the plain walkthrough.
