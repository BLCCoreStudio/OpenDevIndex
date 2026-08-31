#!/usr/bin/env python3
"""Check OpenDevIndex source URLs with conservative, SSRF-aware network rules."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import ipaddress
import json
import socket
import ssl
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from catalog_utils import collect_entries, discover_catalogs

USER_AGENT = "OpenDevIndex-SourceHealth/1.0 (+https://github.com/BLCCoreStudio/OpenDevIndex)"
RESTRICTED_CODES = {401, 403, 407, 423, 425, 429, 451}
BROKEN_CODES = {404, 410}


def static_public_https_url(url: str) -> tuple[bool, str]:
    """Reject obviously unsafe or unsupported URLs without network access."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as exc:
        return False, f"invalid URL: {exc}"

    if parsed.scheme != "https" or not parsed.hostname:
        return False, "URL must use HTTPS and include a hostname"
    if parsed.username or parsed.password:
        return False, "embedded credentials are not allowed"
    if port not in (None, 443):
        return False, "non-standard HTTPS ports are not checked"

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return False, "local hostnames are not allowed"

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True, ""
    if not address.is_global:
        return False, "non-public IP addresses are not allowed"
    return True, ""


def resolve_public_host(url: str) -> tuple[bool, str]:
    ok, reason = static_public_https_url(url)
    if not ok:
        return ok, reason

    parsed = urlparse(url)
    hostname = parsed.hostname
    assert hostname is not None
    try:
        infos = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        return False, f"DNS resolution failed: {exc}"

    addresses: set[str] = set()
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            addresses.add(str(sockaddr[0]))

    if not addresses:
        return False, "DNS returned no addresses"

    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return False, f"unparseable resolved address: {raw}"
        if not address.is_global:
            return False, f"hostname resolves to non-public address: {raw}"
    return True, ""


