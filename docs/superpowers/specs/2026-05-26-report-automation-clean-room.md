# Clean-Room report-automation — Design Spec

**Date:** 2026-05-26
**Owner:** Jamil Mendez (`Jamil1016` on GitHub)
**Status:** Approved for implementation planning
**Context:** Second of six clean-room reference implementations (Sub-project B.2 of the portfolio expansion). The production version operates privately at the user's employer; this repo is the open-source pattern-demo on synthetic data using a deliberately different domain (engineering team activity, not finance).

**Cross-references:**
- Portfolio case study: https://portfolio-gules-gamma-14.vercel.app/projects/report-automation
- First clean-room reference (gmail-scraper, sister repo): https://github.com/Jamil1016/gmail-scraper
- Pattern source: production work on private repo (`jamilmendez-ontel/report-automation`, currently in active development — clean-room version MUST be doubly distinct in domain and naming)

---

## 1. Summary

A working open-source Python implementation of the "scheduled report" pattern: query a database, aggregate, render an HTML report with embedded charts, and deliver. Demo domain is **engineering team daily activity** — PRs merged, builds run, deploys, incidents — pre-seeded into Postgres with ~1,000 synthetic events across 30 days. Generator is **idempotent** (re-running for the same date produces identical output) and **weekday-gated** (skips Saturdays, Sundays, and US federal holidays). Same architectural pattern as the production system; entirely new domain and codebase.

---

## 2. Goals & Non-Goals

### Goals
- Runnable end-to-end on a fresh machine: `git clone && docker compose up -d && pip install -e . && python -m team_activity_report init-db && seed-data && run`
- Demonstrates **weekday/holiday gating**, **idempotent report generation**, **HTML email construction with embedded charts**, and **SQL aggregation queries** patterns from production
- ≥ 1,000 synthetic events seeded deterministically (same seed → same output) across 5 fictional devs and 3 fictional repos
- pytest suite with ≥ 80% coverage on `queries.py`, `generator.py`, `gate.py`
- GitHub Actions CI on the public repo (Tests + Lint) — green badge in README
- README under 200 lines with Mermaid + quick-start, links back to portfolio case study
- Zero references to production employer / finance domain / customers / proprietary terms

