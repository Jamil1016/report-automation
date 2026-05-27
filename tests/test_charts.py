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
