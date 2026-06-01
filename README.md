# Geojit-Style Research Report Generator

Upload a company's financial document (PDF, CSV, or TXT) and download an
auto-filled, 4-page PDF research report laid out like a Geojit "Retail Equity
Research" note. Data is extracted by an LLM; anything the source doesn't contain
is left blank / marked `NA`.

## How it works

A small pipeline, called from a Streamlit UI:

1. **Ingest** – read the uploaded file into plain text (`src/ingest.py`).
2. **Extract** – Google Gemini returns the report data as structured JSON
   (`src/extract.py`). It is instructed to use `null` for anything missing and
   never to invent ratings, targets, or numbers.
3. **Charts** – quarterly series become PNGs via matplotlib (`src/charts.py`).
4. **Render** – an HTML/CSS template is filled with Jinja2 and printed to PDF by
   headless Chromium via Playwright (`src/render.py`, `templates/report.html`).

`src/pipeline.py` wires these together; `app.py` is the web UI.

## Tech stack

- **UI:** Streamlit
- **Extraction:** Google Gemini (`gemini-2.5-flash`, auto-falling back to
  `gemini-2.5-flash-lite` when the model is busy) via the `google-genai` SDK
- **Ingestion:** PyMuPDF (PDF), pandas (CSV)
- **Charts:** matplotlib
- **Templating + PDF:** Jinja2 + Playwright (headless Chromium)

## Requirements

- Python 3.10+
- A free Gemini API key — https://aistudio.google.com/apikey (no credit card)

## Setup & run

```bash
# 1. virtual environment (this project uses one named .summary)
python -m venv .summary
.summary\Scripts\activate          # Windows
# source .summary/bin/activate     # macOS / Linux

# 2. install
pip install -r requirements.txt
playwright install chromium        # one-time: downloads the browser engine

# 3. add your key
copy .env.example .env             # then paste your GEMINI_API_KEY into .env

# 4. run
streamlit run app.py
```

Type a company name, upload a PDF/CSV/TXT, click **Generate report**, download the PDF.

## Where the template fields are defined

Two places, kept in sync:

- **`src/extract.py`** – the `SYSTEM_INSTRUCTION` string defines the JSON shape
  the LLM must return (every section and field of the report).
- **`templates/report.html`** – the matching 4-page layout that renders them.

To add or change a field, edit both.

## Supported input formats

`.pdf`, `.csv`, `.txt`. Add a new one by registering a loader in `LOADERS`
inside `src/ingest.py`.

## Missing-field handling

Every field is optional. The extractor returns `null` for anything the document
doesn't contain, and the renderer shows `NA`; empty sections are omitted. A
company press release (no broker rating/target) renders just as cleanly as a
full analyst note — see the LTTS example.

## Examples

- `examples/LTTS_Q2FY26.pdf` — sample input (a press / investor release)
- `examples/LTTS_Report.pdf` — the generated report

Regenerate, or point at another file, with `python try_part3.py`.

## Project structure

geojit-report-generator
├── app.py                  
├── try_part3.py           
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py          
│   ├── extract.py         
│   ├── charts.py           
│   ├── render.py           
│   └── pipeline.py         
├── templates/
│   └── report.html        
└── examples/
├── LTTS_Q2FY26.pdf
└── LTTS_Report.pdf


## Notes & limitations

- Output is generated automatically and is **not investment advice**; always
  verify figures against primary filings.
- Chart richness depends on the source: a document with only a few quarters of
  history produces sparse charts.
- On a 503 (Gemini high demand) extraction retries and falls back to flash-lite
  automatically; a sustained spike may still need a brief wait.
