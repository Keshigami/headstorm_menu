# Getting started

## What you need
- [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just). On a Mac: `brew install uv just`.
- Python 3.11 is installed by uv.
- No API key is needed anywhere in this project.

## Three commands
```bash
git clone https://github.com/Keshigami/headstorm_menu.git && cd headstorm_menu
just setup
just up           # http://127.0.0.1:8118/  (just down to stop)
```
Everything the app needs is in the repo (synthetic sample data where a dataset is used).

## Commands
`just setup`, `just train` where a model is trained, `just up` / `just down`, `just test`, `just demo`.

## What you see
- Run: `just headstorm_menu-setup && just headstorm_menu-up`, open `http://127.0.0.1:8118/`.
- Two-minute walkthrough: (1) click sample menu_02, read the headline and table; (2) click menu_05 (two columns)
  and check the JSON says `"columns": 2`; (3) open the Batch accordion, press "Run batch", read the accuracy line;
  (4) drop a real menu photo to see where it breaks.
- Video clip: `demo/clips/portfolio__headstorm_menu.webm` (recorded by `just demo-video`).
- Sample inputs: `samples/menu_01.png` to `menu_05.png`; menu_02 gives "Harbor Grill: 13 items, 13 with a price,
  5 categories, 33 OCR boxes".

## Try this
Try it: drop a real menu photo.
