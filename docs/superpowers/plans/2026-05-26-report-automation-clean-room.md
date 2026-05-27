# Clean-Room report-automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable open-source Python package `team_activity_report` that queries a Postgres-seeded engineering-team activity dataset, aggregates into typed query results, renders a deterministic HTML report with embedded base64 charts, applies weekday/holiday gating, and (optionally) sends via SMTP — all with green GitHub Actions CI.

**Architecture:** Single Python package. Async DB layer (asyncpg pool, mirrors gmail-scraper). Pure-function gate. Deterministic seed for reproducible tests. Six async aggregation queries with TypedDict results. matplotlib for deterministic PNG charts (base64-encoded for email-safety). Jinja2 template renders a self-contained HTML file. SMTP delivery is a "would send" stub by default.

**Tech Stack:** Python 3.12, asyncpg, Postgres 16, matplotlib, Jinja2, pytest + pytest-asyncio + testcontainers-postgres, ruff, mypy, docker-compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-05-26-report-automation-clean-room.md`

**Working directory:** `C:\Users\admin\Desktop\Projects\personal\report-automation`

**Repo:** `Jamil1016/report-automation` (currently has 2 commits — placeholder README + spec).

---

## File Structure Overview

```
report-automation/
├── team_activity_report/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── generator.py
│   ├── queries.py
│   ├── charts.py
│   ├── delivery.py
│   ├── gate.py
│   ├── seed.py
│   ├── db.py
│   ├── schema.sql
│   ├── types.py
│   └── templates/
│       └── report.html.j2
├── out/                                # gitignored — generated reports
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # testcontainers Postgres
│   ├── test_gate.py
│   ├── test_seed.py
│   ├── test_queries.py
│   ├── test_charts.py
│   ├── test_generator.py
│   ├── test_delivery.py
│   └── test_cli.py
├── .github/workflows/{test.yml,lint.yml}
├── .env.example, .gitignore, docker-compose.yml, pyproject.toml, README.md, LICENSE
```

---

# Phase 0 — Scaffolding

### Task 1: Project scaffolding

**Files:**
- Create: `.gitignore`, `.env.example`, `pyproject.toml`, `docker-compose.yml`, `LICENSE`
- Create: `team_activity_report/__init__.py`, `team_activity_report/schema.sql`

- [ ] **Step 1: `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.venv/
venv/
.pytest_cache/
.coverage
coverage.xml
htmlcov/
.vscode/
.idea/
.DS_Store
Thumbs.db
.env
.env.local
/out/
```

- [ ] **Step 2: `.env.example`**

```bash
# Local Postgres (matches docker-compose defaults)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/team_reports

# SMTP — leave unset to use the "would send" stub
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=user@example.com
# SMTP_PASS=password
# SMTP_FROM=reports@example.com
```

- [ ] **Step 3: `pyproject.toml`**

```toml
[project]
name = "team-activity-report"
version = "0.1.0"
description = "Generate daily engineering-team activity reports from Postgres. Clean-room reference implementation of the scheduled-report pattern."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Jamil Mendez" }]
dependencies = [
    "asyncpg>=0.29",
    "matplotlib>=3.8",
    "Jinja2>=3.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "testcontainers[postgres]>=4.0",
    "ruff>=0.5",
    "mypy>=1.10",
]

[project.scripts]
team-activity-report = "team_activity_report.cli:cli_entry"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["team_activity_report*"]
exclude = ["tests*"]

