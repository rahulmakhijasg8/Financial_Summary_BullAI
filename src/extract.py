"""Turn document text into the report's structured JSON, using Google Gemini."""
import json
import os
import re

from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """You are an equity research analyst's data-extraction assistant.
From the company document provided, extract the data for a Geojit-style research
report and return it as a SINGLE JSON object.

Rules:
- Return ONLY JSON. No markdown, no commentary.
- Use this exact top-level shape:
  {
    "meta": {company_name, report_title, research_desk, period_label, sector,
             report_date, data_asof, rating, target_price, cmp, return_pct,
             stock_type, bloomberg_code, sensex, nse_code, bse_code, time_frame},
    "key_changes": {target, rating, earnings},        // each "up"|"down"|"none" or null
    "company_data": [{label, value}, ...],
    "shareholding": {columns:[...], rows:[{label, values:[...]}]},
    "price_performance": {columns:[...], rows:[{label, values:[...]}]},
    "narrative": {company_description, highlights:[...], outlook_valuation,
                  key_highlights:[...]},
    "estimates": {columns:[...], rows:[{label, values:[...]}]},
    "quarterly": {columns:[...], rows:[{label, values:[...]}]},
    "charts": {revenue:[{period,value,growth}], gov:[{period,value,growth}],
               ebitda:[{period,value,margin}], pat:[{period,value,margin}]},
    "change_in_estimates": {columns:[...], rows:[{label, values:[...]}]},
    "financials": {period_label,
                   profit_loss:   {columns:[...], rows:[{label, values:[...]}]},
                   balance_sheet: {columns:[...], rows:[...]},
                   cashflow:      {columns:[...], rows:[...]},
                   ratios:        {columns:[...], rows:[...]}},
    "recommendation_history": [{date, rating, target}, ...]
  }
- CRITICAL: if the document does not contain a value, set it to null. NEVER invent
  numbers, ratings, target prices or estimates. A company results document usually
  has NO broker rating/target/CMP/valuation multiples/shareholding -> leave null.
- Always populate financials.profit_loss with the income statement when the document
  has one (even a quarterly results document). Each financials table carries its OWN
  columns; they need not match across tables. Set financials.period_label to
  "Y.E March" only when the columns are fiscal years (e.g. FY23A..FY27E), else null.
- Write report_title, company_description, outlook_valuation and the bullet lists
  in your own words, grounded only in the document.
- report_title should be a short thesis line (<= 9 words).
"""


def _strip_to_json(text: str) -> dict:
    """Models sometimes wrap JSON in ``` fences; recover the object."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")
    return json.loads(text[start:end + 1])


def extract_report_data(doc_text: str, company_name: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Get a free key at "
                           "https://aistudio.google.com/apikey")
    client = genai.Client(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    prompt = (f"Company name (use verbatim for meta.company_name): {company_name}\n\n"
              f"DOCUMENT:\n{doc_text}")
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    data = _strip_to_json(resp.text)
    data.setdefault("meta", {})["company_name"] = company_name
    return data