"""Collect snapshots into the local database.

Run continuously:   python -m src.collector
Run a single pass:  python -m src.collector --once
"""
import sys
import time

from .api import OpenSkyError
from .pipeline import get_aircraft
from .rules import run_rules
from .storage import save_snapshot

INTERVAL_SECONDS = 300  # 3 requests per pass -> 864 credits a day at this setting


def collect_once():
    df = get_aircraft()
    if df.empty:
        print("No aircraft found; nothing saved.")
        return
    alerts = run_rules(df)
    save_snapshot(df, alerts)
    print(f"Saved {len(df)} aircraft and {len(alerts)} alerts.")


def main():
    if "--once" in sys.argv:
        collect_once()
        return

    print(f"Collecting every {INTERVAL_SECONDS} s. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                collect_once()
            except OpenSkyError as exc:
                print(f"Skipped this round: {exc}")
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()