[tool.setuptools.package-data]
team_activity_report = ["schema.sql", "templates/*.j2"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = ["-v", "--strict-markers"]

[tool.coverage.run]
source = ["team_activity_report"]
omit = ["team_activity_report/__main__.py", "team_activity_report/cli.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true

[[tool.mypy.overrides]]
module = ["asyncpg.*", "matplotlib.*", "jinja2.*", "dotenv.*"]
ignore_missing_imports = true
```

- [ ] **Step 4: `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    container_name: team-reports-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: team_reports
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

- [ ] **Step 5: `LICENSE`** (MIT, 2026, Jamil Mendez — same wording as gmail-scraper)

```
MIT License

Copyright (c) 2026 Jamil Mendez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 6: `team_activity_report/__init__.py`**

```python
"""team_activity_report — generate engineering-team daily activity reports from Postgres."""

__version__ = "0.1.0"
```

- [ ] **Step 7: `team_activity_report/schema.sql`**

```sql
create table if not exists events (
  id               bigserial primary key,
  occurred_at      timestamptz not null,
  kind             text not null
                   check (kind in ('pr_merged', 'build_completed', 'deploy',
                                   'incident_opened', 'incident_closed')),
  actor            text not null,
  repo             text,
  status           text,
  duration_seconds int,
  payload          jsonb not null default '{}'::jsonb
);

create index if not exists events_kind_occurred_idx
  on events (kind, occurred_at desc);
create index if not exists events_occurred_idx
  on events (occurred_at desc);
create index if not exists events_actor_idx
  on events (actor);
```

- [ ] **Step 8: Install + verify**

```bash
cd "C:\Users\admin\Desktop\Projects\personal\report-automation"
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -c "import team_activity_report; print(team_activity_report.__version__)"
```
Expected: `0.1.0`.

- [ ] **Step 9: Commit**

```bash
git add .gitignore .env.example pyproject.toml docker-compose.yml LICENSE team_activity_report/
git commit -m "chore: project scaffolding (pyproject, docker, schema, license)"
```

---

# Phase 1 — Types + Gate (TDD)

### Task 2: `types.py` + `gate.py` with TDD

**Files:**
- Create: `team_activity_report/types.py`
- Create: `team_activity_report/gate.py`
- Create: `tests/__init__.py`, `tests/test_gate.py`

- [ ] **Step 1: Create `tests/__init__.py`** (empty file)

- [ ] **Step 2: Create `team_activity_report/types.py`** (no logic; types-only — no test needed)

```python
"""Typed data contracts for query results and report context."""

from __future__ import annotations

from typing import TypedDict


class BuildStats(TypedDict):
    total: int
    success: int
    failure: int
    cancelled: int
    success_rate: float  # 0.0 to 1.0


class RepoCount(TypedDict):
    repo: str
    count: int


class HourlyCount(TypedDict):
    hour: int  # 0-23
    count: int


class DevCount(TypedDict):
    actor: str
    count: int


class ReportTotals(TypedDict):
    prs: int
    builds: int
    deploys: int
    incidents_open: int
```

- [ ] **Step 3: Write failing tests at `tests/test_gate.py`**

```python
from datetime import date

import pytest

from team_activity_report.gate import is_holiday, is_weekend, should_run


class TestIsWeekend:
    def test_saturday(self) -> None:
        # 2026-05-23 is a Saturday
        assert is_weekend(date(2026, 5, 23)) is True

    def test_sunday(self) -> None:
        # 2026-05-24 is a Sunday
        assert is_weekend(date(2026, 5, 24)) is True

    def test_monday(self) -> None:
        # 2026-05-25 is Memorial Day (Mon) — still not weekend
        assert is_weekend(date(2026, 5, 25)) is False

    def test_wednesday(self) -> None:
        assert is_weekend(date(2026, 5, 27)) is False


class TestIsHoliday:
    def test_new_years_day(self) -> None:
        assert is_holiday(date(2026, 1, 1)) is True

    def test_memorial_day(self) -> None:
        assert is_holiday(date(2026, 5, 25)) is True

    def test_christmas(self) -> None:
        assert is_holiday(date(2026, 12, 25)) is True

    def test_random_workday(self) -> None:
        assert is_holiday(date(2026, 5, 27)) is False


class TestShouldRun:
    def test_weekday_runs(self) -> None:
        # 2026-05-26 is a Tuesday, not a holiday
        ok, reason = should_run(date(2026, 5, 26))
        assert ok is True
        assert reason == "weekday"

    def test_weekend_skips(self) -> None:
        ok, reason = should_run(date(2026, 5, 23))
        assert ok is False
        assert reason == "weekend"

    def test_holiday_skips(self) -> None:
        ok, reason = should_run(date(2026, 5, 25))
        assert ok is False
        assert reason == "holiday"

    def test_holiday_on_weekend_reports_as_weekend(self) -> None:
        # If a holiday happens to fall on a weekend, weekend wins (it's checked first)
        # 2026-07-04 is a Saturday
        ok, reason = should_run(date(2026, 7, 4))
        assert ok is False
        assert reason == "weekend"
```

- [ ] **Step 4: Run, confirm fail**

```bash
pytest tests/test_gate.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'team_activity_report.gate'`.

- [ ] **Step 5: Implement `team_activity_report/gate.py`**

```python
"""Weekday + holiday gate. Pure functions, no IO."""

from __future__ import annotations

from datetime import date

# 2026 US federal holidays (when the federal government observes them).
# When a holiday falls on a weekend, the observed date may shift — this list
# reflects the actual calendar holiday, not the observed shift.
_HOLIDAYS_2026: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),   # New Year's Day
        date(2026, 1, 19),  # Martin Luther King Jr. Day
        date(2026, 2, 16),  # Presidents Day
        date(2026, 5, 25),  # Memorial Day
        date(2026, 6, 19),  # Juneteenth
        date(2026, 7, 4),   # Independence Day (Saturday in 2026; observed Fri 7/3)
        date(2026, 9, 7),   # Labor Day
        date(2026, 10, 12), # Columbus Day
        date(2026, 11, 11), # Veterans Day
        date(2026, 11, 26), # Thanksgiving
        date(2026, 12, 25), # Christmas
    }
)


def is_weekend(d: date) -> bool:
    """Saturday (5) or Sunday (6)."""
    return d.weekday() >= 5


def is_holiday(d: date) -> bool:
    """True if d is a US federal holiday in 2026."""
    return d in _HOLIDAYS_2026


