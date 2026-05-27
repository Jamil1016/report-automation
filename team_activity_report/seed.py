"""Deterministic synthetic event generator.

Anchored at 2026-05-04 09:00 UTC (a Monday). Same seed + same `days` → identical events.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

import asyncpg

ANCHOR = datetime(2026, 5, 4, 9, 0, tzinfo=UTC)  # Monday

ACTORS = ("alice-dev", "bob-eng", "charlie-ops", "dana-qa", "eve-platform")
REPOS = ("widget-api", "payments-svc", "web-app")
EVENT_KINDS = (
    "pr_merged",
    "build_completed",
    "deploy",
    "incident_opened",
    "incident_closed",
)


class Event(TypedDict):
    occurred_at: datetime
    kind: str
    actor: str
    repo: str | None
    status: str | None
    duration_seconds: int | None
    payload: dict[str, Any]


def _is_workday(d: datetime) -> bool:
    return d.weekday() < 5


def _during_work_hours(rng: random.Random) -> int:
    """Random number of seconds offset from 09:00 within the workday.

    Returns a value in [0, 9*3600] — 9-hour workday.
    """
    return rng.randint(0, 9 * 3600)


def generate_events(days: int, seed: int) -> list[Event]:
    """Generate deterministic synthetic events for `days` days starting at ANCHOR.

    Distribution:
      - PRs merged: ~2-4 per workday per dev, Tue/Wed peak, none on weekends
      - Build completions: ~5 per PR merge + background builds during work hours
      - Deploys: 1-3 per workday across repos, Friday is quiet (max 1)
      - Incidents: ~1-2 per week, ~80% resolved same day, ~20% next workday
    """
    rng = random.Random(seed)
    events: list[Event] = []

    for day_offset in range(days):
        day_start = ANCHOR + timedelta(days=day_offset)

        if not _is_workday(day_start):
            continue

        # PRs merged — Tue/Wed peak
        pr_multiplier = 1.5 if day_start.weekday() in (1, 2) else 1.0
        for actor in ACTORS:
            n_prs = int(rng.randint(2, 4) * pr_multiplier)
            for _ in range(n_prs):
                ts = day_start + timedelta(seconds=_during_work_hours(rng))
                repo = rng.choice(REPOS)
                events.append(
                    Event(
                        occurred_at=ts,
                        kind="pr_merged",
                        actor=actor,
                        repo=repo,
                        status=None,
                        duration_seconds=None,
                        payload={"pr_number": rng.randint(100, 9999)},
                    )
                )
                # Each PR triggers 1-3 builds within 5 minutes
                for _ in range(rng.randint(1, 3)):
                    build_ts = ts + timedelta(seconds=rng.randint(0, 300))
                    status_roll = rng.random()
                    if status_roll < 0.9:
                        status = "success"
                    elif status_roll < 0.95:
                        status = "failure"
                    else:
                        status = "cancelled"
                    events.append(
                        Event(
                            occurred_at=build_ts,
                            kind="build_completed",
                            actor=actor,
                            repo=repo,
                            status=status,
                            duration_seconds=rng.randint(60, 600),
                            payload={"workflow": rng.choice(["pr-check", "deploy", "nightly"])},
                        )
                    )

        # Background builds during the workday (independent of PRs)
        for _ in range(rng.randint(5, 15)):
            ts = day_start + timedelta(seconds=_during_work_hours(rng))
            actor = rng.choice(ACTORS)
            repo = rng.choice(REPOS)
            status_roll = rng.random()
            status = "success" if status_roll < 0.9 else "failure"
            events.append(
                Event(
                    occurred_at=ts,
                    kind="build_completed",
                    actor=actor,
                    repo=repo,
                    status=status,
                    duration_seconds=rng.randint(60, 600),
                    payload={"workflow": "background"},
                )
            )

        # Deploys — quiet on Fridays
        max_deploys = 1 if day_start.weekday() == 4 else 3
        n_deploys = rng.randint(1, max_deploys)
        for _ in range(n_deploys):
            ts = day_start + timedelta(seconds=_during_work_hours(rng))
            events.append(
                Event(
                    occurred_at=ts,
                    kind="deploy",
                    actor=rng.choice(ACTORS),
                    repo=rng.choice(REPOS),
                    status="success",
                    duration_seconds=rng.randint(120, 900),
                    payload={"environment": rng.choice(["staging", "production"])},
                )
            )

        # Incidents — roughly 1 every 3 workdays
        if rng.random() < 0.33:
            opened_ts = day_start + timedelta(seconds=_during_work_hours(rng))
            opener = rng.choice(ACTORS)
            repo = rng.choice(REPOS)
            severity = rng.choice(["sev1", "sev2", "sev3"])
            incident_id = rng.randint(1000, 9999)
            events.append(
                Event(
                    occurred_at=opened_ts,
                    kind="incident_opened",
                    actor=opener,
                    repo=repo,
                    status=None,
                    duration_seconds=None,
                    payload={"incident_id": incident_id, "severity": severity},
                )
            )
            # ~80% resolved same day, ~20% next workday
            if rng.random() < 0.8:
                closed_ts = opened_ts + timedelta(seconds=rng.randint(1800, 14400))  # 30 min - 4 hr
            else:
                next_workday = day_start + timedelta(days=1)
                while not _is_workday(next_workday):
                    next_workday += timedelta(days=1)
                closed_ts = next_workday + timedelta(seconds=_during_work_hours(rng))
            events.append(
                Event(
                    occurred_at=closed_ts,
                    kind="incident_closed",
                    actor=rng.choice(ACTORS),
                    repo=repo,
                    status=None,
                    duration_seconds=None,
                    payload={"incident_id": incident_id, "severity": severity},
                )
            )

    # Sort by occurred_at for stable ordering
    events.sort(key=lambda e: e["occurred_at"])
    return events


async def seed_events(pool: asyncpg.Pool, days: int = 30, seed: int = 42) -> int:
    """Truncate and insert deterministic synthetic events. Returns the inserted count."""
    from team_activity_report.db import truncate_events

    await truncate_events(pool)
    events = generate_events(days=days, seed=seed)

    async with pool.acquire() as conn:
        await conn.executemany(
            """
            insert into events
              (occurred_at, kind, actor, repo, status, duration_seconds, payload)
            values
              ($1, $2, $3, $4, $5, $6, $7::jsonb)
            """,
            [
                (
                    e["occurred_at"],
                    e["kind"],
                    e["actor"],
                    e["repo"],
                    e["status"],
                    e["duration_seconds"],
                    json.dumps(e["payload"]),
                )
                for e in events
            ],
        )
    return len(events)
