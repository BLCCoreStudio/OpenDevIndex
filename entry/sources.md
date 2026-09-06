# Sources

Reviewed for the Argo CD deep-dive on **2026-09-06**.

OpenDevIndex prefers upstream project documentation, canonical repositories, standards, and original security/architecture material. Version-sensitive operational defaults should be checked against the documentation for the exact Argo CD release in use.

## Project and architecture

- **Argo CD official documentation** — https://argo-cd.readthedocs.io/en/stable/ (`official`)
- **Argo CD source repository** — https://github.com/argoproj/argo-cd (`repository`)
- **Argo CD Apache-2.0 license** — https://github.com/argoproj/argo-cd/blob/master/LICENSE (`repository`)
- **Architectural Overview** — https://argo-cd.readthedocs.io/en/stable/operator-manual/architecture/ (`documentation`)
- **Component Architecture** — https://argo-cd.readthedocs.io/en/stable/developer-guide/architecture/components/ (`documentation`)

## Application and reconciliation model

- **Application Specification Reference** — https://argo-cd.readthedocs.io/en/stable/user-guide/application-specification/ (`documentation`)
- **Automated Sync Policy** — https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/ (`documentation`)
- **Sync Options** — https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/ (`documentation`)
- **Sync Phases and Waves** — https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/ (`documentation`)
- **Diffing Customization** — https://argo-cd.readthedocs.io/en/stable/user-guide/diffing/ (`documentation`)
- **Resource Tracking** — https://argo-cd.readthedocs.io/en/stable/user-guide/resource_tracking/ (`documentation`)
- **Resource Health** — https://argo-cd.readthedocs.io/en/stable/operator-manual/health/ (`documentation`)
- **Tracking and Deployment Strategies** — https://argo-cd.readthedocs.io/en/stable/user-guide/tracking_strategies/ (`documentation`)

## Projects, tenancy, and security

- **Projects** — https://argo-cd.readthedocs.io/en/stable/user-guide/projects/ (`documentation`)
- **RBAC Configuration** — https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/ (`documentation`)
- **Security Overview** — https://argo-cd.readthedocs.io/en/stable/operator-manual/security/ (`documentation`)
- **Declarative Setup** — https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/ (`documentation`)
- **Application Sync using Impersonation** — https://argo-cd.readthedocs.io/en/stable/operator-manual/app-sync-using-impersonation/ (`documentation`)

## ApplicationSet and fleet management

- **Generating Applications with ApplicationSet** — https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/ (`documentation`)
- **ApplicationSet Generators** — https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/ (`documentation`)
- **ApplicationSet Specification** — https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/applicationset-specification/ (`documentation`)
- **Pull Request Generator** — https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Pull-Request/ (`documentation`)

## Helm and manifest generation

- **Argo CD Helm Integration** — https://argo-cd.readthedocs.io/en/stable/user-guide/helm/ (`documentation`)

## Operations and recovery

- **Installation** — https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/ (`documentation`)
- **Argo CD Core** — https://argo-cd.readthedocs.io/en/stable/operator-manual/core/ (`documentation`)
- **Disaster Recovery** — https://argo-cd.readthedocs.io/en/stable/operator-manual/disaster_recovery/ (`documentation`)
- **Argo CD FAQ** — https://argo-cd.readthedocs.io/en/stable/faq/ (`documentation`)

## Editorial notes

- `stable` documentation URLs are preferred for evergreen concepts; exact flags and defaults still need installed-version verification.
- Helm is treated as a manifest renderer inside Argo CD's reconciliation model; direct Helm release semantics are documented separately in the `cloud/helm` module.
- Kubernetes API behavior remains authoritative for admission, defaulting, field ownership, controllers, RBAC, and workload health below Argo CD.
- The repository source is authoritative for the Apache-2.0 license and implementation details when documentation is ambiguous.