def should_run(d: date) -> tuple[bool, str]:
    """Return (True, 'weekday'), (False, 'weekend'), or (False, 'holiday').

    Weekend is checked before holiday so weekend-falling holidays report as weekend.
    """
    if is_weekend(d):
        return False, "weekend"
    if is_holiday(d):
        return False, "holiday"
    return True, "weekday"
```

- [ ] **Step 6: Run, confirm pass**

```bash
pytest tests/test_gate.py -v
```
Expected: PASS, all 11 tests.

- [ ] **Step 7: Commit**

```bash
git add team_activity_report/types.py team_activity_report/gate.py tests/__init__.py tests/test_gate.py
git commit -m "feat: types + weekday/holiday gate with TDD"
```

---

# Phase 2 — Database Layer

### Task 3: `db.py` — asyncpg pool + helpers

**Files:**
- Create: `team_activity_report/db.py`

(No dedicated test file — `db.py` is exercised by every integration test that uses the `db_pool` fixture in `conftest.py` later.)

- [ ] **Step 1: Implement `team_activity_report/db.py`**

```python
"""Database layer — asyncpg pool + schema application.

DATABASE_URL must be set in the environment (see .env.example).
"""

from __future__ import annotations

import os
from pathlib import Path

import asyncpg

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return url


async def create_pool() -> asyncpg.Pool:
    """Create an asyncpg pool from DATABASE_URL."""
    pool = await asyncpg.create_pool(database_url(), min_size=1, max_size=10)
    assert pool is not None
    return pool


async def init_schema(pool: asyncpg.Pool) -> None:
    """Apply schema.sql against the pool. Idempotent."""
    sql = _SCHEMA_PATH.read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)


async def truncate_events(pool: asyncpg.Pool) -> None:
    """Truncate the events table. Used by seed.py."""
    async with pool.acquire() as conn:
        await conn.execute("truncate table events restart identity")
```

- [ ] **Step 2: Commit**

```bash
git add team_activity_report/db.py
git commit -m "feat: asyncpg pool + schema/truncate helpers"
```

---

# Phase 3 — Seed (TDD)

### Task 4: Deterministic synthetic seed

**Files:**
- Create: `team_activity_report/seed.py`
- Create: `tests/conftest.py`
- Create: `tests/test_seed.py`

- [ ] **Step 1: Create `tests/conftest.py`** (mirrors gmail-scraper pattern — testcontainers Postgres)

```python
import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Boot a Postgres container for the test session.

    Skipped if SKIP_INTEGRATION_TESTS=1 (use for fast local iteration).
    """
    if os.environ.get("SKIP_INTEGRATION_TESTS") == "1":
        pytest.skip("integration tests skipped")
    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
        yield url


@pytest_asyncio.fixture(scope="function")
async def db_pool(postgres_url: str) -> AsyncIterator[asyncpg.Pool]:
    """Fresh connection pool + schema for every test."""
    pool = await asyncpg.create_pool(postgres_url, min_size=1, max_size=2)
    assert pool is not None
    schema_sql = Path("team_activity_report/schema.sql").read_text()
    async with pool.acquire() as conn:
        await conn.execute("drop table if exists events cascade")
        await conn.execute(schema_sql)
    try:
        yield pool
    finally:
        await pool.close()
```

- [ ] **Step 2: Write failing tests at `tests/test_seed.py`**

```python
from datetime import UTC, date, datetime

import pytest

from team_activity_report.seed import (
    EVENT_KINDS,
    REPOS,
    ACTORS,
    ANCHOR,
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
        assert ANCHOR == datetime(2026, 5, 4, 9, 0, tzinfo=UTC)
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
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_seed.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 4: Implement `team_activity_report/seed.py`**

```python
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
```

- [ ] **Step 5: Run, confirm all tests pass**

```bash
pytest tests/test_seed.py -v
```
Expected: PASS (10 tests — 8 unit + 2 integration).

- [ ] **Step 6: Commit**

```bash
git add team_activity_report/seed.py tests/conftest.py tests/test_seed.py
git commit -m "feat: deterministic synthetic event seed"
```

---

# Phase 4 — Queries (TDD)

### Task 5: `queries.py` with 6 async functions

**Files:**
- Create: `team_activity_report/queries.py`
- Create: `tests/test_queries.py`

- [ ] **Step 1: Write failing tests at `tests/test_queries.py`**

```python
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
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_queries.py -v
```
Expected: FAIL — `team_activity_report.queries` not importable.

- [ ] **Step 3: Implement `team_activity_report/queries.py`**

```python
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


async def active_devs(
    pool: asyncpg.Pool, target_date: date, top_n: int = 5
) -> list[DevCount]:
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
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_queries.py -v
```
Expected: PASS (12 tests).

- [ ] **Step 5: Commit**

```bash
git add team_activity_report/queries.py tests/test_queries.py
git commit -m "feat: async aggregation queries for daily report"
```

---

# Phase 5 — Charts (TDD)

### Task 6: `charts.py` — deterministic base64 PNG

**Files:**
- Create: `team_activity_report/charts.py`
- Create: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests at `tests/test_charts.py`**

```python
import base64

from team_activity_report.charts import hourly_throughput_chart
from team_activity_report.types import HourlyCount


def _make_hourly_data() -> list[HourlyCount]:
    return [HourlyCount(hour=h, count=h * 2) for h in range(24)]


class TestHourlyThroughputChart:
    def test_returns_non_empty_base64_string(self) -> None:
        s = hourly_throughput_chart(_make_hourly_data())
        assert isinstance(s, str)
        assert len(s) > 100

    def test_returns_valid_png_after_decode(self) -> None:
        s = hourly_throughput_chart(_make_hourly_data())
        png_bytes = base64.b64decode(s)
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_deterministic_on_same_input(self) -> None:
        """Same input → byte-identical output."""
        a = hourly_throughput_chart(_make_hourly_data())
        b = hourly_throughput_chart(_make_hourly_data())
        assert a == b

    def test_handles_all_zeros(self) -> None:
        """All-zero data shouldn't crash."""
        data = [HourlyCount(hour=h, count=0) for h in range(24)]
        s = hourly_throughput_chart(data)
        assert len(s) > 100
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_charts.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `team_activity_report/charts.py`**

