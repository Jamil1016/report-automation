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
