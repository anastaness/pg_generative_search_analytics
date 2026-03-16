from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "status_chart.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "status_chart.html"
OUT_PNG = OUT_DIR / "status_chart.png"


def prepare_segments(raw_segments: list[dict]) -> tuple[list[dict], int]:
    total = sum(item["value"] for item in raw_segments)

    prepared = []
    for item in raw_segments:
        value = item["value"]
        pct = (value / total * 100) if total else 0.0
        prepared.append(
            {
                "key": item["key"],
                "label": item["label"],
                "value": value,
                "pct": pct,
                "pct_str": f"{pct:.2f}%",
                "class_name": item["class_name"],
            }
        )

    return prepared, total


def render_html(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(TEMPLATE_NAME)
    return template.render(**context)


def save_html(html_text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def render_png(html_path: Path, png_path: Path, width: int = 1600, height: int = 900) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()


def main() -> None:
    raw_segments = [
        {
            "key": "no_brand_detected",
            "label": "Не представлен ни один бренд",
            "value": 35,
            "class_name": "no-brand",
        },
        {
            "key": "pg_only",
            "label": "Представлен только P&G",
            "value": 11,
            "class_name": "pg-only",
        },
        {
            "key": "both_present",
            "label": "Представлены P&G и конкуренты",
            "value": 2,
            "class_name": "both-present",
        },
    ]

    segments, total = prepare_segments(raw_segments)

    context = {
        "page_title": "Статусы запросов",
        "eyebrow": "Анализ запросов",
        "main_title": "Распределение запросов по статусам",
        "subtitle": "Категория обнаружения брендов",
        "segments": segments,
        "total": total,
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")


if __name__ == "__main__":
    main()