### Non-Goals (v1)
- Real GitHub Actions cron schedule on the public repo (the README documents the integration pattern; doesn't wire up live cron)
- Real SMTP delivery (a `--email` flag triggers a "would send to X" log stub — never actually emails)
- Apps Script trigger simulation (over-engineered for clean-room)
- Real-time event ingestion (the events table is pre-seeded; no ingestion pipeline in this repo)
- Multi-tenant / multi-team support
- Configurable templates / per-team customization
- Slack / Discord / Teams delivery integrations
- Database other than Postgres (no SQLite swap, no MySQL)
- Web UI / dashboard for viewing reports (reports are static HTML files saved to disk)
- Vector / semantic search over historical reports
- PDF generation (HTML only)

---

## 3. Domain — Engineering Team Daily Digest

The repo simulates a daily report summarizing a small engineering team's activity. Domain chosen to:
- Be **universally recognizable** to recruiters and engineers (no industry-specific jargon)
- **Pair with gmail-scraper's CI domain** for portfolio coherence — both repos work with engineering-team data
- Be **deliberately distinct from finance** so there's no confusion with the production system

Events tracked:
| `kind` value | What it represents | Aggregation in report |
|---|---|---|
| `pr_merged` | A pull request was merged | count |
| `build_completed` | A CI build finished | count, success rate, throughput by hour |
| `deploy` | A deployment landed | count by repo |
| `incident_opened` | An incident was opened | open count = `opened - closed` |
| `incident_closed` | An incident was closed | (used for open count) |

5 fictional devs: `alice-dev`, `bob-eng`, `charlie-ops`, `dana-qa`, `eve-platform`.
3 fictional repos: `widget-api`, `payments-svc`, `web-app`.

Deliberate seed distribution:
- More PRs on Tuesdays/Wednesdays (mid-week peak)
- Fewer deploys on Fridays (intentional engineering practice)
- ~5% of builds fail
- 1-2 incidents per week, most resolved within hours

---

## 4. Architecture

```
                  ┌──────────────┐
                  │ Postgres     │
                  │ (events)     │
                  └──────┬───────┘
                         │
                         ▼
        ┌─────────────────────────────────┐
        │ queries.py                      │
        │ - count_prs(date)               │
        │ - build_stats(date)             │
        │ - deploys_by_repo(date)         │
        │ - open_incidents_as_of(date)    │
        │ - throughput_by_hour(date)      │
        │ - active_devs(date)             │
        └──────────────┬──────────────────┘
                       │ aggregations
                       ▼
        ┌─────────────────────────────────┐
        │ charts.py                       │
        │ matplotlib → base64 PNG         │
        └──────────────┬──────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ generator.py                    │
        │ + templates/report.html.j2      │
        └──────────────┬──────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ delivery.py                     │
        │ - save_to_disk (always)         │
        │ - send_smtp (if --email + env)  │
        └─────────────────────────────────┘
```

Each module has one clear responsibility:
- `queries.py` — async DB queries returning typed result objects, no rendering
- `charts.py` — matplotlib rendering only, returns base64 PNG strings
- `generator.py` — orchestrates query → chart → template → output
- `delivery.py` — save and optional SMTP
- `gate.py` — pure functions, no IO

---

## 5. Repository Layout

```
report-automation/                              # Jamil1016/report-automation
├── team_activity_report/
│   ├── __init__.py
│   ├── __main__.py                             # python -m team_activity_report entry
│   ├── cli.py                                  # argparse: run / init-db / seed-data
│   ├── generator.py                            # query → chart → template → output
│   ├── queries.py                              # asyncpg-based SQL aggregations
│   ├── charts.py                               # matplotlib → base64 PNG
│   ├── delivery.py                             # save_to_disk + send_smtp stub
│   ├── gate.py                                 # should_run(date)
│   ├── seed.py                                 # synthetic event generator (deterministic)
│   ├── db.py                                   # asyncpg pool + helpers
│   ├── schema.sql                              # CREATE TABLE events + indexes
│   ├── types.py                                # TypedDicts for query results
│   └── templates/
│       └── report.html.j2
├── out/                                        # (gitignored) — generated reports land here
├── tests/
│   ├── __init__.py
│   ├── conftest.py                             # testcontainers Postgres
│   ├── test_gate.py                            # weekday/holiday gating
│   ├── test_seed.py                            # determinism + row count
│   ├── test_queries.py                         # aggregation correctness
│   ├── test_charts.py                          # PNG bytes non-empty + decodable
│   ├── test_generator.py                       # end-to-end idempotency
│   └── test_cli.py                             # argparse + dispatch
├── .github/
│   └── workflows/
│       ├── test.yml                            # pytest + coverage
│       └── lint.yml                            # ruff + mypy
├── .env.example
├── .gitignore
├── docker-compose.yml                          # Postgres 16
├── pyproject.toml
├── README.md
└── LICENSE                                     # MIT
```

---

## 6. Data Model

```sql
-- team_activity_report/schema.sql
create table if not exists events (
  id               bigserial primary key,
  occurred_at      timestamptz not null,
  kind             text not null
                   check (kind in ('pr_merged', 'build_completed', 'deploy',
                                   'incident_opened', 'incident_closed')),
  actor            text not null,
  repo             text,
  status           text,                        -- nullable; only set for build_completed
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

**Why this shape:** single events table is the simplest model that lets every aggregation query be a `WHERE kind = $1 AND occurred_at BETWEEN ...`. The `payload` JSONB column absorbs event-type-specific fields without schema migration (e.g. `incident_opened` includes severity in payload).

---

## 7. Seed (`team_activity_report/seed.py`)

Deterministic synthetic event generator. Given a fixed RNG seed (default `42`) and a number of days (default `30`), produces ~1,000 events distributed across 5 devs and 3 repos.

Distribution rules:
- **PR merges:** ~3 per workday per dev. None on weekends. Slight Tue/Wed peak.
- **Build completions:** ~5 per PR merge plus continuous background builds during work hours
- **Deploys:** 1-3 per workday across repos. Fridays are quiet (1 max).
- **Incidents:** ~1-2 per week, randomly assigned to a repo. ~80% resolved same day (close event 1-6 hours later); ~20% resolved next workday.

Same seed → exactly the same events (positions, timestamps, actors). This is required for the test suite to make exact-count assertions on aggregations.

CLI:
```bash
python -m team_activity_report seed-data --days 30 --seed 42
```

Idempotent: a TRUNCATE precedes the insert so re-seeding starts clean.

---

## 8. Queries (`team_activity_report/queries.py`)

Async functions taking an `asyncpg.Pool` + a target date, returning typed results:

```python
async def count_prs(pool: asyncpg.Pool, target_date: date) -> int: ...
async def build_stats(pool: asyncpg.Pool, target_date: date) -> BuildStats: ...
async def deploys_by_repo(pool: asyncpg.Pool, target_date: date) -> list[RepoCount]: ...
async def open_incidents_as_of(pool: asyncpg.Pool, target_date: date) -> int: ...
async def throughput_by_hour(pool: asyncpg.Pool, target_date: date) -> list[HourlyCount]: ...
async def active_devs(pool: asyncpg.Pool, target_date: date, top_n: int = 5) -> list[DevCount]: ...
```

`BuildStats`, `RepoCount`, `HourlyCount`, `DevCount` are `TypedDict`s in `types.py`. All queries reference `occurred_at` at `AT TIME ZONE 'UTC'` (no Eastern Time conversion in this repo — the production system needs ET conversion per the user's rule, but this clean-room demo uses pure UTC and notes the convention in the README without leaking the work-side requirement).

`build_stats` returns:
```python
class BuildStats(TypedDict):
    total: int
    success: int
    failure: int
    cancelled: int
    success_rate: float  # 0.0 to 1.0
```

`open_incidents_as_of`: counts `incident_opened` minus `incident_closed` where occurred_at ≤ end of target_date. Lets the report show "still open" not "opened today".

---

## 9. Charts (`team_activity_report/charts.py`)

Single chart type for v1: **bar chart of throughput by hour**. Returns base64-encoded PNG string suitable for inline embedding in HTML email (`<img src="data:image/png;base64,...">`).

```python
def hourly_throughput_chart(hourly: list[HourlyCount]) -> str:
    """Render bar chart of activity by hour. Returns base64 PNG."""
```

matplotlib configuration:
- Dark theme (`bg='#0f172a'`, text `'#e2e8f0'`) to match the portfolio's visual style
- 800×400 px (sized for inline email)
- No interactive features (matplotlib Agg backend)
- Deterministic output (no random colors, no timestamps in output)

Determinism is critical: `test_generator.py` asserts that two runs against the same data produce byte-identical chart PNG (so the report file is byte-identical too).

---

## 10. Template (`team_activity_report/templates/report.html.j2`)

Single Jinja2 template. Inline CSS (email-safe). Receives a context dict:

```python
{
    "report_date": date,
    "day_of_week": str,            # "Tuesday"
    "totals": {
        "prs": int,
        "builds": int,
        "deploys": int,
        "incidents_open": int,
    },
    "build_stats": BuildStats,
    "deploys_by_repo": list[RepoCount],
    "active_devs": list[DevCount],
    "throughput_chart_b64": str,   # base64 PNG
}
```

Renders:
1. Header — "Engineering Team Daily Digest — <date> (<day>)"
2. KPI grid — 4 large numbers (PRs / builds / deploys / open incidents)
3. Build success rate — percentage + breakdown bar
4. Throughput chart — inline base64 PNG
5. Top devs — sorted list
6. Deploys by repo — sorted list
7. Footer — "Generated by team-activity-report v0.1.0 at <ISO timestamp omitted for determinism>"

Last line uses a constant string (no live timestamp) so the file is byte-identical on re-runs.

---

## 11. Generator (`team_activity_report/generator.py`)

Single entry function:

```python
async def generate(
    pool: asyncpg.Pool,
    target_date: date,
    out_dir: Path,
) -> Path:
    """Generate the report for target_date. Returns the path to the written HTML file."""
```

Implementation:
1. Run all six queries (in a single transaction for snapshot consistency)
2. Build the chart PNG
3. Build the Jinja2 context
4. Render template
5. Write to `<out_dir>/<YYYY-MM-DD>-report.html`
6. Return path

Idempotent: writing to the same path on re-run produces identical bytes. Validated by `test_generator.py`.

---

## 12. Delivery (`team_activity_report/delivery.py`)

Two functions:

```python
def save_to_disk(report_path: Path) -> None: ...  # no-op, generator already wrote
def send_smtp(html: str, to_addr: str) -> str:
    """If SMTP_HOST + SMTP_USER + SMTP_PASS env vars are all set, send.
    Otherwise log 'would send to X' and return that string.
    Returns the action taken as a string for the CLI to print.
    """
```

`--email` flag in CLI calls `send_smtp`. By default (no SMTP env vars), the report is generated to disk only — the demo never accidentally sends anything.

---

## 13. Weekday Gate (`team_activity_report/gate.py`)

Pure functions, no IO:

```python
def is_weekend(d: date) -> bool: ...
def is_holiday(d: date) -> bool: ...  # 2026 US federal holidays hardcoded
def should_run(d: date) -> tuple[bool, str]:
    """Returns (True, 'weekday') or (False, 'weekend') or (False, 'holiday')."""
```

CLI checks `should_run` before generating. `--force` overrides.

Holiday list (2026 US federal):
- 2026-01-01 (New Year's)
- 2026-01-19 (MLK Day)
- 2026-02-16 (Presidents Day)
- 2026-05-25 (Memorial Day)
- 2026-06-19 (Juneteenth)
- 2026-07-03 (Independence Day observed)
- 2026-09-07 (Labor Day)
- 2026-10-12 (Columbus Day)
- 2026-11-11 (Veterans Day)
- 2026-11-26 (Thanksgiving)
- 2026-12-25 (Christmas)

---

## 14. CLI (`team_activity_report/cli.py`)

```
python -m team_activity_report init-db
python -m team_activity_report seed-data [--days 30] [--seed 42]
python -m team_activity_report run [--date YYYY-MM-DD] [--email] [--force] [--out DIR]
python -m team_activity_report --help
```

### `run` flow:
1. Resolve target_date (default: yesterday)
2. Check `should_run(target_date)` unless `--force`
3. If skipping, print `<day-of-week> — skipping (<reason>; use --force to override)` and exit 0. Example: `Saturday — skipping (weekend; use --force to override)`
4. Otherwise generate via `generator.generate()`
5. Print `Wrote out/<date>-report.html`
6. If `--email`: call `delivery.send_smtp()` and print action

---

## 15. Testing

| File | Responsibility | Coverage target |
|---|---|---|
| `test_gate.py` | `is_weekend`, `is_holiday`, `should_run` against fixed dates | 100% of `gate.py` |
| `test_seed.py` | Same seed produces same events; ~1,000 events for 30 days; no weekend PRs | 90% of `seed.py` |
| `test_queries.py` | Each query returns expected counts against seeded data | ≥ 90% of `queries.py` |
| `test_charts.py` | `hourly_throughput_chart` returns non-empty base64 string; decoding produces valid PNG bytes | covers `charts.py` |
| `test_generator.py` | Full run produces a file; running twice produces byte-identical output; output contains expected sections | ≥ 85% of `generator.py` |
| `test_cli.py` | argparse + dispatch (mocked DB) | covers `cli.py` happy path |

Integration tests (queries, generator, seed) use `testcontainers-postgres` — same pattern as gmail-scraper.

---

## 16. CI on the Public Repo

`.github/workflows/test.yml` — pytest + coverage with a Postgres 16 service container. Triggers on push + pull_request to main.

`.github/workflows/lint.yml` — ruff check + ruff format check + mypy. Same triggers.

Both badges in README header.

No daily-cron workflow in v1 (deferred to v0.2 — README documents the integration pattern but doesn't wire up live execution).

---

## 17. README Structure

Tight, hiring-friendly:

1. Title + badges (Tests, Lint, License)
2. One-liner + a paragraph framing the pattern (scheduled reports against a DB → HTML + charts → delivery)
3. **Architecture** — Mermaid diagram (same shape as Section 4)
4. **Quick start** — 6-line shell block
5. **How it works** — 3 numbered points: deterministic seed → typed query layer → idempotent rendering
6. **Tests** — table of test files
7. **Background** — "I built this pattern at scale at $WORK against finance data. This is a clean-room implementation on synthetic engineering-team data so the architecture is verifiable. Portfolio case study at https://..."
8. **License** — MIT

Target: ≤ 200 lines including code blocks.

---

## 18. Success Criteria

1. `git clone && docker compose up -d && pip install -e . && python -m team_activity_report init-db && seed-data && run --force --date 2026-05-26` works on a fresh machine
2. All six test files green; coverage ≥ 80% on `queries.py`, `generator.py`, `gate.py`
3. `.github/workflows/test.yml` and `lint.yml` show green badges on the README
4. Output HTML contains all 7 sections (header, KPI grid, build success rate, throughput chart, top devs, deploys by repo, footer)
5. Running `run --date <same>` twice produces a byte-identical file (validated by checksum in test_generator.py)
6. `run --date <weekend>` exits 0 with message "Saturday — skipping (use --force)"
7. README ≤ 200 lines
8. Sanitization clean — no employer / finance / customer / proprietary terms in any committed file
9. Portfolio case study at `/projects/report-automation` flips from `publicRepoStatus: "coming"` to `"live"`

---

## 19. Out of Scope (Future Versions)

- v0.2: Live daily GHA cron schedule rendering reports to a `/reports/` folder, committed back to the repo (shows the actual scheduling pattern in action)
- v0.2: Slack webhook delivery
- v0.3: Configurable templates per audience (engineering team vs. exec summary)
- v0.3: Real-time event ingestion API (POST /events) instead of pre-seeded data
- v0.3: Multi-team / multi-tenant support
- Never (out of pattern): web UI, mobile app, PDF generation, vector search

---

## 20. Open Questions (resolve during implementation)

- **Chart library:** matplotlib is the choice. Plotly would produce interactive charts but the inline-PNG requirement for email rules it out. Skip plotly.
- **HTML purifier:** the Jinja2 template renders trusted content (all values come from our own DB), so no purifier needed. If we ever accept user-submitted event data, add one.
- **Holiday list locale:** US federal only for v1. If we ever expand, swap to the `holidays` PyPI package.
- **Coverage badge service:** Codecov (free for OSS) preferred — same as gmail-scraper.

These don't block the implementation plan.
