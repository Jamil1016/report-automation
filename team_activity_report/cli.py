"""Command-line interface — argparse with run / init-db / seed-data subcommands."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from team_activity_report.db import create_pool, init_schema
from team_activity_report.delivery import send_smtp
from team_activity_report.gate import should_run
from team_activity_report.generator import generate
from team_activity_report.seed import seed_events

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="team-activity-report",
        description="Generate daily engineering-team activity reports.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Apply schema.sql to the configured DATABASE_URL")

    seed = sub.add_parser("seed-data", help="Insert deterministic synthetic events")
    seed.add_argument("--days", type=int, default=30, help="Number of days to seed (default: 30)")
    seed.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")

    run = sub.add_parser("run", help="Generate the daily report")
    run.add_argument("--date", help="Target date YYYY-MM-DD (default: yesterday)")
    run.add_argument("--email", action="store_true", help="Also attempt SMTP delivery")
    run.add_argument("--force", action="store_true", help="Skip the weekday/holiday gate")
    run.add_argument("--out", default="out", help="Output directory (default: ./out)")

    return parser


def _resolve_target_date(arg: str | None) -> date:
    if arg:
        return datetime.strptime(arg, "%Y-%m-%d").date()
    return datetime.now().date() - timedelta(days=1)


async def _run(args: argparse.Namespace) -> int:
    target = _resolve_target_date(args.date)
    if not args.force:
        ok, reason = should_run(target)
        if not ok:
            day_name = _DAY_NAMES[target.weekday()]
            print(f"{day_name} — skipping ({reason}; use --force to override)")
            return 0

    pool = await create_pool()
    try:
        out_path = await generate(pool, target, Path(args.out))
        print(f"Wrote {out_path}")
        if args.email:
            html = out_path.read_text(encoding="utf-8")
            to_addr = "team@example.com"
            status = send_smtp(html, to_addr)
            print(status)
        return 0
    finally:
        await pool.close()


async def _init_db() -> int:
    pool = await create_pool()
    try:
        await init_schema(pool)
        print("Schema applied.")
        return 0
    finally:
        await pool.close()


async def _seed(args: argparse.Namespace) -> int:
    pool = await create_pool()
    try:
        n = await seed_events(pool, days=args.days, seed=args.seed)
        print(f"Seeded {n} events.")
        return 0
    finally:
        await pool.close()


async def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    if args.command == "init-db":
        return await _init_db()
    if args.command == "seed-data":
        return await _seed(args)
    if args.command == "run":
        return await _run(args)
    return 1


def cli_entry() -> None:
    sys.exit(asyncio.run(main()))
