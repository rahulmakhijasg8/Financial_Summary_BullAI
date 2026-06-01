"""Fill the HTML template with data + charts, then render to PDF via Chromium."""
import os
import threading

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "templates")

SETTINGS = {"missing_marker": "NA", "currency_default": "Rs.", "units_default": "cr"}


def _make_env():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                      autoescape=select_autoescape(["html"]))
    missing = SETTINGS["missing_marker"]

    def g(v):                       # get-or-blank: None/""/"nan" -> "NA"
        if v is None:
            return missing
        s = str(v).strip()
        return missing if s == "" or s.lower() == "nan" else s

    def arrow(d):
        return {"up": "▲", "down": "▼", "none": "■"}.get(str(d).lower(), "■")

    def arrow_class(d):
        return {"up": "up", "down": "down", "none": "flat"}.get(str(d).lower(), "flat")

    env.filters.update(g=g, arrow=arrow, arrow_class=arrow_class)
    return env


def render_html(data, charts):
    return _make_env().get_template("report.html").render(
        d=data, charts=charts, settings=SETTINGS)


def render_pdf(data, charts, out_path):
    html = render_html(data, charts)
    err = {}

    # Playwright's sync API dislikes running inside some event loops (e.g. Streamlit),
    # so we run it in its own thread, which always has a clean slate.
    def run():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html, wait_until="load")
                page.pdf(path=out_path, format="A4", print_background=True,
                         margin={"top": "10mm", "bottom": "12mm",
                                 "left": "8mm", "right": "8mm"})
                browser.close()
        except Exception as e:
            err["e"] = e

    t = threading.Thread(target=run)
    t.start()
    t.join()
    if "e" in err:
        raise err["e"]
    return out_path