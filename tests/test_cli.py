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
        with (
            patch("team_activity_report.cli.create_pool", new_callable=AsyncMock) as pool_mock,
            patch("team_activity_report.cli.generate", new_callable=AsyncMock) as gen_mock,
        ):
            pool_mock.return_value.close = AsyncMock()
            gen_mock.return_value = tmp_path / "2026-05-23-report.html"
            exit_code = await main(
                ["run", "--date", "2026-05-23", "--force", "--out", str(tmp_path)]
            )
        assert exit_code == 0
        gen_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_db_calls_init_schema(self) -> None:
        with (
            patch("team_activity_report.cli.create_pool", new_callable=AsyncMock) as pool_mock,
            patch("team_activity_report.cli.init_schema", new_callable=AsyncMock) as init_mock,
        ):
            pool_mock.return_value.close = AsyncMock()
            exit_code = await main(["init-db"])
        assert exit_code == 0
        init_mock.assert_called_once()
