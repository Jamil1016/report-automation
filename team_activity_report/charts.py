"""Deterministic matplotlib charts → base64-encoded PNG strings.

Determinism is critical for byte-identical report files on re-runs:
  - Use Agg backend (no display, no interactive features)
  - Override PNG metadata to avoid timestamp injection
  - Fixed figure size, dpi, and color palette
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from team_activity_report.types import HourlyCount

_BG = "#0f172a"        # slate-950 — matches portfolio theme
_FG = "#e2e8f0"        # slate-200
_BAR = "#10b981"       # emerald-500


def hourly_throughput_chart(hourly: list[HourlyCount]) -> str:
    """Render a bar chart of activity per hour. Returns base64-encoded PNG."""
    hours = [h["hour"] for h in hourly]
    counts = [h["count"] for h in hourly]

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100, facecolor=_BG)
    ax.set_facecolor(_BG)
    ax.bar(hours, counts, color=_BAR, edgecolor="none")
    ax.set_xlabel("Hour (UTC)", color=_FG)
    ax.set_ylabel("Events", color=_FG)
    ax.set_xticks(range(0, 24, 2))
    ax.tick_params(colors=_FG)
    for spine in ax.spines.values():
        spine.set_color(_FG)
    ax.grid(axis="y", color="#334155", linestyle="-", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        facecolor=_BG,
        metadata={"Software": ""},  # suppress timestamp in PNG metadata for determinism
    )
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
