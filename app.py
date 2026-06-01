import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src import ingest, pipeline

load_dotenv()
st.set_page_config(page_title="Geojit Report Generator", page_icon="📈")

st.title("📈 Geojit-Style Report Generator")
st.caption("Upload a company's financial document and download a research-report PDF.")

company = st.text_input("Company name", placeholder="e.g. L&T Technology Services Ltd.")
uploaded = st.file_uploader("Financial document",
                            type=[e.lstrip(".") for e in ingest.supported_formats()])

if st.button("Generate report", type="primary", disabled=not (company and uploaded)):
    try:
        with st.spinner("Reading the document, extracting data, building the PDF…"):
            out_path = os.path.join(tempfile.mkdtemp(), "report.pdf")
            pipeline.generate_report(uploaded.name, uploaded.read(), company, out_path)
        st.success("Report ready.")
        with open(out_path, "rb") as f:
            st.download_button("⬇ Download PDF", f.read(),
                               file_name=f"{company.replace(' ', '_')}_Report.pdf",
                               mime="application/pdf")
    except Exception as e:
        st.error(f"Could not generate report: {e}")