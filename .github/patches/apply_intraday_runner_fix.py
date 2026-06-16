from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "run_intraday_collector.py"

RUNNER_PATH.write_text(
    dedent(
        r'''
        from __future__ import annotations

        import argparse
        import subprocess
        import sys
        import time
        from datetime import datetime, time as clock_time, timedelta
        from zoneinfo import ZoneInfo

        KST = ZoneInfo("Asia/Seoul")


        def parse_target(value: str) -> clock_time:
            hour_text, minute_text = value.split(":", 1)
            return clock_time(int(hour_text), int(minute_text))


        def run_collection(label: str) -> int:
            print(f"::group::Collect ETF holdings at KST {label}", flush=True)
            try:
                completed = subprocess.run(
                    [sys.executable, "scripts/cloud_daily.py", "--latest-only"],
                    check=False,
                )
                return completed.returncode
            finally:
                print("::endgroup::", flush=True)


        def main() -> int:
            parser = argparse.ArgumentParser(description="Run ETF collection at exact KST intraday targets from one early GitHub runner.")
            parser.add_argument("--targets", nargs="+", default=["07:00", "08:00", "09:00", "10:00"])
            parser.add_argument("--grace-minutes", type=int, default=35)
            args = parser.parse_args()

            today = datetime.now(KST).date()
            grace = timedelta(minutes=args.grace_minutes)
            attempted = 0
            successful = 0
            failed = 0
            skipped = 0

            for target_label in args.targets:
                target_dt = datetime.combine(today, parse_target(target_label), tzinfo=KST)
                now = datetime.now(KST)

                if now < target_dt:
                    wait_seconds = int((target_dt - now).total_seconds())
                    print(f"Waiting {wait_seconds}s until KST {target_label}.", flush=True)
                    time.sleep(wait_seconds)
                elif now > target_dt + grace:
                    print(
                        f"Skipping KST {target_label}: runner started too late at {now.isoformat(timespec='seconds')}.",
                        flush=True,
                    )
                    skipped += 1
                    continue
                else:
                    print(
                        f"Running KST {target_label} immediately; current time is {now.isoformat(timespec='seconds')}.",
                        flush=True,
                    )

                attempted += 1
                status = run_collection(target_label)
                if status == 0:
                    successful += 1
                else:
                    failed += 1
                    print(f"Collection at KST {target_label} returned exit code {status}.", flush=True)

            print(
                f"Intraday collection summary: attempted={attempted}, successful={successful}, failed={failed}, skipped={skipped}",
                flush=True,
            )

            if attempted == 0:
                return 1
            if successful == 0 and failed > 0:
                return 1
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).strip()
    + "\n",
    encoding="utf-8",
)

print("Created intraday collector runner.")
