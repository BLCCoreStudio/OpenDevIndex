# Sources

Verified for the Ansible deep-dive on **2026-09-06**.

Primary references:

- **Ansible Community Documentation** — https://docs.ansible.com/projects/ansible/latest/ (`documentation`)
- **ansible-core source repository** — https://github.com/ansible/ansible (`repository`)
- **ansible-core project metadata and license declaration** — https://github.com/ansible/ansible/blob/devel/pyproject.toml (`repository`)
- **ansible-core GPL license** — https://github.com/ansible/ansible/blob/devel/COPYING (`repository`)
- **Installing Ansible / `ansible-core` versus `ansible`** — https://docs.ansible.com/projects/ansible-core/devel/installation_guide/intro_installation.html (`documentation`)
- **Ansible basic concepts** — https://docs.ansible.com/projects/ansible-core/devel/getting_started/basic_concepts.html (`documentation`)
- **Playbooks** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks.html (`documentation`)
- **Dynamic inventory** — https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_dynamic_inventory.html (`documentation`)
- **Connection plugins** — https://docs.ansible.com/projects/ansible/latest/plugins/connection.html (`documentation`)
- **Module execution architecture** — https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html (`documentation`)
- **Strategy plugins** — https://docs.ansible.com/projects/ansible/latest/plugins/strategy.html (`documentation`)
- **Playbook execution strategies** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html (`documentation`)
- **Variables and precedence** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html (`documentation`)
- **Facts and magic variables** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_vars_facts.html (`documentation`)
- **Roles** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html (`documentation`)
- **Collections** — https://docs.ansible.com/projects/ansible/latest/collections_guide/index.html (`documentation`)
- **Error handling** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_error_handling.html (`documentation`)
- **Executing playbooks / check, diff, become, tags and debugging** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_execution.html (`documentation`)
- **Asynchronous actions** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_async.html (`documentation`)
- **Delegation** — https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_delegation.html (`documentation`)
- **Ansible Vault** — https://docs.ansible.com/projects/ansible/latest/vault_guide/vault.html (`documentation`)
- **Lookup plugins** — https://docs.ansible.com/projects/ansible/latest/plugins/lookup.html (`documentation`)
- **Vars plugins** — https://docs.ansible.com/projects/ansible/latest/plugins/vars.html (`documentation`)
- **Release and maintenance model** — https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html (`documentation`)

Source selection favors current upstream Ansible documentation and the canonical ansible-core repository. Core versions, community-package contents, Collection versions, plugins, Python support, and controller/execution-environment behavior evolve independently, so version-specific production assumptions should be revalidated before upgrades.
