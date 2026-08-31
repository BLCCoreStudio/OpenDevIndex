# Git

Git is a free and open-source distributed version control system used to track changes, coordinate development, and move work between repositories without requiring a single central server for the local history.

## Why it matters

A normal Git clone contains repository history, so developers can inspect commits, create branches, compare changes, and commit locally before synchronizing with a remote. That distributed model supports everything from solo projects to very large collaborative codebases.

## Core model

Git stores project history as objects addressed by cryptographic hashes. Commits point to project trees and parent commits; branch names are movable references to commits. Commands such as `clone`, `fetch`, `pull`, `commit`, `branch`, `merge`, `rebase`, and `push` manipulate local history or synchronize it with other repositories.

## Good fit

- Source-code version control
- Collaborative software development
- Release and maintenance branches
- Code review workflows built on Git hosting services
- Reproducible history for configuration, documentation, and other text-based assets

## Trade-offs

Git is powerful, but its data model and commands can be confusing at first. Large binary assets may require additional tooling, and rewriting shared history can disrupt collaborators. Hosting platforms such as GitHub, GitLab, and Forgejo add collaboration features around Git but are not Git itself.

## Alternatives

Mercurial and Fossil are distributed alternatives. Subversion and Perforce use more centralized models and can be preferable in specific enterprise or large-binary workflows.

## Verification

This module was reviewed against the official Git website and documentation on 2026-08-31.
