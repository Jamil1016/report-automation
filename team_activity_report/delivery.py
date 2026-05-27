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
        os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS")
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