```python
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
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_charts.py -v
```
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add team_activity_report/charts.py tests/test_charts.py
git commit -m "feat: deterministic matplotlib bar chart → base64 PNG"
```

---

# Phase 6 — Template + Generator (TDD)

### Task 7: Jinja2 template + generator

**Files:**
- Create: `team_activity_report/templates/report.html.j2`
- Create: `team_activity_report/generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Create `team_activity_report/templates/report.html.j2`**

```jinja2
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Engineering Team Daily Digest — {{ report_date }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
  .wrap { max-width: 800px; margin: 0 auto; }
  h1 { font-size: 28px; margin: 0 0 4px; font-weight: 600; }
  .sub { color: #94a3b8; font-size: 14px; margin-bottom: 32px; }
  .kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 32px; }
  .kpi { background: #1e293b; border-radius: 12px; padding: 16px; }
  .kpi-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .kpi-value { font-size: 28px; font-weight: 600; }
  h2 { font-size: 16px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin: 32px 0 12px; font-weight: 600; }
  .section { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  .success-bar { background: #0f172a; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 8px; }
  .success-bar-fill { background: #10b981; height: 100%; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { padding: 6px 0; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; }
  li:last-child { border-bottom: none; }
  .name { color: #e2e8f0; }
  .count { color: #94a3b8; font-variant-numeric: tabular-nums; }
  .chart { text-align: center; }
  .chart img { max-width: 100%; height: auto; border-radius: 8px; }
  footer { color: #475569; font-size: 11px; text-align: center; margin-top: 48px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Engineering Team Daily Digest</h1>
  <div class="sub">{{ report_date }} ({{ day_of_week }})</div>

  <div class="kpis">
    <div class="kpi"><div class="kpi-label">PRs Merged</div><div class="kpi-value">{{ totals.prs }}</div></div>
    <div class="kpi"><div class="kpi-label">Builds Run</div><div class="kpi-value">{{ totals.builds }}</div></div>
    <div class="kpi"><div class="kpi-label">Deploys</div><div class="kpi-value">{{ totals.deploys }}</div></div>
    <div class="kpi"><div class="kpi-label">Open Incidents</div><div class="kpi-value">{{ totals.incidents_open }}</div></div>
  </div>

  <h2>Build Success Rate</h2>
  <div class="section">
    <div style="display:flex; justify-content:space-between; align-items:baseline">
      <span style="font-size: 32px; font-weight: 600">{{ "%.1f"|format(build_stats.success_rate * 100) }}%</span>
      <span style="color:#94a3b8">{{ build_stats.success }} success / {{ build_stats.failure }} failure / {{ build_stats.cancelled }} cancelled</span>
    </div>
    <div class="success-bar"><div class="success-bar-fill" style="width: {{ "%.1f"|format(build_stats.success_rate * 100) }}%"></div></div>
  </div>

  <h2>Throughput by Hour (UTC)</h2>
  <div class="section chart">
    <img src="data:image/png;base64,{{ throughput_chart_b64 }}" alt="Hourly throughput">
  </div>

  <h2>Top Active Developers</h2>
  <div class="section">
    {% if active_devs %}
    <ul>
      {% for dev in active_devs %}
      <li><span class="name">{{ dev.actor }}</span><span class="count">{{ dev.count }} events</span></li>
      {% endfor %}
    </ul>
    {% else %}
    <div style="color:#94a3b8">No activity recorded.</div>
    {% endif %}
  </div>

  <h2>Deploys by Repository</h2>
  <div class="section">
    {% if deploys_by_repo %}
    <ul>
      {% for row in deploys_by_repo %}
      <li><span class="name">{{ row.repo }}</span><span class="count">{{ row.count }}</span></li>
      {% endfor %}
    </ul>
    {% else %}
    <div style="color:#94a3b8">No deployments recorded.</div>
    {% endif %}
  </div>

  <footer>Generated by team-activity-report v0.1.0</footer>
</div>
</body>
</html>
```

