"""Orchestrate query → chart → template → write."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import asyncpg
from jinja2 import Environment, FileSystemLoader, select_autoescape

from team_activity_report.charts import hourly_throughput_chart
from team_activity_report.queries import (
    active_devs,
    build_stats,
    count_prs,
    deploys_by_repo,
    open_incidents_as_of,
    throughput_by_hour,
)

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _build_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )


async def generate(pool: asyncpg.Pool, target_date: date, out_dir: Path) -> Path:
    """Generate the report for target_date. Returns the path to the written HTML file."""
    prs = await count_prs(pool, target_date)
    stats = await build_stats(pool, target_date)
    deploys = await deploys_by_repo(pool, target_date)
    incidents_open = await open_incidents_as_of(pool, target_date)
    hourly = await throughput_by_hour(pool, target_date)
    devs = await active_devs(pool, target_date, top_n=5)

    chart_b64 = hourly_throughput_chart(hourly)

    context = {
        "report_date": target_date.isoformat(),
        "day_of_week": _DAY_NAMES[target_date.weekday()],
        "totals": {
            "prs": prs,
            "builds": stats["total"],
            "deploys": sum(d["count"] for d in deploys),
            "incidents_open": incidents_open,
        },
        "build_stats": stats,
        "deploys_by_repo": deploys,
        "active_devs": devs,
        "throughput_chart_b64": chart_b64,
    }

    env = _build_env()
    template = env.get_template("report.html.j2")
    html = template.render(**context)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{target_date.isoformat()}-report.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
