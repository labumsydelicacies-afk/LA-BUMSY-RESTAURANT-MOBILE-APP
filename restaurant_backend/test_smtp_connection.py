#!/usr/bin/env python3
"""Standalone SMTP connection test for production debugging."""

import os
import sys
import smtplib
from pathlib import Path

# Load from .env if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✓ Loaded .env from {env_path}")
    else:
        print(f"✗ No .env file found at {env_path}")
except ImportError:
    print("python-dotenv not installed, using system environment only")

# Get credentials
smtp_email = os.getenv("SMTP_EMAIL")
smtp_password = os.getenv("SMTP_PASSWORD")
smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "465"))

print("\n=== SMTP CONFIGURATION ===")
print(f"SMTP_EMAIL: {repr(smtp_email)}")
print(f"SMTP_PASSWORD length: {len(smtp_password) if smtp_password else 0}")
print(f"SMTP_HOST: {smtp_host}")
print(f"SMTP_PORT: {smtp_port}")

# Validate
if not smtp_email:
    print("\n✗ SMTP_EMAIL is not set!")
    sys.exit(1)
if not smtp_password:
    print("\n✗ SMTP_PASSWORD is not set!")
    sys.exit(1)

# Test connection
print("\n=== TESTING SMTP CONNECTION ===")
try:
    print(f"Connecting to {smtp_host}:{smtp_port}...")
    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
    print("✓ TCP connection successful")

    print(f"Authenticating as {smtp_email}...")
    server.login(smtp_email, smtp_password)
    print("✓ Authentication successful")

    server.quit()
    print("\n✓✓✓ SMTP TEST PASSED ✓✓✓")
    sys.exit(0)

except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ AUTHENTICATION FAILED: {e}")
    print("Possible causes:")
    print("  - Wrong password or app password")
    print("  - Gmail account security settings")
    print("  - IP/datacenter blocking")
    sys.exit(1)

except smtplib.SMTPException as e:
    print(f"\n✗ SMTP ERROR: {e}")
    sys.exit(1)

except Exception as e:
    print(f"\n✗ CONNECTION ERROR: {e}")
    sys.exit(1)