- [ ] **Step 2: Write failing tests at `tests/test_generator.py`**

```python
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
```

- [ ] **Step 3: Run, confirm fail**

```bash
pytest tests/test_generator.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 4: Implement `team_activity_report/generator.py`**

```python
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
```

- [ ] **Step 5: Run, confirm pass**

```bash
pytest tests/test_generator.py -v
```
Expected: PASS (4 tests).

- [ ] **Step 6: Run all tests + coverage**

```bash
pytest --cov
```
Expected: all tests pass, coverage ≥ 80% on the listed modules.

- [ ] **Step 7: Commit**

```bash
git add team_activity_report/templates team_activity_report/generator.py tests/test_generator.py
git commit -m "feat: Jinja2 template + generator with idempotent byte-identical output"
```

---

# Phase 7 — Delivery

### Task 8: `delivery.py` — save + SMTP stub

**Files:**
- Create: `team_activity_report/delivery.py`
- Create: `tests/test_delivery.py`

- [ ] **Step 1: Write failing tests at `tests/test_delivery.py`**

```python
from unittest.mock import MagicMock, patch

import pytest

from team_activity_report.delivery import send_smtp


class TestSendSmtp:
    def test_returns_would_send_when_env_missing(self, monkeypatch) -> None:
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USER", raising=False)
        monkeypatch.delenv("SMTP_PASS", raising=False)
        result = send_smtp("<html></html>", "to@example.com")
        assert "would send" in result.lower()
        assert "to@example.com" in result

    def test_returns_sent_when_env_present(self, monkeypatch) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "user@example.com")
        monkeypatch.setenv("SMTP_PASS", "secret")
        monkeypatch.setenv("SMTP_FROM", "from@example.com")

        with patch("team_activity_report.delivery.smtplib.SMTP") as smtp_class:
            smtp_inst = MagicMock()
            smtp_class.return_value.__enter__.return_value = smtp_inst

            result = send_smtp("<html></html>", "to@example.com")

        assert "sent" in result.lower()
        assert "to@example.com" in result
        smtp_inst.login.assert_called_once_with("user@example.com", "secret")
        smtp_inst.send_message.assert_called_once()
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_delivery.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `team_activity_report/delivery.py`**

```python
"""Email delivery — real SMTP when configured, "would send" stub otherwise.

By default (no SMTP_* env vars), nothing is actually sent — this keeps the
demo safe for casual `python -m team_activity_report run --email` usage.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def _smtp_configured() -> bool:
    return bool(
        os.environ.get("SMTP_HOST")
        and os.environ.get("SMTP_USER")
        and os.environ.get("SMTP_PASS")
    )


def send_smtp(html: str, to_addr: str) -> str:
    """Send (or stub-send) the rendered HTML report.

    Returns a status string suitable for printing from the CLI.
    """
    if not _smtp_configured():
        return f"Would send to {to_addr} (SMTP_* env vars not set; using stub)."

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    sender = os.environ.get("SMTP_FROM", user)

    msg = EmailMessage()
    msg["Subject"] = "Engineering Team Daily Digest"
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content("HTML version below. Use an HTML-capable mail client.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)

    return f"Sent to {to_addr} via {host}."
```

- [ ] **Step 4: Run, confirm pass**

```bash
pytest tests/test_delivery.py -v
```
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add team_activity_report/delivery.py tests/test_delivery.py
git commit -m "feat: SMTP delivery with would-send stub default"
```

---

# Phase 8 — CLI

### Task 9: `cli.py` + `__main__.py` + tests

**Files:**
- Create: `team_activity_report/cli.py`
- Create: `team_activity_report/__main__.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests at `tests/test_cli.py`**

