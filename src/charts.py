"""Render charts as base64 PNGs to embed directly in the HTML."""
import base64
import io

import matplotlib
matplotlib.use("Agg")          # no GUI; just render to memory
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

GEOJIT = {"teal": "#137a63", "line": "#e8702a", "grid": "#e6ece9", "text": "#33403c"}
plt.rcParams.update({"font.size": 8, "text.color": GEOJIT["text"],
                     "axes.labelcolor": GEOJIT["text"],
                     "xtick.color": GEOJIT["text"], "ytick.color": GEOJIT["text"]})


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def _to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def combo_bar_line(series, line_key):
    """Bars for the value + an orange % line on a second axis."""
    if not series:
        return ""
    periods = [str(d.get("period", "")) for d in series]
    values = [_num(d.get("value")) for d in series]
    pct = [_num(d.get(line_key)) for d in series]

    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    x = range(len(periods))
    ax.bar(x, values, color=GEOJIT["teal"], width=0.6, zorder=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right", fontsize=6.5)
    ax.grid(axis="y", color=GEOJIT["grid"], linewidth=0.6, zorder=0)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if any(p is not None for p in pct):
        ax2 = ax.twinx()
        ax2.plot(x, pct, color=GEOJIT["line"], marker="o", markersize=2.5, linewidth=1.4)
        ax2.spines["top"].set_visible(False)
        ax2.tick_params(labelsize=6.5)
    return _to_b64(fig)


def line(points, x_key, y_key):
    if not points:
        return ""
    xs = [str(p.get(x_key, "")) for p in points]
    ys = [_num(p.get(y_key)) for p in points]
    fig, ax = plt.subplots(figsize=(4.6, 1.7))
    ax.plot(range(len(xs)), ys, color=GEOJIT["teal"], marker="o", markersize=3, linewidth=1.5)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=45, ha="right", fontsize=6)
    ax.grid(color=GEOJIT["grid"], linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _to_b64(fig)


def build_all(data):
    """Build every chart the template might show. Missing data -> empty string."""
    c = data.get("charts", {}) or {}
    out = {
        "revenue": combo_bar_line(c.get("revenue", []), "growth"),
        "gov":     combo_bar_line(c.get("gov", []), "growth"),
        "ebitda":  combo_bar_line(c.get("ebitda", []), "margin"),
        "pat":     combo_bar_line(c.get("pat", []), "margin"),
    }
    hist = data.get("recommendation_history") or []
    out["rating_history"] = line(hist, "date", "target") if hist else ""
    return out