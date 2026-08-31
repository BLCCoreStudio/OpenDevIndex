# Contributing to OpenDevIndex

OpenDevIndex is a structured, source-backed index of software, developer tools, AI, security, open source, infrastructure, standards, and emerging technology.

## Core principle

Every entry must be useful on its own. Branches are knowledge modules, not placeholders.

## Entry branch naming

Use one of these prefixes:

- `tool/<slug>`
- `language/<slug>`
- `framework/<slug>`
- `ai/<slug>`
- `security/<slug>`
- `cloud/<slug>`
- `database/<slug>`
- `protocol/<slug>`
- `concept/<slug>`
- `opensource/<slug>`

Examples: `tool/qemu`, `language/rust`, `framework/pytorch`, `protocol/mcp`.

## Required files in an entry branch

Each knowledge branch should contain:

- `entry/README.md` — human-readable overview
- `entry/entry.yaml` — machine-readable metadata
- `entry/sources.md` — primary and high-quality references
- `entry/history.md` — notable milestones and changes

## Quality rules

1. No empty or number-only branches.
2. No copied marketing text.
3. Prefer primary sources and official documentation.
4. Separate facts from opinions.
5. Include alternatives and trade-offs where useful.
6. Mark rapidly changing information with a verification date.
7. Keep entries concise enough to scan but detailed enough to teach.

## Pull requests

Changes to the core schema, automation, or catalog belong in normal feature branches and PRs. Knowledge-module branches are independently versioned and should remain understandable without relying on hidden context.

## Long-term goal

Build 10,000 verified, useful knowledge modules without sacrificing quality for the branch count.
