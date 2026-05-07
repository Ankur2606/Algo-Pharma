"""
Poll only the project results endpoint for long-running pipeline monitoring.

Usage:
  uv run python scripts/poll_results.py --project-id 9 --token "<JWT>"
  uv run python scripts/poll_results.py --project-id 9 --token "<JWT>" --max-seconds 3600 --interval 10
"""

from __future__ import annotations

import argparse
from datetime import datetime
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll /api/results/{project_id}")
    parser.add_argument("--project-id", type=int, required=True, help="Project ID to monitor")
    parser.add_argument("--token", required=True, help="Bearer JWT token")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval in seconds")
    parser.add_argument("--max-seconds", type=int, default=1800, help="Maximum total polling time")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {args.token}"}
    start = time.time()

    print(f"Monitoring project_id={args.project_id} at {base_url}")
    print(f"interval={args.interval}s max_seconds={args.max_seconds}s")

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        while True:
            elapsed = int(time.time() - start)
            if elapsed > args.max_seconds:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] TIMEOUT after {elapsed}s")
                break

            try:
                resp = client.get(f"/api/results/{args.project_id}", headers=headers)
                if resp.status_code != 200:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                    time.sleep(args.interval)
                    continue

                data = resp.json()
                counts = data.get("counts", {})
                status = data.get("status", "unknown")
                processed = counts.get("processed_posts", 0)
                signals = counts.get("signals", 0)
                crawl_logs = counts.get("crawl_logs", 0)

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"elapsed={elapsed}s status={status} "
                    f"processed={processed} signals={signals} crawl_logs={crawl_logs}"
                )

                if status == "complete":
                    print("Project reached COMPLETE state.")
                    break

            except Exception as exc:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {exc!r}")

            time.sleep(args.interval)


if __name__ == "__main__":
    main()
