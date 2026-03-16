from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "top_domains_chart.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "top_domains_chart.html"
OUT_PNG = OUT_DIR / "top_domains_chart.png"


def prepare_rows(raw_rows: list[dict]) -> tuple[list[dict], float]:
    max_value = max((item["value"] for item in raw_rows), default=1.0)
    prepared = []

    for idx, item in enumerate(raw_rows, start=1):
        value = float(item["value"])
        prepared.append(
            {
                "rank": idx,
                "domain": item["domain"],
                "value": value,
                "value_str": f"{value:.4f}%",
                "width_pct": (value / max_value * 100) if max_value else 0.0,
                "is_top": idx == 1,
            }
        )

    return prepared, max_value


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


def render_png(html_path: Path, png_path: Path, width: int = 1600, height: int = 980) -> None:
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
    raw_rows = [
        {"domain": "ozon.ru", "value": 11.5179},
        {"domain": "probolezny.ru", "value": 6.3667},
        {"domain": "apteka.ru", "value": 6.2595},
        {"domain": "wildberries.ru", "value": 6.2417},
        {"domain": "market.yandex.ru", "value": 6.1714},
        {"domain": "yandex.ru", "value": 5.8881},
        {"domain": "kp.ru", "value": 5.6667},
        {"domain": "stolichki.ru", "value": 5.0179},
        {"domain": "detmir.ru", "value": 3.7333},
        {"domain": "dzen.ru", "value": 3.0095},
    ]

    rows, max_value = prepare_rows(raw_rows)

    context = {
        "page_title": "Источники с наибольшим процентом цитирования",
        "eyebrow": "Анализ источников",
        "main_title": "Топ источников по доле упоминаний",
        "subtitle": "",
        "rows": rows,
        "max_value": f"{max_value:.4f}%",
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")


if __name__ == "__main__":
    main()
