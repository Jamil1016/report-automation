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
