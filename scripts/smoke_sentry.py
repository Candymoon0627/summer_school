from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.sentry import capture_sentry_test_event, init_sentry, is_sentry_configured


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Sentry smoke-test event.")
    parser.add_argument("--source", default="host-script", help="Label to include in the event.")
    args = parser.parse_args()

    if not is_sentry_configured():
        raise SystemExit("SENTRY_DSN is not configured.")

    init_sentry()
    event_id = capture_sentry_test_event(source=args.source)
    if not event_id:
        raise SystemExit("Sentry event was not accepted by the local SDK.")

    print(f"Sentry test event sent: {event_id}")


if __name__ == "__main__":
    main()
