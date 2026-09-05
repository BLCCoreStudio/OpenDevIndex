# Sources

Reviewed for the Helm deep-dive on **2026-09-05**. The source set prefers current upstream Helm documentation and the canonical repository. Helm behavior is tightly coupled to both its own major version and the Kubernetes versions it supports, so release-sensitive claims should be checked against the version actually in use.

## Project and architecture

- **Helm documentation** — https://helm.sh/docs/ (`official`)
- **Helm source repository** — https://github.com/helm/helm (`repository`)
- **Introduction to Helm** — https://helm.sh/docs/intro/introduction/ (`documentation`)
- **Helm 4 Overview** — https://helm.sh/docs/overview/ (`documentation`)
- **Helm Version Support Policy** — https://helm.sh/docs/topics/version_skew/ (`documentation`)

## Charts, values, and templating

- **Charts** — https://helm.sh/docs/topics/charts/ (`documentation`)
- **Chart Template Guide** — https://helm.sh/docs/chart_template_guide/ (`documentation`)
- **Built-in Objects** — https://helm.sh/docs/chart_template_guide/builtin_objects/ (`documentation`)
- **Values Files** — https://helm.sh/docs/chart_template_guide/values_files/ (`documentation`)
- **Template Functions and Pipelines** — https://helm.sh/docs/chart_template_guide/functions_and_pipelines/ (`documentation`)
- **Named Templates** — https://helm.sh/docs/chart_template_guide/named_templates/ (`documentation`)
- **Subcharts and Global Values** — https://helm.sh/docs/chart_template_guide/subcharts_and_globals/ (`documentation`)
- **Chart Dependencies** — https://helm.sh/docs/topics/charts/#chart-dependencies (`documentation`)
- **Library Charts** — https://helm.sh/docs/topics/library_charts/ (`documentation`)

## Release lifecycle and testing

- **Chart Hooks** — https://helm.sh/docs/topics/charts_hooks/ (`documentation`)
- **Chart Tests** — https://helm.sh/docs/topics/chart_tests/ (`documentation`)
- **helm install** — https://helm.sh/docs/helm/helm_install/ (`documentation`)
- **helm upgrade** — https://helm.sh/docs/helm/helm_upgrade/ (`documentation`)
- **helm rollback** — https://helm.sh/docs/helm/helm_rollback/ (`documentation`)
- **helm uninstall** — https://helm.sh/docs/helm/helm_uninstall/ (`documentation`)
- **helm history** — https://helm.sh/docs/helm/helm_history/ (`documentation`)
- **helm get** — https://helm.sh/docs/helm/helm_get/ (`documentation`)
- **helm template** — https://helm.sh/docs/helm/helm_template/ (`documentation`)
- **helm lint** — https://helm.sh/docs/helm/helm_lint/ (`documentation`)

## Distribution and supply chain

- **Use OCI-based registries** — https://helm.sh/docs/topics/registries/ (`documentation`)
- **Chart Repository Guide** — https://helm.sh/docs/topics/chart_repository/ (`documentation`)
- **Helm Provenance and Integrity** — https://helm.sh/docs/topics/provenance/ (`documentation`)
- **Artifact Hub** — https://artifacthub.io/ (`official`)

## Security, permissions, and extension

- **Role-based Access Control** — https://helm.sh/docs/topics/rbac/ (`documentation`)
- **Advanced Helm Techniques** — https://helm.sh/docs/topics/advanced/ (`documentation`)
- **Permissions management for SQL storage backend** — https://helm.sh/docs/topics/permissions_sql_storage_backend/ (`documentation`)
- **Helm Plugins Guide** — https://helm.sh/docs/topics/plugins/ (`documentation`)
- **Helm Go SDK** — https://helm.sh/docs/topics/advanced/#go-sdk (`documentation`)

## Kubernetes boundary

- **Kubernetes API concepts** — https://kubernetes.io/docs/reference/using-api/api-concepts/ (`documentation`)
- **Kubernetes RBAC** — https://kubernetes.io/docs/reference/access-authn-authz/rbac/ (`documentation`)
- **Kubernetes Custom Resources** — https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/ (`documentation`)

The durable concepts in this module are charts, values, rendering, releases, Kubernetes API interaction, and release history. Exact flags, plugin behavior, chart API versions, apply strategy, supported Kubernetes skew, and major-version migration details are version-sensitive and should be revalidated before production changes.