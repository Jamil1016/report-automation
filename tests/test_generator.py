import hashlib
from datetime import date
from pathlib import Path

import pytest

from team_activity_report.generator import generate
from team_activity_report.seed import seed_events

TEST_DATE = date(2026, 5, 5)  # Tuesday with seeded activity


@pytest.fixture
async def seeded_pool(db_pool):
    await seed_events(db_pool, days=30, seed=42)
    return db_pool


class TestGenerate:
    @pytest.mark.asyncio
    async def test_writes_file_at_expected_path(self, seeded_pool, tmp_path: Path) -> None:
        out = await generate(seeded_pool, TEST_DATE, tmp_path)
        assert out.exists()
        assert out.name == "2026-05-05-report.html"

    @pytest.mark.asyncio
    async def test_output_contains_expected_sections(self, seeded_pool, tmp_path: Path) -> None:
        out = await generate(seeded_pool, TEST_DATE, tmp_path)
        html = out.read_text(encoding="utf-8")
        assert "Engineering Team Daily Digest" in html
        assert "2026-05-05" in html
        assert "Tuesday" in html
        assert "PRs Merged" in html
        assert "Build Success Rate" in html
        assert "Throughput by Hour" in html
        assert "Top Active Developers" in html
        assert "Deploys by Repository" in html
        assert "data:image/png;base64," in html
        assert "team-activity-report v0.1.0" in html

    @pytest.mark.asyncio
    async def test_idempotent_byte_identical(self, seeded_pool, tmp_path: Path) -> None:
        """Two runs on the same date produce byte-identical files."""
        first = await generate(seeded_pool, TEST_DATE, tmp_path)
        first_hash = hashlib.sha256(first.read_bytes()).hexdigest()

        # Run again — same date, same data, same output
        second = await generate(seeded_pool, TEST_DATE, tmp_path)
        second_hash = hashlib.sha256(second.read_bytes()).hexdigest()

        assert first_hash == second_hash

    @pytest.mark.asyncio
    async def test_different_dates_produce_different_output(self, seeded_pool, tmp_path: Path) -> None:
        a = await generate(seeded_pool, date(2026, 5, 5), tmp_path)
        b = await generate(seeded_pool, date(2026, 5, 6), tmp_path)
        assert hashlib.sha256(a.read_bytes()).hexdigest() != hashlib.sha256(b.read_bytes()).hexdigest()