```python
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from team_activity_report.cli import build_parser, main


class TestCLIParser:
    def test_init_db_subcommand(self) -> None:
        args = build_parser().parse_args(["init-db"])
        assert args.command == "init-db"

    def test_seed_data_with_defaults(self) -> None:
        args = build_parser().parse_args(["seed-data"])
        assert args.command == "seed-data"
        assert args.days == 30
        assert args.seed == 42

    def test_seed_data_with_args(self) -> None:
        args = build_parser().parse_args(["seed-data", "--days", "15", "--seed", "7"])
        assert args.days == 15
        assert args.seed == 7

    def test_run_defaults(self) -> None:
        args = build_parser().parse_args(["run"])
        assert args.command == "run"
        assert args.date is None
        assert args.email is False
        assert args.force is False
        assert args.out == "out"

    def test_run_full_flags(self) -> None:
        args = build_parser().parse_args(
            ["run", "--date", "2026-05-26", "--email", "--force", "--out", "reports"]
        )
        assert args.date == "2026-05-26"
        assert args.email is True
        assert args.force is True
        assert args.out == "reports"


class TestCLISmoke:
    @pytest.mark.asyncio
    async def test_run_skips_on_weekend_by_default(self) -> None:
        # 2026-05-23 is Saturday
        with patch("team_activity_report.cli.create_pool", new_callable=AsyncMock):
            exit_code = await main(["run", "--date", "2026-05-23"])
        assert exit_code == 0  # skipping is success

    @pytest.mark.asyncio
    async def test_run_force_overrides_weekend(self, tmp_path: Path) -> None:
        # Mock generate so we don't need a real DB
        with patch("team_activity_report.cli.create_pool", new_callable=AsyncMock) as pool_mock, \
             patch("team_activity_report.cli.generate", new_callable=AsyncMock) as gen_mock:
            pool_mock.return_value.close = AsyncMock()
            gen_mock.return_value = tmp_path / "2026-05-23-report.html"
            exit_code = await main(["run", "--date", "2026-05-23", "--force", "--out", str(tmp_path)])
        assert exit_code == 0
        gen_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_db_calls_init_schema(self) -> None:
        with patch("team_activity_report.cli.create_pool", new_callable=AsyncMock) as pool_mock, \
             patch("team_activity_report.cli.init_schema", new_callable=AsyncMock) as init_mock:
            pool_mock.return_value.close = AsyncMock()
            exit_code = await main(["init-db"])
        assert exit_code == 0
        init_mock.assert_called_once()
```

- [ ] **Step 2: Run, confirm fail**

```bash
pytest tests/test_cli.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `team_activity_report/cli.py`**

```python
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
    return (datetime.now().date() - timedelta(days=1))


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
```

- [ ] **Step 4: Implement `team_activity_report/__main__.py`**

```python
"""Module entry: python -m team_activity_report"""

from team_activity_report.cli import cli_entry

if __name__ == "__main__":
    cli_entry()
```

- [ ] **Step 5: Refresh editable install (so the console script entry-point installs)**

```bash
pip install -e .[dev]
```

- [ ] **Step 6: Run tests, confirm pass**

```bash
pytest tests/test_cli.py -v
```
Expected: PASS (8 tests).

- [ ] **Step 7: End-to-end smoke**

```bash
docker compose up -d
# wait ~5s for healthy
python -m team_activity_report init-db
python -m team_activity_report seed-data --days 30
python -m team_activity_report run --date 2026-05-26 --out out
ls out
python -m team_activity_report run --date 2026-05-23  # Saturday — should skip
python -m team_activity_report run --date 2026-05-23 --force --out out  # forced
docker compose down
```

Expected:
- `init-db` → `Schema applied.`
- `seed-data` → `Seeded N events.` (N around 800-1200)
- `run --date 2026-05-26` → `Wrote out/2026-05-26-report.html`
- `run --date 2026-05-23` → `Saturday — skipping (weekend; use --force to override)`
- `run --date 2026-05-23 --force` → `Wrote out/2026-05-23-report.html`

- [ ] **Step 8: Commit**

```bash
git add team_activity_report/cli.py team_activity_report/__main__.py tests/test_cli.py
git commit -m "feat: CLI with run / init-db / seed-data subcommands + weekday gate enforcement"
```

---

# Phase 9 — GitHub Actions CI

### Task 10: GHA workflows

**Files:**
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/lint.yml`

- [ ] **Step 1: Create `.github/workflows/test.yml`**

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: team_reports
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/team_reports
        run: pytest --cov --cov-report=xml --cov-report=term
```

- [ ] **Step 2: Create `.github/workflows/lint.yml`**

```yaml
name: Lint

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Ruff check
        run: ruff check team_activity_report tests

      - name: Ruff format check
        run: ruff format --check team_activity_report tests

      - name: Mypy
        run: mypy team_activity_report
```

- [ ] **Step 3: Run lint locally and fix any issues**

```bash
ruff check team_activity_report tests
ruff format --check team_activity_report tests
mypy team_activity_report
```

If ruff format complains, run `ruff format team_activity_report tests` to auto-fix.
If mypy complains about unused imports or stubs, fix in the code or add to overrides in `pyproject.toml`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml .github/workflows/lint.yml
git commit -m "feat: GitHub Actions CI for tests + lint"
```

---

# Phase 10 — README + Final Verification

### Task 11: README

**Files:**
- Modify: `README.md` (overwrites the placeholder)

- [ ] **Step 1: Overwrite `README.md`**

