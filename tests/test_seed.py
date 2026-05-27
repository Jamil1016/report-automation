from datetime import UTC, datetime

import pytest

from team_activity_report.seed import (
    ACTORS,
    ANCHOR,
    EVENT_KINDS,
    REPOS,
    generate_events,
    seed_events,
)


class TestGenerateEvents:
    def test_seed_determinism(self) -> None:
        """Same seed + same days produces same event list."""
        a = generate_events(days=30, seed=42)
        b = generate_events(days=30, seed=42)
        assert len(a) == len(b)
        for ea, eb in zip(a, b, strict=True):
            assert ea == eb

    def test_different_seeds_produce_different_events(self) -> None:
        a = generate_events(days=30, seed=42)
        b = generate_events(days=30, seed=43)
        assert a != b

    def test_event_count_in_expected_range(self) -> None:
        """30 days should produce ~600-1500 events. Loose bounds; just guard against runaway."""
        events = generate_events(days=30, seed=42)
        assert 500 < len(events) < 2000

    def test_no_pr_merges_on_weekends(self) -> None:
        """PRs are only merged on workdays."""
        events = generate_events(days=30, seed=42)
        for e in events:
            if e["kind"] == "pr_merged":
                assert e["occurred_at"].weekday() < 5

    def test_all_actors_in_known_set(self) -> None:
        events = generate_events(days=30, seed=42)
        for e in events:
            assert e["actor"] in ACTORS

    def test_all_kinds_valid(self) -> None:
        events = generate_events(days=30, seed=42)
        for e in events:
            assert e["kind"] in EVENT_KINDS

    def test_repos_only_in_known_set_when_set(self) -> None:
        events = generate_events(days=30, seed=42)
        for e in events:
            if e["repo"] is not None:
                assert e["repo"] in REPOS

    def test_anchor_is_a_monday(self) -> None:
        """The anchor date is fixed at 2026-05-04 (Monday)."""
        assert datetime(2026, 5, 4, 9, 0, tzinfo=UTC) == ANCHOR
        assert ANCHOR.weekday() == 0  # Monday


class TestSeedEvents:
    @pytest.mark.asyncio
    async def test_seeds_into_db(self, db_pool) -> None:
        n = await seed_events(db_pool, days=10, seed=42)
        async with db_pool.acquire() as conn:
            count = await conn.fetchval("select count(*) from events")
        assert count == n
        assert n > 0

    @pytest.mark.asyncio
    async def test_seed_truncates_first(self, db_pool) -> None:
        """Re-seeding doesn't double the row count."""
        first = await seed_events(db_pool, days=10, seed=42)
        second = await seed_events(db_pool, days=10, seed=42)
        async with db_pool.acquire() as conn:
            count = await conn.fetchval("select count(*) from events")
        assert count == second
        assert first == second  # deterministic
