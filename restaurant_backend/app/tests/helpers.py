"""Shared helpers for ad-hoc backend test scripts."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def configure_output() -> None:
    """Prefer UTF-8 output when supported by the active terminal."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def print_header(title: str) -> None:
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def print_footer() -> None:
    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETE")
    print("=" * 50 + "\n")


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
