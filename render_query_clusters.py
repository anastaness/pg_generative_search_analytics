from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "query_clusters.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "query_clusters.html"
OUT_PNG = OUT_DIR / "query_clusters.png"


def render_html(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(TEMPLATE_NAME)
    return template.render(**context)


def save_html(html: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def render_png(html_path: Path, png_path: Path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        page.goto(html_path.resolve().as_uri())
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()


def main():

    clusters = [
        {
            "name": "Hair Care",
            "class": "hair",
            "queries": [
                "head shoulders или vichy",
                "head shoulders шампунь ментол",
                "head shoulders шампунь против перхоти",
                "pantene pro v интенсивное восстановление",
                "pantene или elseve",
            ],
        },
        {
            "name": "Oral Care",
            "class": "oral",
            "queries": [
                "oral b io series",
            ],
        },
        {
            "name": "Baby Care",
            "class": "baby",
            "queries": [
                "pampers premium care 1",
                "pampers premium care размеры",
                "pampers или merries для новорожденных",
                "подгузники для недоношенных детей",
                "рейтинг подгузников для новорожденных 2026",
            ],
        },
        {
            "name": "Other",
            "class": "other",
            "queries": [],
        },
    ]

    context = {
        "title": "Кластеры сильных запросов",
        "clusters": clusters,
    }

    html = render_html(context)

    save_html(html, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print("PNG:", OUT_PNG.resolve())


if __name__ == "__main__":
    main()