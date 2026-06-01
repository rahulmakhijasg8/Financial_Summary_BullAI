"""Read an uploaded file (PDF / CSV / TXT) into plain text."""
import io
from pathlib import Path

import pandas as pd


def _from_pdf(data: bytes) -> str:
    import fitz  # PyMuPDF
    parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for i, page in enumerate(doc, 1):
            parts.append(f"--- PAGE {i} ---\n{page.get_text()}")
    return "\n".join(parts)


def _from_csv(data: bytes) -> str:
    df = pd.read_csv(io.BytesIO(data))
    lines = ["CSV columns: " + ", ".join(map(str, df.columns))]
    for _, row in df.iterrows():
        lines.append(" | ".join(f"{c}={row[c]}" for c in df.columns))
    return "\n".join(lines)


def _from_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


# Map each file extension to the function that handles it.
LOADERS = {".pdf": _from_pdf, ".csv": _from_csv, ".txt": _from_txt}


def load_document(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in LOADERS:
        raise ValueError(f"Unsupported format '{ext}'. Supported: {list(LOADERS)}")
    text = LOADERS[ext](data)
    if not text.strip():
        raise ValueError(f"No text extracted from {filename}.")
    return text


def supported_formats():
    return sorted(LOADERS)