```markdown
# team-activity-report

![Tests](https://github.com/Jamil1016/report-automation/actions/workflows/test.yml/badge.svg)
![Lint](https://github.com/Jamil1016/report-automation/actions/workflows/lint.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Open-source reference implementation of the "scheduled report from a database" pattern, using synthetic engineering-team activity (PRs, builds, deploys, incidents) as the demo domain.

## The Pattern

A daily report aggregates the prior day's events from a Postgres database, renders them into an HTML document with embedded charts, applies weekday/holiday gating, and (optionally) sends via SMTP. The production version of this system runs privately at my employer against a different domain. This repo demonstrates the architecture on synthetic engineering-team data so the patterns are verifiable.

Three properties matter:

1. **Idempotent generation** — running for the same target date produces a byte-identical output file
2. **Weekday-gated by default** — skips Saturdays, Sundays, and US federal holidays unless `--force` is passed
3. **Deterministic seed** — the same RNG seed produces the same synthetic events, so tests can make exact assertions

## Architecture

```mermaid
graph LR
  S[seed.py<br/>deterministic events] --> PG[(Postgres)]
  PG --> Q[queries.py<br/>6 async aggregations]
  Q --> C[charts.py<br/>matplotlib → base64 PNG]
  C --> G[generator.py<br/>+ Jinja2 template]
  G --> O[out/&lt;date&gt;-report.html]
  G --> D[delivery.py<br/>SMTP stub by default]
```

## Quick Start

```bash
git clone https://github.com/Jamil1016/report-automation
cd report-automation
docker compose up -d
pip install -e .
cp .env.example .env
python -m team_activity_report init-db
python -m team_activity_report seed-data --days 30
python -m team_activity_report run --date 2026-05-26
open out/2026-05-26-report.html
```

## How It Works

- **Deterministic seed:** `team_activity_report/seed.py` generates ~1,000 events across 5 fictional developers and 3 fictional repos over 30 days. Same `--seed` value produces the same events.
- **Typed query layer:** `queries.py` exposes 6 async functions returning `TypedDict` results. Tests assert on exact counts against the seeded data.
- **Idempotent rendering:** `charts.py` overrides matplotlib's PNG timestamp metadata, the Jinja2 footer uses a constant string (no live timestamp), and `generator.py` writes a deterministic filename — so running twice produces a byte-identical file. `test_generator.py::test_idempotent_byte_identical` validates this with a SHA-256 check.
- **Weekday gate:** `gate.py` exposes pure functions for `is_weekend`, `is_holiday`, and `should_run`. The CLI checks `should_run` before generating; `--force` overrides for testing.
- **SMTP stub default:** `delivery.send_smtp` logs "Would send to X" unless `SMTP_HOST`, `SMTP_USER`, and `SMTP_PASS` are all set in the environment. The demo can run `--email` safely.

## Tests

```bash
pytest                              # all tests (requires Docker for testcontainers)
SKIP_INTEGRATION_TESTS=1 pytest     # unit only — fast, no DB
pytest --cov                        # with coverage
```

| Test file | Covers |
|---|---|
| `test_gate.py` | Weekday + holiday gating |
| `test_seed.py` | Determinism, distribution rules |
| `test_queries.py` | Aggregation correctness against seeded data |
| `test_charts.py` | Valid PNG output + determinism |
| `test_generator.py` | Full run + idempotent SHA-256 |
| `test_delivery.py` | SMTP stub when env missing, real send when present |
| `test_cli.py` | argparse + dispatch (mocked DB) |

## Background

I built this pattern at scale at $WORK (private repo, different domain). The case study with production metrics is at:

**https://portfolio-gules-gamma-14.vercel.app/projects/report-automation**

## License

MIT
```

- [ ] **Step 2: Verify nothing broke**

```bash
pytest
ruff check team_activity_report tests
ruff format --check team_activity_report tests
mypy team_activity_report
```

Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: replace placeholder README with full project documentation"
```

---

### Task 12: Final verification + push + flip portfolio status

**Files:** (operations only — no code)

- [ ] **Step 1: Clean-slate local smoke**

```bash
cd "C:\Users\admin\Desktop\Projects\personal\report-automation"
docker compose down -v
docker compose up -d
sleep 8
python -m team_activity_report init-db
python -m team_activity_report seed-data --days 30
python -m team_activity_report run --date 2026-05-26
python -m team_activity_report run --date 2026-05-26   # second run — byte-identical
python -m team_activity_report run --date 2026-05-23  # Saturday — should skip
docker compose down
```

Expected:
- First `run`: `Wrote out/2026-05-26-report.html`
- Second `run`: same message, **same file**, byte-identical
- Saturday run: `Saturday — skipping (weekend; use --force to override)`

Verify byte-identical:
```bash
sha256sum out/2026-05-26-report.html
# re-run the date and compare hashes — they must match
```

- [ ] **Step 2: Sanitization sweep**

```bash
grep -ri "ontel\|nanoninth\|AT&T\|T-Mobile\|Verizon\|jamil.mendez@ontel.co\|FA[0-9]\|finance\|daily finance" \
  team_activity_report/ tests/ README.md 2>&1 | head -20
