"""Deterministic illustrations are controls, never photographs of a real offer."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

FOLDER = Path(__file__).parents[1] / "fixtures/listing"


def generate_assessment_corpus() -> None:
    manifest = FOLDER / "assessment_cases.json"
    value = json.loads(manifest.read_text())
    target = FOLDER / "assessment_images"
    target.mkdir(exist_ok=True)
    for case in value["cases"]:
        if case["kind"] != "synthetic_control":
            continue
        path = target / (case["id"] + ".png")
        _illustration(path, case["category"], case["illustration_scenario"])
        case["photos"] = [
            dict(
                id=case["id"],
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                path="assessment_images/" + path.name,
                width=640,
                height=480,
                provenance="Project-created deterministic synthetic illustration",
                authorization="Project-created control",
            )
        ]
    manifest.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _illustration(path: Path, category: str, scenario: str) -> None:
    image = Image.new("RGB", (640, 480), "#ebe7df")
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), "SYNTHETIC CONTROL / NOT A REAL LISTING", fill="#242b28")
    draw.rounded_rectangle(
        (120, 100, 520, 350), radius=15, fill="#586b62", outline="#242b28", width=5
    )
    if category == "camera":
        draw.ellipse((210, 140, 430, 350), fill="#a8bab0", outline="#242b28", width=15)
    if category in {"computer", "television"}:
        draw.rectangle((140, 120, 500, 320), fill="#b9c2b7", outline="#242b28", width=4)
        draw.polygon([(110, 350), (530, 350), (575, 390), (65, 390)], fill="#586b62")
    if category == "headphone":
        draw.arc((160, 70, 480, 370), 180, 360, fill="#242b28", width=30)
        draw.rectangle((135, 210, 200, 370), fill="#242b28")
        draw.rectangle((440, 210, 505, 370), fill="#242b28")
    if category == "console":
        draw.rectangle((270, 100, 370, 350), fill="#b9c2b7")
    if scenario == "light_wear":
        draw.line((155, 295, 200, 280), fill="#cfd7cc", width=2)
    if scenario == "clear_defect":
        draw.line(
            [(290, 130), (270, 190), (330, 215), (290, 270), (355, 320)], fill="#242b28", width=10
        )
        draw.line((350, 335, 400, 375), fill="#9a451c", width=8)
    if scenario == "suspected":
        draw.ellipse((250, 170, 380, 280), fill="#8a9d90", outline="#a8bab0", width=15)
    image.save(path, "PNG")
