# Sources

Reviewed for the Grafana deep-dive on **2026-09-06**.

OpenDevIndex prefers upstream Grafana documentation and the canonical source repository. Grafana documentation spans OSS, Enterprise, and Grafana Cloud, so edition markers must be checked before treating a feature as available in the open-source build.

## Project and platform

- **Grafana documentation** — https://grafana.com/docs/grafana/latest/ (`official`)
- **Grafana source repository** — https://github.com/grafana/grafana (`repository`)
- **Grafana AGPL-3.0 license** — https://github.com/grafana/grafana/blob/main/LICENSE (`repository`)

## Data sources and querying

- **Data sources** — https://grafana.com/docs/grafana/latest/datasources/ (`documentation`)
- **Prometheus data source** — https://grafana.com/docs/grafana/latest/datasources/prometheus/ (`documentation`)
- **Explore** — https://grafana.com/docs/grafana/latest/explore/ (`documentation`)

## Dashboards and visualization

- **Dashboards** — https://grafana.com/docs/grafana/latest/dashboards/ (`documentation`)
- **Dashboard variables** — https://grafana.com/docs/grafana/latest/dashboards/variables/ (`documentation`)
- **Transform data** — https://grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/transform-data/ (`documentation`)
- **Panels and visualizations** — https://grafana.com/docs/grafana/latest/panels-visualizations/ (`documentation`)

## Alerting

- **Grafana Alerting fundamentals** — https://grafana.com/docs/grafana/latest/alerting/fundamentals/ (`documentation`)
- **Configure notifications** — https://grafana.com/docs/grafana/latest/alerting/configure-notifications/ (`documentation`)
- **Contact points** — https://grafana.com/docs/grafana/latest/alerting/configure-notifications/manage-contact-points/ (`documentation`)

## Administration and as-code workflows

- **Administration** — https://grafana.com/docs/grafana/latest/administration/ (`documentation`)
- **Provision Grafana** — https://grafana.com/docs/grafana/latest/administration/provisioning/ (`documentation`)
- **Authentication** — https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/ (`documentation`)
- **Dashboard permissions** — https://grafana.com/docs/grafana/latest/administration/user-management/manage-dashboard-permissions/ (`documentation`)
- **Plugin management** — https://grafana.com/docs/grafana/latest/administration/plugin-management/ (`documentation`)

## Deployment and recovery

- **Install Grafana** — https://grafana.com/docs/grafana/latest/setup-grafana/installation/ (`documentation`)
- **Set up Grafana for high availability** — https://grafana.com/docs/grafana/latest/setup-grafana/set-up-for-high-availability/ (`documentation`)
- **Back up Grafana** — https://grafana.com/docs/grafana/latest/administration/back-up-grafana/ (`documentation`)

## Editorial notes

- Grafana is treated primarily as a query/visualization/alerting control plane over external telemetry systems, not as the owner of the underlying metrics, logs, or traces.
- Grafana's own relational database stores Grafana application/configuration state and is distinct from configured data sources.
- Prometheus query semantics remain PromQL semantics even when the query is authored through Grafana.
- Enterprise/Cloud-only RBAC and other edition-specific functionality is not presented as universally available in Grafana OSS.
- Exact HA/session behavior, supported database versions, plugin APIs, and scale recommendations are version-sensitive and should be checked against the installed release.
