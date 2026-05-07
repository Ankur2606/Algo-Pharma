"""
End-to-end smoke test for AlgoPharma backend.

Covers:
- User signup/login
- Project creation and keyword add
- Forum source add (approve-forum)
- Results and signals endpoint checks
- Optional demo pipeline trigger for signal generation

Usage:
  python scripts/e2e_smoke_test.py
  python scripts/e2e_smoke_test.py --base-url http://127.0.0.1:8000 --run-demo
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import string
import sys
import time
from typing import Any

import httpx


def _rand_suffix(n: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(n))


def _ok(name: str, detail: str = "") -> None:
    msg = f"[PASS] {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)


def _fail(name: str, detail: str) -> None:
    print(f"[FAIL] {name} - {detail}")
    raise SystemExit(1)


def _safe_json(resp: httpx.Response) -> Any:
    content_type = (resp.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            return resp.json()
        except Exception:
            return {"_parse_error": "invalid json", "text": resp.text[:1000]}
    return {"text": resp.text[:1000]}


def _log_call(
    log_file: Path,
    *,
    method: str,
    path: str,
    kwargs: dict[str, Any],
    response: httpx.Response | None,
    expected_codes: tuple[int, ...],
    error: str | None = None,
) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "request": {
            "method": method,
            "path": path,
            "headers": kwargs.get("headers", {}),
            "params": kwargs.get("params"),
            "json": kwargs.get("json"),
            "data": kwargs.get("data"),
            "timeout": kwargs.get("timeout"),
        },
        "expected_status_codes": list(expected_codes),
        "response": None,
        "error": error,
    }
    if response is not None:
        record["response"] = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": _safe_json(response),
        }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")


def _pretty(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=True, indent=2)


def _log_call_pretty(
    pretty_log_file: Path,
    *,
    method: str,
    path: str,
    kwargs: dict[str, Any],
    response: httpx.Response | None,
    expected_codes: tuple[int, ...],
    error: str | None = None,
) -> None:
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    request_headers = kwargs.get("headers", {})
    request_params = kwargs.get("params")
    request_json = kwargs.get("json")
    request_data = kwargs.get("data")
    request_timeout = kwargs.get("timeout")

    if response is None:
        response_obj: Any = None
    else:
        response_obj = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": _safe_json(response),
        }

    block = [
        "{",
        f'  "timestamp": "{timestamp_utc}",',
        '  "request": {',
        f'    "method": "{method}",',
        f'    "path": "{path}",',
        f'    "headers": {_pretty(request_headers)},',
        f'    "params": {_pretty(request_params)},',
        f'    "json": {_pretty(request_json)},',
        f'    "data": {_pretty(request_data)},',
        f'    "timeout": {_pretty(request_timeout)}',
        "  },",
        f'  "expected": {_pretty(list(expected_codes))},',
        f'  "response": {_pretty(response_obj)},',
        f'  "error": {_pretty(error)}',
        "}",
        "-" * 80,
        "",
    ]

    with pretty_log_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(block))


def _req(
    client: httpx.Client,
    log_file: Path,
    pretty_log_file: Path,
    method: str,
    path: str,
    *,
    expected: int | tuple[int, ...],
    **kwargs: Any,
) -> httpx.Response:
    if isinstance(expected, int):
        expected_codes = (expected,)
    else:
        expected_codes = expected

    resp = None
    try:
        resp = client.request(method, path, **kwargs)
    except Exception as exc:
        _log_call(
            log_file,
            method=method,
            path=path,
            kwargs=kwargs,
            response=None,
            expected_codes=expected_codes,
            error=repr(exc),
        )
        _log_call_pretty(
            pretty_log_file,
            method=method,
            path=path,
            kwargs=kwargs,
            response=None,
            expected_codes=expected_codes,
            error=repr(exc),
        )
        raise

    _log_call(
        log_file,
        method=method,
        path=path,
        kwargs=kwargs,
        response=resp,
        expected_codes=expected_codes,
    )
    _log_call_pretty(
        pretty_log_file,
        method=method,
        path=path,
        kwargs=kwargs,
        response=resp,
        expected_codes=expected_codes,
    )
    if resp.status_code not in expected_codes:
        snippet = resp.text[:400].replace("\n", " ")
        _fail(
            f"{method} {path}",
            f"expected {expected_codes}, got {resp.status_code}, body={snippet}",
        )
    return resp


def main() -> None:
    parser = argparse.ArgumentParser(description="AlgoPharma E2E smoke tester")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="FastAPI base URL")
    parser.add_argument(
        "--run-demo",
        action="store_true",
        help="Trigger project-specific crawl/signal pipeline",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=20,
        help="Max seconds to poll results when --run-demo is used",
    )
    parser.add_argument(
        "--log-dir",
        default="logs/e2e",
        help="Directory for request/response JSONL logs",
    )
    parser.add_argument(
        "--demo-timeout-seconds",
        type=int,
        default=900,
        help="Timeout for trigger request",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=2,
        help="Polling interval for results endpoint",
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=10,
        help="Print progress heartbeat every N seconds while polling",
    )
    parser.add_argument(
        "--max-same-status",
        type=int,
        default=40,
        help="Stop polling early if same status/count repeats this many times",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    suffix = _rand_suffix()
    email = f"e2e_{suffix}@example.com"
    username = f"e2e_{suffix}"
    password = "E2eTest@123"
    project_name = f"E2E Project {suffix}"
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"e2e_run_{run_id}_{suffix}.jsonl"
    pretty_log_file = log_dir / f"e2e_run_{run_id}_{suffix}.log"

    print(f"Base URL: {base_url}")
    print(f"Log file: {log_file}")
    print(f"Readable log: {pretty_log_file}")
    print("Starting end-to-end smoke test...")

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        # 0) Health check
        resp = _req(client, log_file, pretty_log_file, "GET", "/", expected=200)
        _ok("Service reachable", f"status={resp.status_code}")

        # 1) Register
        reg = _req(
            client,
            log_file,
            pretty_log_file,
            "POST",
            "/api/auth/register",
            expected=(200, 201),
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": "user",
            },
        ).json()
        token = reg.get("access_token")
        if not token:
            _fail("Register", "No access_token in response")
        _ok("Register user", f"user={username}")

        headers = {"Authorization": f"Bearer {token}"}

        # 2) Me endpoint
        me = _req(
            client, log_file, pretty_log_file, "GET", "/api/auth/me", expected=200, headers=headers
        ).json()
        user_id = me.get("id")
        if not user_id:
            _fail("Get current user", "Missing id in /api/auth/me response")
        _ok("Auth me", f"user_id={user_id}, role={me.get('role')}")

        # 3) Create project
        project = _req(
            client,
            log_file,
            pretty_log_file,
            "POST",
            "/api/projects",
            expected=200,
            headers=headers,
            json={"name": project_name, "description": "E2E smoke run"},
        ).json()
        project_id = project.get("id")
        if not project_id:
            _fail("Create project", "Missing id in response")
        _ok("Create project", f"project_id={project_id}")

        # 4) Add keyword
        kw = _req(
            client,
            log_file,
            pretty_log_file,
            "POST",
            f"/api/projects/{project_id}/keywords",
            expected=200,
            headers=headers,
            json={"term": "dolo 650", "synonyms": ["paracetamol"]},
        ).json()
        _ok("Add keyword", f"keyword_id={kw.get('id')}")

        # 5) Verify results/list endpoint
        projects = _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            "/api/results/list",
            expected=200,
            headers=headers,
        ).json()
        if not any(p.get("id") == project_id for p in projects):
            _fail("List projects", f"Created project {project_id} not returned")
        _ok("Results list", f"projects={len(projects)}")

        # 6) Forum source add endpoint (currently not admin protected)
        forum_url = f"https://example.com/forum/{suffix}"
        approve_resp = _req(
            client,
            log_file,
            pretty_log_file,
            "POST",
            "/api/agentic/approve-forum",
            expected=200,
            json={
                "url": forum_url,
                "config": {"forum_type": "custom", "selectors": {"thread": ".thread"}},
            },
        ).json()
        if "source_id" not in approve_resp:
            _fail("Approve forum", "No source_id in response")
        _ok("Create/update forum source", f"source_id={approve_resp['source_id']}")

        # 7) Optional pipeline trigger for the specific project
        if args.run_demo:
            _req(
                client,
                log_file,
                pretty_log_file,
                "POST",
                f"/api/crawl/trigger/{project_id}",
                expected=200,
                timeout=args.demo_timeout_seconds,
            )
            _ok("Triggered project crawl pipeline", f"project_id={project_id}")
        else:
            _ok("Skipped pipeline trigger", "pass --run-demo to execute signal generation")

        # 8) Poll results endpoint for created project
        started = time.time()
        last_status = None
        last_heartbeat = started
        same_status_count = 0
        previous_signature = None
        while time.time() - started <= args.poll_seconds:
            result = _req(
                client,
                log_file,
                pretty_log_file,
                "GET",
                f"/api/results/{project_id}",
                expected=200,
                headers=headers,
            ).json()
            last_status = result.get("status")
            counts = result.get("counts", {})
            signature = (
                last_status,
                counts.get("signals", 0),
                counts.get("processed_posts", 0),
                counts.get("crawl_logs", 0),
            )
            if signature == previous_signature:
                same_status_count += 1
            else:
                same_status_count = 0
                previous_signature = signature

            elapsed = int(time.time() - started)
            if time.time() - last_heartbeat >= args.heartbeat_seconds:
                print(
                    f"[WAIT] elapsed={elapsed}s status={last_status} "
                    f"signals={counts.get('signals', 0)} "
                    f"processed={counts.get('processed_posts', 0)} "
                    f"crawl_logs={counts.get('crawl_logs', 0)}"
                )
                last_heartbeat = time.time()

            if last_status in {"analysing", "complete"}:
                break

            if same_status_count >= args.max_same_status:
                print(
                    "[WARN] No progress observed for a long time; stopping poll early. "
                    "Check pipeline logs/server terminal."
                )
                break
            time.sleep(args.poll_interval_seconds)
        _ok("Project results endpoint", f"status={last_status}")

        # 9) Signals list endpoint for created project
        sig_list = _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/signals?days=365",
            expected=200,
            headers=headers,
        ).json()
        _ok("Signals list endpoint", f"signals={len(sig_list)}")

        # 10) Drilldown if at least one signal exists
        if sig_list:
            first_signal_id = sig_list[0]["id"]
            drill = _req(
                client,
                log_file,
                pretty_log_file,
                "GET",
                f"/api/signals/{first_signal_id}/drilldown",
                expected=200,
                headers=headers,
            ).json()
            _ok(
                "Signal drilldown endpoint",
                f"signal_id={first_signal_id}, posts={len(drill.get('supporting_posts', []))}",
            )
        else:
            _ok("Signal drilldown endpoint", "skipped because no signals for this project")

        # 11) CSV export endpoint (exists; auth rule currently permissive in code)
        csv_resp = _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            "/api/export/pvpi-csv",
            expected=200,
            headers=headers,
        )
        content_type = csv_resp.headers.get("content-type", "")
        _ok("PvPI export endpoint", content_type)

        # 12) Analytics endpoints
        _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/analytics/ae-trend?days=30",
            expected=200,
            headers=headers,
        )
        _ok("Analytics ae-trend endpoint")

        _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/analytics/sentiment",
            expected=200,
            headers=headers,
        )
        _ok("Analytics sentiment endpoint")

        _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/analytics/top-symptoms?limit=10",
            expected=200,
            headers=headers,
        )
        _ok("Analytics top-symptoms endpoint")

        _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/analytics/prr-chart",
            expected=200,
            headers=headers,
        )
        _ok("Analytics prr-chart endpoint")

        _req(
            client,
            log_file,
            pretty_log_file,
            "GET",
            f"/api/projects/{project_id}/analytics/platform-breakdown",
            expected=200,
            headers=headers,
        )
        _ok("Analytics platform-breakdown endpoint")

    print("All smoke checks completed.")
    print(f"JSONL log: {log_file}")
    print(f"Readable log: {pretty_log_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
