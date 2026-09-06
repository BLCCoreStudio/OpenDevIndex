# Sources

Verified for the GitHub Actions deep-dive on **2026-09-06**.

Primary references:

- **GitHub Actions documentation** — https://docs.github.com/actions (`documentation`)
- **Workflow syntax** — https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (`documentation`)
- **Events that trigger workflows** — https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (`documentation`)
- **Contexts reference** — https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (`documentation`)
- **Expressions reference** — https://docs.github.com/en/actions/reference/workflows-and-actions/expressions (`documentation`)
- **Secure use reference** — https://docs.github.com/en/actions/reference/security/secure-use (`documentation`)
- **Automatic `GITHUB_TOKEN` authentication** — https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication (`documentation`)
- **OpenID Connect concept** — https://docs.github.com/en/actions/concepts/security/openid-connect (`documentation`)
- **OpenID Connect reference** — https://docs.github.com/en/actions/reference/security/oidc (`documentation`)
- **Deployment environments** — https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments (`documentation`)
- **Reusable workflow configurations** — https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations (`documentation`)
- **Dependency caching** — https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows (`documentation`)
- **Workflow artifacts** — https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts (`documentation`)
- **GitHub-hosted runners** — https://docs.github.com/en/actions/concepts/runners/github-hosted-runners (`documentation`)
- **Self-hosted runners** — https://docs.github.com/en/actions/concepts/runners/self-hosted-runners (`documentation`)
- **Self-hosted runner reference** — https://docs.github.com/en/actions/reference/runners/self-hosted-runners (`documentation`)
- **Actions Runner Controller** — https://docs.github.com/en/actions/concepts/runners/actions-runner-controller (`documentation`)
- **Runner groups** — https://docs.github.com/en/actions/concepts/runners/runner-groups (`documentation`)
- **GitHub Actions runner source repository** — https://github.com/actions/runner (`repository`)
- **GitHub Actions runner MIT license** — https://github.com/actions/runner/blob/main/LICENSE (`repository`)

The `MIT` license above applies to the open-source `actions/runner` repository. The hosted GitHub Actions service and wider GitHub platform have separate product/service terms and should not be inferred to be MIT-licensed from the runner repository.

Source selection favors current official GitHub documentation and the canonical runner repository. Event semantics, permissions, runner images, OIDC claims, environments, reusable workflows, cache/artifact behavior, and hosted-service capabilities evolve continuously and should be rechecked for security-sensitive decisions.
