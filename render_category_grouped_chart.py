from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "category_grouped_chart.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "category_grouped_chart.html"
OUT_PNG = OUT_DIR / "category_grouped_chart.png"


def prepare_categories(raw_categories: list[dict]) -> list[dict]:
    prepared = []

    for item in raw_categories:
        pg_value = item.get("pg", 0.0)
        competitor_value = item.get("competitor", 0.0)

        bars = [
            {
                "label": "P&G",
                "value": pg_value,
                "value_str": f"{pg_value:.2f}%" if pg_value % 1 else f"{int(pg_value)}%",
                "height_pct": max(pg_value, 2.0) if pg_value > 0 else 0.0,
                "class_name": "pg",
            }
        ]

        if competitor_value > 0:
            bars.append(
                {
                    "label": "Конкуренты",
                    "value": competitor_value,
                    "value_str": f"{competitor_value:.2f}%" if competitor_value % 1 else f"{int(competitor_value)}%",
                    "height_pct": max(competitor_value, 2.0),
                    "class_name": "competitor",
                }
            )

        prepared.append(
            {
                "category": item["category"],
                "mention_count": item["mention_count"],
                "bars": bars,
            }
        )

    return prepared


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


def render_png(html_path: Path, png_path: Path, width: int = 1600, height: int = 950) -> None:
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
    raw_categories = [
        {"category": "Baby Care", "pg": 85.71, "competitor": 14.29, "mention_count": 6},
        {"category": "Hair Care", "pg": 100.0, "competitor": 0.0, "mention_count": 4},
        {"category": "Другие", "pg": 75.0, "competitor": 25.0, "mention_count": 3},
    ]

    context = {
        "page_title": "",
        "eyebrow": "Анализ по категориям",
        "main_title": "Доля упоминаний по категориям",
        "subtitle": "",
        "categories": prepare_categories(raw_categories),
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")


if __name__ == "__main__":
    main()