"""Gradio UI for MenuSync on port 8118: upload or pick a sample, see the parsed table and annotated image."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import gradio as gr
import pandas as pd

from menusync.batch import run_batch
from menusync.ocr import reader, unavailable_reason
from menusync.parser import MenuDigitizer, flatten
from menusync.samples import generate

HERE = Path(__file__).resolve().parent
SAMPLES, OUTPUT = HERE / "samples", HERE / "output"
PORT = int(os.getenv("PORT", "8118"))
SERVICE = "headstorm_menu"
sys.path.insert(0, str(HERE.parents[1]))
from common.gradio_theme import CSS, DARK_JS, theme  # noqa: E402

if not any(SAMPLES.glob("*.png")):
    generate(SAMPLES)
EXAMPLES = sorted(str(p) for p in SAMPLES.glob("*.png"))
digitizer = MenuDigitizer()


def parse(image):
    if image is None:
        raise gr.Error("Drop a menu photo or pick a sample below.")
    try:
        menu = digitizer.process(image)
    except RuntimeError as e:
        raise gr.Error(f"{e}. EasyOCR needs its English model once (~100 MB); check the network and retry.") from e
    rows = flatten(menu)
    table = pd.DataFrame(rows)[["category", "item", "price", "confidence"]] if rows else pd.DataFrame()
    annotated = digitizer.annotate(image, menu)
    report = {k: v for k, v in menu.items() if k != "_lines"}
    headline = (f"**{menu['restaurant'] or 'Unknown restaurant'}**: {menu['n_items']} items, "
                f"{menu['n_priced']} with a price, {len(menu['categories'])} categories, "
                f"{menu['ocr_boxes']} OCR boxes.")  # fmt: skip
    return headline, annotated, table, report


def batch():
    s = run_batch(SAMPLES, OUTPUT)
    lines = [f"{s['succeeded']}/{s['files']} files in {s['seconds']}s ({s['seconds_per_file']}s per file); "
             f"{s['items']} items, {s['priced']} priced; {s['failed']} failed (see output/errors.log)."]  # fmt: skip
    if "eval" in s:
        e = s["eval"]
        lines.append(f"Against ground truth: item recall {e['item_recall']:.0%}, price accuracy on found items "
                     f"{e['price_accuracy_on_found']:.0%}, category recall {e['category_recall']:.0%}.")  # fmt: skip
    lines.append("Written: " + ", ".join(s["outputs"]))
    return "\n\n".join(lines), json.loads((OUTPUT / "menus.json").read_text())


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="MenuSync AI") as demo:
        gr.HTML(
            '<header class="top"><h1>MenuSync AI: menu digitization</h1>'
            '<span class="sub">Menu photo to structured items and prices: EasyOCR, then spatial line grouping '
            'that pairs each item with the price on its row.</span>'
            '<span class="badge on">EasyOCR en</span><span class="badge">port 8118</span></header>'
        )
        with gr.Row():
            with gr.Column(scale=1):
                inp = gr.Image(type="pil", label="Menu image", elem_id="input", height=420)
                run = gr.Button("Parse menu", variant="primary", elem_id="run")
            with gr.Column(scale=1):
                headline = gr.Markdown("Drop a menu photo or pick a sample.", elem_id="result")
                table = gr.Dataframe(label="Parsed items", interactive=False, wrap=True)
        with gr.Row():
            annotated = gr.Image(label="Annotated: teal title, rose category, white item, amber price", height=520)
            report = gr.JSON(label="Structured JSON")
        with gr.Accordion("Batch engine over samples/ (writes output/menus.json and menus.csv)", open=False):
            batch_btn = gr.Button("Run batch", elem_id="batch")
            batch_out = gr.Markdown()
            batch_json = gr.JSON(label="output/menus.json")
            batch_btn.click(batch, outputs=[batch_out, batch_json])
        outputs = [headline, annotated, table, report]
        gr.Examples(EXAMPLES, inputs=inp, outputs=outputs, fn=parse, run_on_click=True, cache_examples=False,
                    label="Samples (one click runs the parser)", examples_per_page=5)  # fmt: skip
        run.click(parse, inputs=inp, outputs=outputs)
        inp.upload(parse, inputs=inp, outputs=outputs)
    return demo


def build_app():
    from fastapi import FastAPI

    api = FastAPI(title=SERVICE)

    @api.get("/health")
    def health():
        return {"ok": True, "service": SERVICE, "model_loaded": reader() is not None,
                "ocr_error": unavailable_reason()}  # fmt: skip

    # Gradio 6: theme, css and js are mount/launch arguments, not Blocks arguments
    return gr.mount_gradio_app(api, build_demo(), path="/", theme=theme(), css=CSS, js=DARK_JS)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(build_app(), host="127.0.0.1", port=PORT)
