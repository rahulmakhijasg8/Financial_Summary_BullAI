"""One call: file bytes -> finished PDF on disk."""
from . import ingest, extract, charts, render


def generate_report(filename, file_bytes, company_name, out_path):
    text = ingest.load_document(filename, file_bytes)
    data = extract.extract_report_data(text, company_name)
    chart_imgs = charts.build_all(data)
    render.render_pdf(data, chart_imgs, out_path)
    return data