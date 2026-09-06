# Sources

Verified for the OpenTofu deep-dive on **2026-09-06**.

Primary references:

- **OpenTofu official site** — https://opentofu.org/ (`official`)
- **OpenTofu source repository** — https://github.com/opentofu/opentofu (`repository`)
- **OpenTofu license** — https://github.com/opentofu/opentofu/blob/main/LICENSE (`repository`)
- **CLI provisioning workflow** — https://opentofu.org/docs/cli/run/ (`documentation`)
- **Providers** — https://opentofu.org/docs/language/providers/ (`documentation`)
- **Provider requirements** — https://opentofu.org/docs/language/providers/requirements/ (`documentation`)
- **Modules** — https://opentofu.org/docs/language/modules/ (`documentation`)
- **State** — https://opentofu.org/docs/language/state/ (`documentation`)
- **State storage and backends** — https://opentofu.org/docs/language/state/backends/ (`documentation`)
- **State locking** — https://opentofu.org/docs/language/state/locking/ (`documentation`)
- **State and plan encryption** — https://opentofu.org/docs/language/state/encryption/ (`documentation`)
- **Backend configuration** — https://opentofu.org/docs/language/settings/backends/configuration/ (`documentation`)
- **Dependency lock file** — https://opentofu.org/docs/language/files/dependency-lock/ (`documentation`)
- **OpenTofu v1.x compatibility promises** — https://opentofu.org/docs/language/v1-compatibility-promises/ (`documentation`)
- **Migrating from Terraform** — https://opentofu.org/docs/intro/migration/ (`documentation`)
- **Language and compatibility settings** — https://opentofu.org/docs/language/settings/ (`documentation`)

Additional upstream material reviewed while deepening the module includes current documentation for configuration file formats, state encryption key providers and methods, migration/fallback behavior, provider installation, and version-specific Terraform migration guidance.

Source selection favors current OpenTofu documentation, the canonical repository, and the upstream MPL-2.0 license. Provider behavior, registry infrastructure, Terraform compatibility, migration paths, and encryption components can evolve independently and should be rechecked before production changes.
