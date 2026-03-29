#!/usr/bin/env python3
"""Scheduler wrapper that runs daily_sync.py on a cron-like schedule.

Uses only stdlib — no external scheduling libraries needed.
Designed to run as a long-lived Docker container process.

Environment variables:
    SYNC_HOUR   — Hour (0-23) to run in the configured timezone (default: 18 = 6 PM)
    SYNC_MINUTE — Minute (0-59) to run (default: 0)
    TZ          — Timezone for scheduling (default: America/New_York)
    SYNC_ON_STARTUP — If "1", run sync immediately on container start (default: 0)

Usage:
    python scripts/daily_sync_scheduler.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

SYNC_HOUR = int(os.environ.get("SYNC_HOUR", "18"))
SYNC_MINUTE = int(os.environ.get("SYNC_MINUTE", "0"))
SYNC_ON_STARTUP = os.environ.get("SYNC_ON_STARTUP", "0") == "1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_SCRIPT = os.path.join(SCRIPT_DIR, "daily_sync.py")


def run_sync():
    """Execute daily_sync.py as a subprocess."""
    print(f"\n{'=' * 60}")
    print(f"Running daily sync at {datetime.now()}")
    print(f"{'=' * 60}\n", flush=True)

    result = subprocess.run(
        [sys.executable, SYNC_SCRIPT],
        cwd=os.path.dirname(SCRIPT_DIR),
    )

    print(f"\nSync finished with exit code {result.returncode}", flush=True)
    return result.returncode


def next_run_time() -> datetime:
    """Calculate the next scheduled run time."""
    now = datetime.now()
    target = now.replace(hour=SYNC_HOUR, minute=SYNC_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    # Skip weekends (Saturday=5, Sunday=6)
    while target.weekday() in (5, 6):
        target += timedelta(days=1)
    return target


def main():
    print(f"oobir daily-sync scheduler started at {datetime.now()}")
    print(
        f"Schedule: weekdays at {SYNC_HOUR:02d}:{SYNC_MINUTE:02d} (TZ={os.environ.get('TZ', 'system default')})"
    )
    print(f"Sync on startup: {SYNC_ON_STARTUP}")
    print(flush=True)

    if SYNC_ON_STARTUP:
        run_sync()

    while True:
        target = next_run_time()
        wait_seconds = (target - datetime.now()).total_seconds()
        print(
            f"Next sync scheduled for {target} ({wait_seconds / 3600:.1f}h from now)",
            flush=True,
        )

        # Sleep in chunks so we can handle signals gracefully
        while True:
            remaining = (target - datetime.now()).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 60))

        run_sync()


if __name__ == "__main__":
    main()
