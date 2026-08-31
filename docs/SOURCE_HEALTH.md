# Source health

OpenDevIndex periodically checks the canonical links attached to validated catalog records. The goal is to detect stale or permanently missing references without making normal pull-request validation depend on the availability of third-party websites.

## What is checked

The checker deduplicates and checks:

- module homepages;
- source repositories;
- official, documentation, standard, advisory, research, and repository references.

## Network safety

Source-health requests are made only from trusted workflow executions. Pull requests receive static URL validation but do not trigger arbitrary outbound health requests.

The checker:

- requires HTTPS;
- rejects embedded credentials;
- rejects non-standard HTTPS ports;
- rejects localhost, private, link-local, loopback, reserved, and other non-public IP destinations;
- resolves hostnames before requesting them;
- revalidates every redirect target before following it;
- uses bounded timeouts, retries, and concurrency.

## Result classes

- **healthy** — successful 2xx/3xx response;
- **restricted** — the destination is reachable but blocks or limits automated access, such as 401, 403, 429, or similar responses;
- **transient** — DNS, TLS, timeout, or 5xx failure that may recover later;
- **broken** — a permanent missing response such as 404/410, or a destination that violates the public-HTTPS safety policy.

The default workflow fails only on **broken** results. Restricted and transient responses remain visible in the report without creating false permanent-failure signals.

## Run manually

```bash
python -m pip install -r requirements-ci.txt
python scripts/check_source_health.py \
  --catalog-dir catalog \
  --report-json source-health.json \
  --report-md source-health.md \
  --fail-on broken
```

The scheduled GitHub Actions workflow publishes the Markdown summary to the job summary and uploads both report formats as workflow artifacts.