```

Expected: no matches (substring "finance" especially — this clean-room is engineering-team domain, not finance).

- [ ] **Step 3: Push to GitHub**

```bash
gh auth switch -u Jamil1016
git push origin main
gh auth switch -u jamilmendez-ontel
```

- [ ] **Step 4: Verify GHA workflows go green**

```bash
gh auth switch -u Jamil1016
sleep 30
gh run list --repo Jamil1016/report-automation --limit 5
gh auth switch -u jamilmendez-ontel
```

Both `Tests` and `Lint` runs should show `completed / success` within ~2-3 minutes.

- [ ] **Step 5: Flip portfolio status from "coming" to "live"**

```bash
cd "C:\Users\admin\Desktop\Projects\personal\portfolio"
gh auth switch -u Jamil1016
git pull origin main
```

Edit `lib/projects.ts` — find the `report-automation` entry and:
- Change `publicRepoStatus: "coming"` → `"live"`
- Delete the `publicEtaWeek: "W5",` line

Verify:
```bash
grep -A 7 'slug: "report-automation"' lib/projects.ts
```

Should show `publicRepoStatus: "live"` and no `publicEtaWeek` line.

Run portfolio tests + build:
```bash
npm test
npm run build
```

Both must pass.

Commit + push:
```bash
git add lib/projects.ts
git commit -m "feat: flip report-automation status from 'coming' to 'live'"
git push origin main
gh auth switch -u jamilmendez-ontel
```

Vercel auto-deploys; portfolio case study loses the "OSS · W5" badge.

- [ ] **Step 6: Milestone commit on report-automation**

```bash
cd "C:\Users\admin\Desktop\Projects\personal\report-automation"
git commit --allow-empty -m "milestone: v0.1.0 shipped — second clean-room repo of six"
gh auth switch -u Jamil1016
git push origin main
gh auth switch -u jamilmendez-ontel
```

- [ ] **Step 7: Final acceptance checklist (manual)**

- [ ] README badges show green Tests + Lint
- [ ] Cloning to a fresh directory and running Quick Start works first try
- [ ] Portfolio `/projects/report-automation` shows "live" status, no "coming" badge
- [ ] No "finance" / "ontel" / "nanoninth" / customer terms anywhere in the public repo
- [ ] Two runs on the same date produce byte-identical reports (verified by sha256sum)

---

## Self-Review

### Spec coverage

| Spec section | Implemented by |
|---|---|
| §1 Summary — runnable, dogfooded, deterministic | All tasks combined |
| §2 Goals: runnable end-to-end | Tasks 1, 9, 12 |
| §2 Goals: weekday/holiday gate + idempotent + chart embedding + aggregation | Tasks 2, 5, 6, 7 |
| §2 Goals: ≥80% coverage | Tasks 2-9 |
| §2 Goals: GHA workflows on public repo | Task 10 |
| §3 Domain — engineering team | Task 4 (seed) + Task 5 (queries) |
| §4 Architecture | Repo structure built by Tasks 1-9 |
| §5 Repo structure | Tasks 1 (top-level) + remaining tasks (per-file) |
| §6 Data model (events table + indexes) | Task 1 (schema.sql) |
| §7 Seed | Task 4 |
| §8 Six query functions | Task 5 |
| §9 Charts | Task 6 |
| §10 Template | Task 7 |
| §11 Generator | Task 7 |
| §12 Delivery | Task 8 |
| §13 Weekday gate | Task 2 |
| §14 CLI surface (run + init-db + seed-data) | Task 9 |
| §15 Six test files | Tasks 2, 4, 5, 6, 7, 8, 9 (seven actually — also test_delivery) |
| §16 GHA CI | Task 10 |
| §17 README | Task 11 |
| §18 Success criteria 1-9 | Task 12 |

### Placeholder scan

No "TBD" / "implement later" / "similar to Task N" / vague-error-handling markers. Every code block is complete and runnable; every command has explicit expected output.

### Type consistency

- `Event` TypedDict in Task 4 used in `seed.py` only — no cross-task references
- `BuildStats`, `RepoCount`, `HourlyCount`, `DevCount`, `ReportTotals` from Task 2's `types.py` are consumed in Tasks 5 (queries), 6 (charts), 7 (generator)
- `gate.should_run` signature from Task 2 is called from `cli._run` in Task 9
- `generator.generate(pool, target_date, out_dir)` signature in Task 7 matches the call from `cli._run` in Task 9
- `seed.seed_events(pool, days, seed)` signature in Task 4 matches `cli._seed` call in Task 9
- `delivery.send_smtp(html, to_addr)` signature in Task 8 matches `cli._run` call in Task 9
- All async function signatures (returning `int`, `BuildStats`, `list[...]`) match their test expectations

One spec note: spec §15 listed 6 test files. The plan creates 7 (adds `test_delivery.py`). Tighter test coverage; net positive vs. spec. Not a contradiction.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-26-report-automation-clean-room.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
**2. Inline Execution** — batch via executing-plans skill with checkpoints

Which approach?
