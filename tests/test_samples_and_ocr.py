import json

from PIL import Image

from menusync.batch import run_batch
from menusync.parser import MenuDigitizer


def test_samples_generated(samples):
    files = sorted(samples.glob("menu_*.png"))
    assert len(files) == 5
    truth = json.loads((samples / "ground_truth.json").read_text())
    assert set(truth) == {f.name for f in files}
    im = Image.open(files[0])
    assert im.size[0] >= 800 and im.size[1] >= 1200
    assert sum(len(c["items"]) for c in truth[files[0].name]["categories"]) >= 8


def test_ocr_parses_a_synthetic_menu(samples, ocr_ready):
    truth = json.loads((samples / "ground_truth.json").read_text())["menu_01.png"]
    menu = MenuDigitizer().process(str(samples / "menu_01.png"))
    expected = sum(len(c["items"]) for c in truth["categories"])
    assert menu["n_items"] >= 0.7 * expected, menu
    assert menu["n_priced"] >= 0.6 * expected, menu
    assert len(menu["categories"]) >= 3
    assert MenuDigitizer.annotate(str(samples / "menu_01.png"), menu).size == tuple(menu["image_size"])


def test_batch_writes_outputs_and_eval(samples, ocr_ready, tmp_path):
    s = run_batch(samples, tmp_path, limit=2, log=lambda *_: None)
    assert s["files"] == 2 and s["failed"] == 0 and s["items"] > 10
    assert (tmp_path / "menus.json").exists() and (tmp_path / "menus.csv").exists()
    assert (tmp_path / "errors.log").read_text() == ""
    assert s["eval"]["item_recall"] >= 0.7 and s["eval"]["price_accuracy_on_found"] >= 0.7, s["eval"]


def test_batch_logs_a_bad_file(samples, ocr_ready, tmp_path):
    bad = tmp_path / "in"
    bad.mkdir()
    (bad / "broken.png").write_bytes(b"not an image")
    s = run_batch(bad, tmp_path / "out", log=lambda *_: None)
    assert s["failed"] == 1 and "broken.png" in (tmp_path / "out" / "errors.log").read_text()
