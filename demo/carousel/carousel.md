# MenuSync AI · carousel

Spec: film/specs/portfolio__headstorm_menu.json · 8 slides, 1080x1350.

## 1/8 Hook

- This menu was an image a moment ago.

## 2/8 The question

- First run: 87% of items found.
- Can two layout rules close the gap?
- first run, items found 87% → after two layout rules 100%

## 3/8 What it does

- MenuSync AI
- Portfolio · Computer Vision
- Menu images to priced rows, scored against ground truth
- max@baluyot ~ $ curl -s :8118/gradio_api/call/parse_1 -d '{"data": [{"path": "samples/menu_01.png", "meta": {"_type": "gradio.FileData"}}]}'

## 4/8 How it is built

- 1. menusync/samples.py draws 5 menus (one two-colum — pandas
- 2. CRNN recogniser, English) and pure-Pytho — easyocr
- 3. EasyOCR (CRAFT detector — easyocr · opencv-python-headless · pillow
- 4. Gradio 5 Blocks on FastAPI (shared theme — Gradio
- 5. Dashboard — HTML + ui.css
- A page rule: 88.00 is really $8.00

## 5/8 The result

- Three runs against the same 71 items
- Run 1: line grouping · 87% · 92%
- Run 2: + column splitter · 100% · 84.5%
- Run 3: + currency-glyph rule · 100% · 100% (highlighted)

## 6/8 The proof

- First sample, one click: category, item, price
- screen: portfolio/headstorm_menu/demo/poster.png

## 7/8 The answer and the limit

- 100%
- items and prices · 71 items · 5 synthetic menus
- Synthetic menus only. Photos will score lower.
- The fake batch loop is gone. And it ships.

## 8/8 Try it

- Try it: drop a real menu photo.
- max@baluyot ~ $ git clone https://github.com/Keshigami/headstorm_menu.git
- max@baluyot ~ $ just headstorm_menu-setup
- max@baluyot ~ $ just headstorm_menu-up
- github.com/Keshigami/headstorm_menu
- Maximus Friedrich Baluyot
- AI & ML Specialist · Applied AI · ML Engineering · Automation

_Maximus Friedrich Baluyot · Caltech CTME · PGC AIML_
