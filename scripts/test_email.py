#!/usr/bin/env python3
"""
Test email sender script.

Sends a test email to the SMTP server to trigger the RAG workflow.
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings


def send_test_email(
    smtp_host: str = "localhost",
    smtp_port: int = 1025,
    from_addr: str = "xyz@test.com",
    to_addr: str = "support@example.com",
    subject: str = "Database connection timeout issues",
    body: str = None,
):
    """
    Send a test email to the SMTP server.

    Args:
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        from_addr: Sender email address
        to_addr: Recipient email address
        subject: Email subject
        body: Email body (if None, uses default test content)
    """
    if body is None:
        body = """
We are experiencing severe database connection timeout issues in our production environment.

Symptoms:
- Applications timing out when connecting to database
- Connection pool exhaustion warnings
- HTTP 504 Gateway Timeout responses
- Issues occurring during peak hours (9 AM - 11 AM EST)

This is affecting multiple services and causing user complaints.

Can you please help investigate and resolve this issue urgently?

Thanks,
Operations Team
"""

    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        print(f"Sending test email to {smtp_host}:{smtp_port}...")
        print(f"From: {from_addr}")
        print(f"Subject: {subject}")
        print()

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.send_message(msg)

        print("✅ Email sent successfully!")
        print()
        print("Check the application logs to see the workflow processing:")
        print("  - Vector search results")
        print("  - LLM-generated summary")
        print("  - ServiceNow incident creation")
        print()
        print("You can also check the incident in the mock ServiceNow API:")
        print("  http://localhost:8002/api/now/table/incident")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        sys.exit(1)


def main():
    """Main function."""
    settings = get_settings()

    print("=" * 80)
    print("RAG Incident System - Test Email Sender")
    print("=" * 80)
    print()

    # Get allowed senders from config
    allowed_senders = settings.smtp_allowed_senders_list
    if allowed_senders:
        from_addr = allowed_senders[0]
        print(f"Using allowed sender: {from_addr}")
    else:
        from_addr = "xyz@test.com"
        print(f"No allowed senders configured, using default: {from_addr}")

    print()

    send_test_email(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        from_addr=from_addr,
    )


if __name__ == "__main__":
    main()
