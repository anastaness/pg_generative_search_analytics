from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "chart_1.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "chart_1.html"
OUT_PNG = OUT_DIR / "chart_1.png"


def build_chart_items(items: list[dict]) -> list[dict]:
    """
    Для каждого графика считаем высоты столбцов в процентах от максимума в его группе.
    """
    prepared = []

    for chart in items:
        values = [bar["value"] for bar in chart["bars"]]
        max_value = max(values) if values else 1.0
        max_value = max(max_value, 1e-9)

        bars = []
        for bar in chart["bars"]:
            height_pct = (bar["value"] / max_value) * 100
            bars.append(
                {
                    "label": bar["label"],
                    "value": bar["value"],
                    "value_str": f'{bar["value"]:.2f}%',
                    "height_pct": height_pct,
                    "class_name": bar["class_name"],
                }
            )

        prepared.append(
            {
                "title": chart["title"],
                "bars": bars,
                "max_str": f"{max_value:.2f}%",
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
    charts = [
        {
            "title": "Доля упоминаний нейросетью",
            "bars": [
                {"label": "P&G", "value": 86.67, "class_name": "pg"},
                {"label": "Конкуренты", "value": 13.33, "class_name": "competitor"},
            ],
        },
        {
            "title": "Охват запросов",
            "bars": [
                {"label": "P&G", "value": 4.39, "class_name": "pg"},
                {"label": "Конкуренты", "value": 0.68, "class_name": "competitor"},
            ],
        },
    ]

    context = {
        "page_title": "Первоначальный анализ",
        "main_title": "Сравнение P&G и конкурентов",
        "charts": build_chart_items(charts),
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")


if __name__ == "__main__":
    main()