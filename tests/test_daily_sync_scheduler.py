"""Offline unit tests for scripts/daily_sync_scheduler.py."""

import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import daily_sync_scheduler as scheduler


class Clock:
    """Minimal datetime stand-in with a movable now() for scheduler tests."""

    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


class TestRunSync(unittest.TestCase):
    def test_runs_daily_sync_script_without_checking_exit_code(self):
        with patch.object(
            scheduler.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=7),
        ) as run:
            self.assertEqual(scheduler.run_sync(), 7)

        command = run.call_args.args[0]
        self.assertEqual(command[1], scheduler.SYNC_SCRIPT)
        self.assertEqual(
            run.call_args.kwargs["cwd"], os.path.dirname(scheduler.SCRIPT_DIR)
        )
        self.assertFalse(run.call_args.kwargs["check"])


class TestNextRunTime(unittest.TestCase):
    def next_run(self, now):
        with (
            patch.object(scheduler, "SYNC_HOUR", 18),
            patch.object(scheduler, "SYNC_MINUTE", 0),
            patch.object(scheduler, "datetime", Clock(now)),
        ):
            return scheduler.next_run_time()

    def test_later_today_when_before_schedule(self):
        result = self.next_run(datetime(2024, 1, 3, 9, 0))
        self.assertEqual(result, datetime(2024, 1, 3, 18, 0))

    def test_tomorrow_when_schedule_already_passed(self):
        result = self.next_run(datetime(2024, 1, 3, 19, 0))
        self.assertEqual(result, datetime(2024, 1, 4, 18, 0))

    def test_skips_weekend_after_friday(self):
        result = self.next_run(datetime(2024, 1, 5, 19, 0))
        self.assertEqual(result, datetime(2024, 1, 8, 18, 0))

    def test_skips_weekend_when_target_is_saturday(self):
        result = self.next_run(datetime(2024, 1, 6, 9, 0))
        self.assertEqual(result, datetime(2024, 1, 8, 18, 0))


class TestMain(unittest.TestCase):
    def test_runs_on_startup_and_loop(self):
        target = datetime(2024, 1, 3, 18, 0)
        clock = Clock(datetime(2024, 1, 3, 9, 0))

        def jump_to_target(_seconds):
            clock.value = target

        stop = RuntimeError("stop scheduling")
        with (
            patch.object(scheduler, "SYNC_ON_STARTUP", True),
            patch.object(scheduler, "datetime", clock),
            patch.object(scheduler.time, "sleep", side_effect=jump_to_target) as sleep,
            patch.object(
                scheduler, "next_run_time", side_effect=[target, stop]
            ) as next_run,
            patch.object(scheduler, "run_sync") as run_sync,
            self.assertRaises(RuntimeError),
        ):
            scheduler.main()

        self.assertEqual(run_sync.call_count, 2)
        self.assertEqual(next_run.call_count, 2)
        sleep.assert_called_once_with(60.0)

    def test_does_not_run_on_startup_when_disabled(self):
        stop = RuntimeError("stop scheduling")
        with (
            patch.object(scheduler, "SYNC_ON_STARTUP", False),
            patch.object(scheduler, "next_run_time", side_effect=stop),
            patch.object(scheduler, "run_sync") as run_sync,
            self.assertRaises(RuntimeError),
        ):
            scheduler.main()
        run_sync.assert_not_called()


if __name__ == "__main__":
    unittest.main()
