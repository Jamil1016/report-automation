"""Async SQL aggregation queries.

All queries scope to a target_date (UTC day boundary): events where
occurred_at >= target_date 00:00 UTC AND occurred_at < target_date+1 00:00 UTC.

The open_incidents_as_of query is a special case — it counts all opens minus
all closes up to (and including) the end of target_date, not just events that
occurred on that date.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

import asyncpg

from team_activity_report.types import (
    BuildStats,
    DevCount,
    HourlyCount,
    RepoCount,
)


def _day_bounds(target_date: date) -> tuple[datetime, datetime]:
    """Return (start, end) UTC datetimes for the day."""
    start = datetime.combine(target_date, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


async def count_prs(pool: asyncpg.Pool, target_date: date) -> int:
    start, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            "select count(*) from events where kind = 'pr_merged' "
            "and occurred_at >= $1 and occurred_at < $2",
            start,
            end,
        )
    return int(n)


async def build_stats(pool: asyncpg.Pool, target_date: date) -> BuildStats:
    start, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            select
              count(*) as total,
              count(*) filter (where status = 'success') as success,
              count(*) filter (where status = 'failure') as failure,
              count(*) filter (where status = 'cancelled') as cancelled
            from events
            where kind = 'build_completed'
              and occurred_at >= $1 and occurred_at < $2
            """,
            start,
            end,
        )
    assert row is not None
    total = int(row["total"])
    success = int(row["success"])
    failure = int(row["failure"])
    cancelled = int(row["cancelled"])
    success_rate = success / total if total > 0 else 0.0
    return BuildStats(
        total=total,
        success=success,
        failure=failure,
        cancelled=cancelled,
        success_rate=success_rate,
    )


async def deploys_by_repo(pool: asyncpg.Pool, target_date: date) -> list[RepoCount]:
    start, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            select repo, count(*) as count
            from events
            where kind = 'deploy'
              and occurred_at >= $1 and occurred_at < $2
              and repo is not null
            group by repo
            order by count desc, repo asc
            """,
            start,
            end,
        )
    return [RepoCount(repo=r["repo"], count=int(r["count"])) for r in rows]


async def open_incidents_as_of(pool: asyncpg.Pool, target_date: date) -> int:
    _, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        opened = await conn.fetchval(
            "select count(*) from events where kind = 'incident_opened' and occurred_at < $1",
            end,
        )
        closed = await conn.fetchval(
            "select count(*) from events where kind = 'incident_closed' and occurred_at < $1",
            end,
        )
    return max(0, int(opened) - int(closed))


async def throughput_by_hour(pool: asyncpg.Pool, target_date: date) -> list[HourlyCount]:
    """All event kinds, bucketed by UTC hour. Returns 24 entries (zeros filled)."""
    start, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            select extract(hour from occurred_at at time zone 'UTC')::int as hour,
                   count(*) as count
            from events
            where occurred_at >= $1 and occurred_at < $2
            group by hour
            order by hour
            """,
            start,
            end,
        )
    by_hour = {int(r["hour"]): int(r["count"]) for r in rows}
    return [HourlyCount(hour=h, count=by_hour.get(h, 0)) for h in range(24)]


async def active_devs(pool: asyncpg.Pool, target_date: date, top_n: int = 5) -> list[DevCount]:
    start, end = _day_bounds(target_date)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            select actor, count(*) as count
            from events
            where occurred_at >= $1 and occurred_at < $2
            group by actor
            order by count desc, actor asc
            limit $3
            """,
            start,
            end,
            top_n,
        )
    return [DevCount(actor=r["actor"], count=int(r["count"])) for r in rows]