class SafeRedirectHandler(HTTPRedirectHandler):
    """Refuse redirects that leave public HTTPS destinations."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        absolute = urljoin(req.full_url, newurl)
        ok, reason = resolve_public_host(absolute)
        if not ok:
            raise URLError(f"unsafe redirect blocked: {reason}")
        return super().redirect_request(req, fp, code, msg, headers, absolute)


def classify_http_code(code: int) -> str:
    if 200 <= code < 400:
        return "healthy"
    if code in BROKEN_CODES:
        return "broken"
    if code in RESTRICTED_CODES:
        return "restricted"
    if 400 <= code < 500:
        return "restricted"
    return "transient"


def check_once(url: str, timeout: float) -> dict:
    ok, reason = resolve_public_host(url)
    if not ok:
        classification = "transient" if reason.startswith("DNS resolution failed") else "broken"
        return {
            "url": url,
            "classification": classification,
            "http_status": None,
            "final_url": None,
            "detail": reason,
        }

    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,text/plain,*/*;q=0.8",
            "Range": "bytes=0-1023",
        },
    )
    opener = build_opener(SafeRedirectHandler())

    try:
        with opener.open(request, timeout=timeout) as response:
            response.read(1)
            final_url = response.geturl()
            code = int(response.getcode() or 200)
            return {
                "url": url,
                "classification": classify_http_code(code),
                "http_status": code,
                "final_url": final_url,
                "detail": "reachable",
            }
    except HTTPError as exc:
        return {
            "url": url,
            "classification": classify_http_code(int(exc.code)),
            "http_status": int(exc.code),
            "final_url": getattr(exc, "url", None),
            "detail": str(exc.reason or exc),
        }
    except (URLError, TimeoutError, socket.timeout, ssl.SSLError, OSError) as exc:
        return {
            "url": url,
            "classification": "transient",
            "http_status": None,
            "final_url": None,
            "detail": str(exc),
        }


def check_url(url: str, timeout: float, retries: int) -> dict:
    result = check_once(url, timeout)
    for attempt in range(retries):
        if result["classification"] != "transient":
            break
        time.sleep(min(2.0, 0.5 * (2**attempt)))
        result = check_once(url, timeout)
    return result


def collect_urls(entries: list[dict]) -> dict[str, set[str]]:
    contexts: dict[str, set[str]] = {}
    for entry in entries:
        ref = entry["module_ref"]
        for field in ("homepage", "repository"):
            url = entry.get(field)
            if isinstance(url, str) and url:
                contexts.setdefault(url, set()).add(f"{ref}:{field}")
        for source in entry.get("sources", []):
            url = source.get("url") if isinstance(source, dict) else None
            if isinstance(url, str) and url:
                contexts.setdefault(url, set()).add(f"{ref}:source")
    return contexts


def render_markdown(results: list[dict], checked_at: str) -> str:
    counts = Counter(result["classification"] for result in results)
    lines = [
        "# OpenDevIndex Source Health",
        "",
        f"Checked at **{checked_at}**.",
        "",
        f"- Healthy: **{counts.get('healthy', 0)}**",
        f"- Restricted/anti-bot: **{counts.get('restricted', 0)}**",
        f"- Transient: **{counts.get('transient', 0)}**",
        f"- Broken: **{counts.get('broken', 0)}**",
        "",
    ]

    notable = [result for result in results if result["classification"] != "healthy"]
    if not notable:
        lines.append("All checked URLs were reachable.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "## Non-healthy results",
            "",
            "| Classification | HTTP | URL | Modules | Detail |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for result in notable:
        status = result["http_status"] if result["http_status"] is not None else "—"
        contexts = ", ".join(result.get("contexts", []))
        detail = str(result.get("detail", "")).replace("|", "\\|").replace("\n", " ")
        url = result["url"].replace("|", "%7C")
        lines.append(
            f"| {result['classification']} | {status} | {url} | {contexts} | {detail} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_checks(catalog_dir: Path, timeout: float, retries: int, workers: int) -> dict:
    entries, catalogs = collect_entries(discover_catalogs(catalog_dir))
    contexts = collect_urls(entries)
    urls = sorted(contexts)

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(check_url, url, timeout, retries): url
            for url in urls
        }
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # defensive: one URL must not abort the report
                result = {
                    "url": url,
                    "classification": "transient",
                    "http_status": None,
                    "final_url": None,
                    "detail": f"checker error: {exc}",
                }
            result["contexts"] = sorted(contexts[url])
            results.append(result)

    results.sort(key=lambda item: (item["classification"], item["url"]))
    checked_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    counts = Counter(result["classification"] for result in results)
    return {
        "schema_version": 1,
        "checked_at": checked_at,
        "catalogs": [item["path"] for item in catalogs],
        "url_count": len(results),
        "summary": dict(sorted(counts.items())),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--report-json", default="source-health.json")
    parser.add_argument("--report-md", default="source-health.md")
    parser.add_argument("--fail-on", choices=("never", "broken", "unhealthy"), default="broken")
    args = parser.parse_args()

    if args.timeout <= 0 or args.retries < 0 or args.workers <= 0:
        parser.error("timeout/workers must be positive and retries must be non-negative")

    try:
        report = run_checks(Path(args.catalog_dir), args.timeout, args.retries, args.workers)
    except ValueError as exc:
        print(f"OpenDevIndex source health failed before network checks: {exc}", file=sys.stderr)
        return 2

    json_path = Path(args.report_json)
    md_path = Path(args.report_md)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report["results"], report["checked_at"]), encoding="utf-8")

    summary = Counter(result["classification"] for result in report["results"])
    print(
        "OpenDevIndex source health: "
        f"{summary.get('healthy', 0)} healthy, "
        f"{summary.get('restricted', 0)} restricted, "
        f"{summary.get('transient', 0)} transient, "
        f"{summary.get('broken', 0)} broken"
    )

    if args.fail_on == "never":
        return 0
    if args.fail_on == "broken" and summary.get("broken", 0):
        return 1
    if args.fail_on == "unhealthy" and (
        summary.get("broken", 0) or summary.get("transient", 0)
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
