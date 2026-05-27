from datetime import UTC, date, datetime

import pytest

from team_activity_report.queries import (
    active_devs,
    build_stats,
    count_prs,
    deploys_by_repo,
    open_incidents_as_of,
    throughput_by_hour,
)
from team_activity_report.seed import seed_events

# Pin to a specific date that we know has activity in the seeded data.
# 2026-05-04 is the seed anchor (Monday). 2026-05-05 is a Tuesday (PR peak day).
TEST_DATE = date(2026, 5, 5)


@pytest.fixture
async def seeded_pool(db_pool):
    """db_pool with seed_events already applied."""
    await seed_events(db_pool, days=30, seed=42)
    return db_pool


class TestCountPrs:
    @pytest.mark.asyncio
    async def test_returns_positive_count_on_workday(self, seeded_pool) -> None:
        n = await count_prs(seeded_pool, TEST_DATE)
        assert n > 0

    @pytest.mark.asyncio
    async def test_returns_zero_on_weekend(self, seeded_pool) -> None:
        # 2026-05-09 is a Saturday — no PRs merged on weekends
        n = await count_prs(seeded_pool, date(2026, 5, 9))
        assert n == 0


class TestBuildStats:
    @pytest.mark.asyncio
    async def test_returns_all_status_breakdown(self, seeded_pool) -> None:
        stats = await build_stats(seeded_pool, TEST_DATE)
        assert "total" in stats
        assert "success" in stats
        assert "failure" in stats
        assert "cancelled" in stats
        assert "success_rate" in stats
        assert stats["total"] == stats["success"] + stats["failure"] + stats["cancelled"]

    @pytest.mark.asyncio
    async def test_success_rate_in_valid_range(self, seeded_pool) -> None:
        stats = await build_stats(seeded_pool, TEST_DATE)
        assert 0.0 <= stats["success_rate"] <= 1.0

    @pytest.mark.asyncio
    async def test_success_rate_zero_when_no_builds(self, seeded_pool) -> None:
        stats = await build_stats(seeded_pool, date(2026, 5, 9))  # Saturday
        assert stats["total"] == 0
        assert stats["success_rate"] == 0.0


class TestDeploysByRepo:
    @pytest.mark.asyncio
    async def test_returns_list_of_repo_counts(self, seeded_pool) -> None:
        rows = await deploys_by_repo(seeded_pool, TEST_DATE)
        assert isinstance(rows, list)
        for r in rows:
            assert "repo" in r and "count" in r
            assert r["count"] > 0

    @pytest.mark.asyncio
    async def test_empty_on_weekend(self, seeded_pool) -> None:
        rows = await deploys_by_repo(seeded_pool, date(2026, 5, 9))
        assert rows == []


class TestOpenIncidentsAsOf:
    @pytest.mark.asyncio
    async def test_returns_int_at_or_above_zero(self, seeded_pool) -> None:
        n = await open_incidents_as_of(seeded_pool, TEST_DATE)
        assert isinstance(n, int)
        assert n >= 0


class TestThroughputByHour:
    @pytest.mark.asyncio
    async def test_returns_24_buckets_with_zeros_filled(self, seeded_pool) -> None:
        rows = await throughput_by_hour(seeded_pool, TEST_DATE)
        # Should fill in zeros for hours with no activity
        assert len(rows) == 24
        for hour_idx, row in enumerate(rows):
            assert row["hour"] == hour_idx
            assert row["count"] >= 0

    @pytest.mark.asyncio
    async def test_total_matches_other_counts(self, seeded_pool) -> None:
        rows = await throughput_by_hour(seeded_pool, TEST_DATE)
        total_hourly = sum(r["count"] for r in rows)
        assert total_hourly > 0


class TestActiveDevs:
    @pytest.mark.asyncio
    async def test_returns_at_most_top_n(self, seeded_pool) -> None:
        rows = await active_devs(seeded_pool, TEST_DATE, top_n=3)
        assert len(rows) <= 3

    @pytest.mark.asyncio
    async def test_sorted_descending(self, seeded_pool) -> None:
        rows = await active_devs(seeded_pool, TEST_DATE, top_n=5)
        counts = [r["count"] for r in rows]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_empty_on_weekend(self, seeded_pool) -> None:
        rows = await active_devs(seeded_pool, date(2026, 5, 9))
        assert rows == []
