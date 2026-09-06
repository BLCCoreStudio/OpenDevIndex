# Sources

Verified for the Terraform deep-dive on **2026-09-06**.

Primary references:

- **Terraform documentation** — https://developer.hashicorp.com/terraform (`documentation`)
- **Terraform source repository** — https://github.com/hashicorp/terraform (`repository`)
- **Terraform license** — https://github.com/hashicorp/terraform/blob/main/LICENSE (`repository`)
- **Terraform state** — https://developer.hashicorp.com/terraform/language/state (`documentation`)
- **State storage and locking** — https://developer.hashicorp.com/terraform/language/state/backends (`documentation`)
- **State locking** — https://developer.hashicorp.com/terraform/language/state/locking (`documentation`)
- **Dependency graph internals** — https://developer.hashicorp.com/terraform/internals/graph (`documentation`)
- **How Terraform works with plugins** — https://developer.hashicorp.com/terraform/plugin/how-terraform-works (`documentation`)
- **Terraform Plugin Protocol** — https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol (`documentation`)
- **Provider configuration** — https://developer.hashicorp.com/terraform/language/block/provider (`documentation`)
- **Modules overview** — https://developer.hashicorp.com/terraform/language/modules (`documentation`)
- **terraform plan** — https://developer.hashicorp.com/terraform/cli/commands/plan (`documentation`)
- **terraform apply** — https://developer.hashicorp.com/terraform/cli/commands/apply (`documentation`)
- **Dependency lock file** — https://developer.hashicorp.com/terraform/language/files/dependency-lock (`documentation`)
- **Manage sensitive data** — https://developer.hashicorp.com/terraform/language/manage-sensitive-data (`documentation`)
- **Import resources** — https://developer.hashicorp.com/terraform/language/import (`documentation`)
- **Module refactoring and moved blocks** — https://developer.hashicorp.com/terraform/language/modules/develop/refactoring (`documentation`)
- **Terraform tests** — https://developer.hashicorp.com/terraform/language/tests (`documentation`)

Additional upstream references reviewed while deepening the module:

- **Meta-arguments** — https://developer.hashicorp.com/terraform/language/meta-arguments
- **`depends_on`** — https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
- **`for_each`** — https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
- **`moved` block** — https://developer.hashicorp.com/terraform/language/block/moved
- **`removed` block** — https://developer.hashicorp.com/terraform/language/block/removed
- **`import` block** — https://developer.hashicorp.com/terraform/language/block/import
- **Ephemeral resources** — https://developer.hashicorp.com/terraform/language/block/ephemeral
- **Provider plugin signatures** — https://developer.hashicorp.com/terraform/cli/plugins/signing
- **Provider installation configuration** — https://developer.hashicorp.com/terraform/cli/config/config-file

Source selection favors current upstream documentation, the canonical repository, and the actual upstream license. Version-specific behavior should be rechecked before production decisions because Terraform language features, provider capabilities, and registry behavior evolve independently.
