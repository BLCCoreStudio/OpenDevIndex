# Git

> Git is a distributed version control system built around a content-addressed object database, a commit graph, movable references, and local-first collaboration.

Git is one of the foundational tools of modern software development. This module explains not only the commands people use every day, but the internal model that makes those commands predictable.

## What is Git?

Git is a **distributed version control system (DVCS)**. A normal clone contains the project's history and object database, so most history inspection, branching, committing, merging, rebasing, and recovery work happens locally rather than requiring a central server.

At its core, Git is also a **content-addressable filesystem with a version-control interface on top**. Files and repository structures are stored as objects identified by hashes. Commits connect those objects into a directed history graph, while branches and tags provide human-friendly names for important points in that graph.

Git itself is not GitHub, GitLab, Bitbucket, or another hosting service. Those services build collaboration, permissions, pull requests, CI, issue tracking, and web interfaces around Git repositories.

## Why does Git exist?

Git was created in 2005 for Linux kernel development after the kernel community needed a new distributed source-control system. Its design emphasized properties that mattered for a large, highly distributed project:

- fast local operations;
- cheap branching and merging;
- distributed development without a mandatory central server;
- strong integrity checking of repository objects;
- efficient transfer and storage of large source histories;
- workflows that do not require every contributor to share the same branching model.

Those design choices are why Git scales from one developer working locally to very large open-source and commercial projects.

## The core mental model

The most useful way to understand Git is to stop thinking of it as "a folder that remembers file changes" and instead think in terms of three working states plus an immutable object graph.

### Working tree

The **working tree** is the checked-out set of files that you edit with normal tools.

### Index / staging area

The **index** is Git's proposed next snapshot. `git add` updates the index with the content and metadata that should be part of the next commit. This is why you can stage only some files—or even selected hunks—without committing every local modification.

### Repository

The repository, normally represented by the `.git` directory, stores objects, references, configuration, logs, and other internal state.

A common flow is therefore:

```text
working tree  --git add-->  index  --git commit-->  commit graph
```

This model explains many commands that otherwise feel arbitrary. `git diff` normally compares the working tree with the index. `git diff --staged` compares the index with the current commit. `git commit` records the snapshot represented by the index.

## Internal architecture

A typical non-bare repository has a `.git` directory containing the repository database and control files. Important pieces include:

```text
.git/
├── HEAD
├── config
├── index
├── objects/
├── refs/
├── logs/
└── hooks/
```

- `objects/` stores Git objects, initially as loose objects and later commonly inside packfiles.
- `refs/` stores references such as local branches and tags when using the traditional ref backend.
- `HEAD` normally identifies the currently checked-out branch; in detached-HEAD state it directly identifies a commit.
- `index` stores the staging-area representation.
- `logs/` commonly contains reflogs, which record local movements of references and can be extremely useful for recovery.
- `config` contains repository-specific Git configuration.
- `hooks/` is the conventional location for local repository hooks.

Modern Git can use additional repository formats and optimized data structures, so the exact on-disk layout can vary. The stable mental model is more important than memorizing every file.

## Object model: blob, tree, commit, tag

Git's object model is the heart of the system.

### Blob

A **blob** stores file content. A blob does not inherently store the file's path or filename. Identical file contents can therefore be represented by the same object.

### Tree

A **tree** represents a directory-like snapshot. Tree entries associate names and modes with blobs or other trees.

### Commit

A **commit** points to a top-level tree and records metadata such as author, committer, message, and parent commit or commits. Parent links form the commit graph.

A normal commit therefore means, roughly:

```text
commit
  ├── tree -> snapshot
  ├── parent -> previous commit
  ├── author / committer
  └── message
```

A merge commit can have multiple parents.

### Tag

An **annotated tag** is an object that can name another object and contain tagger metadata, a message, and optionally a cryptographic signature. A lightweight tag is simply a reference without a separate tag object.

## Content addressing and object IDs

Git computes object IDs from object content plus type/length framing. Because higher-level objects refer to lower-level objects by object ID, changing a tracked file can ultimately produce new tree and commit IDs.

This gives Git strong integrity properties: accidental or malicious modification of stored objects is detectable when the expected object ID no longer matches the content.

Object IDs should not be confused with author authentication. A commit hash proves identity of content within Git's object model; it does **not** by itself prove who created the commit. Signing commits or tags addresses a different problem.

Git's traditional repository format uses SHA-1 object names. Git also supports SHA-256 repository formats, while the official transition documentation continues to describe compatibility and interoperability considerations between formats.

## Refs, branches, tags, and HEAD

A raw commit ID is inconvenient for humans, so Git uses **references**.

A branch such as `main` is fundamentally a movable reference to a commit. Creating a branch is therefore cheap: Git does not copy the entire project history.

When you make a new commit while `HEAD` points to a branch, the branch reference advances to the new commit.

```text
A --- B --- C   main
              ^
             HEAD
```

After one commit:

```text
A --- B --- C --- D   main
                    ^
                   HEAD
```

A tag usually stays fixed, which makes tags useful for naming releases or other important points in history.

## The index in more detail

The index is not merely a list of "files marked for commit." It is a structured representation of paths, object IDs, modes, and related state used to construct the next tree.

This explains several useful workflows:

- stage only one file while leaving other edits uncommitted;
- stage selected lines with `git add -p`;
- resolve merge conflicts by updating index stages;
- inspect staged changes before committing;
- build a commit that differs from the current working tree.

Understanding the index is one of the biggest steps from memorizing Git commands to understanding Git.

## Branching

Branches provide independent movable names over the same underlying commit graph.

```bash
git switch -c feature/search
# edit files
git add .
git commit -m "Add search"
```

Creating the branch does not duplicate every project file in Git's history. The new branch initially points at an existing commit and moves as new commits are added.

Branch names are local by default. A branch named `main` in your clone and a remote-tracking reference such as `origin/main` are related by workflow and configuration, not because they are literally the same reference.

## Merge

**Merging** combines lines of development.

If one branch is directly ahead of another, Git may perform a **fast-forward**, moving the target branch reference without creating a merge commit.

When histories have diverged, a successful non-fast-forward merge normally creates a commit with multiple parents. The merge machinery determines a common ancestor and combines changes made on each side.

Conflicts occur when Git cannot safely decide how to combine changes. A conflict is not corruption; it is a request for a human or higher-level tool to choose the intended result.

Useful commands include:

```bash
git merge feature/search
git status
git diff --merge
git merge --abort
```

## Rebase

**Rebase** changes the base of a line of development by replaying changes onto another commit.

Conceptually:

```text
      C --- D   feature
     /
A --- B --- E   main
```

can become:

```text
A --- B --- E --- C' --- D'   feature
```

`C'` and `D'` represent new commits, not the original objects moved elsewhere. Their parent relationships changed, so their commit IDs change too.

This is why rebasing published history requires coordination. Rebase is powerful for cleaning local history and updating a feature branch, but rewriting commits that other people already based work on can create unnecessary divergence.

## Remotes and remote-tracking references

A **remote** is a named configuration describing another repository location plus fetch/push behavior. `origin` is only a conventional default name created by many clone workflows.

```bash
git remote -v
git fetch origin
git push origin main
```

Fetching transfers objects and updates remote-tracking references such as `refs/remotes/origin/main`. It does not automatically mean your current local branch has been merged or rebased.

This distinction is useful:

- `fetch` updates your view of remote history;
- `merge` combines another history into your current branch;
- `rebase` replays your commits on another base;
- `pull` is a higher-level convenience operation that fetches and then integrates according to configuration/options.

## Refspecs

A **refspec** describes how references map between local and remote namespaces. Most users rarely write complex refspecs manually, but the concept explains how `fetch` and `push` decide which refs to transfer and where to store them.

Refspecs are especially relevant for mirrors, CI systems, unusual branch layouts, and tools that need precise control of remote refs.

## Packfiles and repository storage

New objects may initially exist as **loose objects**. Over time, Git can consolidate objects into **packfiles**.

Packfiles reduce storage and transfer cost by grouping objects and allowing delta compression between related content. Associated indexes let Git locate packed objects efficiently.

Important maintenance-related structures and features include:

- packfiles and pack indexes;
- multi-pack indexes;
- commit-graph files;
- reachability bitmaps;
- automatic maintenance and garbage collection;
- pruning of unreachable objects after retention rules allow it.

For normal repositories, Git handles most of this automatically. Large monorepos and hosting systems care much more about these details because object count, history shape, binary content, and clone behavior directly affect performance.

## Transfer protocols

Git repositories can exchange data through several transports. Common real-world choices include HTTPS and SSH, while local transports and the native Git protocol also exist.

The transport is only one part of the process. Git also performs protocol-level negotiation to determine which objects need to be transferred. Modern protocol versions reduce unnecessary advertisement and improve extensibility for large repositories and servers.

A remote hosting service can therefore provide authentication, authorization, policy, and network transport without changing Git's fundamental object model.

## Common workflows

Git does not impose one universal collaboration workflow. Common models include:

### Feature branches

Develop work on short-lived branches, review it, then merge or rebase according to project policy.

### Trunk-based development

Keep branches short-lived and integrate into a primary branch frequently, often with strong automated testing.

### Fork-and-pull-request

Contributors push branches to personal forks and propose integration into an upstream repository through a hosting platform.

### Maintainer workflow

Maintainers fetch or receive contributor histories, review and test them, then merge, rebase, cherry-pick, or otherwise integrate selected commits.

The important distinction is that these are **project workflows built with Git primitives**, not features that define Git itself.

## Practical command map

### Start or obtain a repository

```bash
git init
git clone <url>
```

### Inspect state

```bash
git status
git log --graph --decorate --oneline --all
git diff
git diff --staged
```

### Build a commit

```bash
git add <path>
git add -p
git commit -m "Explain the change"
```

### Work with branches

```bash
git branch
git switch -c feature/name
git switch main
git merge feature/name
```

### Work with remotes

```bash
git remote -v
git fetch --all --prune
git push -u origin feature/name
```

### Recover from mistakes

```bash
git reflog
git restore <path>
git restore --staged <path>
git reset <commit>
```

Recovery commands can destroy uncommitted work when used incorrectly. Before using destructive reset/clean operations, inspect `git status`, understand which state is being changed, and create a backup branch when uncertain.

## Plumbing and porcelain

Git commands are often described as either **porcelain** or **plumbing**.

Porcelain commands provide user-facing workflows: `git status`, `git switch`, `git commit`, `git merge`, and similar commands.

Plumbing commands expose lower-level object and reference operations. Examples include:

```bash
git hash-object
git cat-file
git write-tree
git commit-tree
git update-ref
```

Learning a few plumbing commands is valuable because they reveal that ordinary Git operations are compositions over objects, trees, commits, refs, and the index.

## Tools commonly used with Git

Git is surrounded by a large ecosystem.

- **Hosting and collaboration:** GitHub, GitLab, Bitbucket, Codeberg, self-hosted forges.
- **Large-file handling:** [Git LFS](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/git-lfs/entry).
- **GitHub command line:** [GitHub CLI](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/gh/entry).
- **CI/CD:** [GitHub Actions](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/github-actions/entry), Jenkins, Buildkite, GitLab CI/CD, and many others.
- **Editors and IDEs:** most major editors expose staging, diff, blame, history, and merge tooling over Git.
- **Review tools:** hosting platforms add pull/merge requests and protected-branch workflows on top of Git refs and commits.
- **Repository analysis:** linters, secret scanners, dependency tools, code-search systems, and release automation frequently use Git history as an input.

## Integrations

Git commonly integrates with:

- SSH agents and HTTPS credential helpers;
- commit/tag signing using supported signing mechanisms;
- CI systems triggered by pushes, tags, or merge requests;
- issue trackers and code-review systems;
- submodules and subtree-based dependency workflows;
- Git LFS for large binary assets;
- hooks for local or server-side automation;
- package/release systems that derive versions from tags or commits.

These integrations should not be confused with the core Git data model. Keeping that boundary clear makes it easier to debug whether a problem is in Git itself, a hosting service, authentication, CI, or project policy.

## Alternatives

Git is dominant, but it is not the only version-control model.

- **Mercurial** is another distributed VCS with different usability and extension trade-offs.
- **Fossil** combines distributed version control with additional project-management features in a tightly integrated system.
- **Subversion (SVN)** uses a centralized model that can be simpler for some controlled environments and file-locking workflows.
- **Perforce Helix Core** is common in some very large game, media, and binary-heavy environments where centralized asset workflows are important.
- **Jujutsu** provides a newer user model and can interoperate with Git repositories in many workflows.

The right comparison depends on team topology, repository size, binary assets, locking requirements, hosting constraints, and whether Git ecosystem compatibility is mandatory.

## Trade-offs

### Strengths

- Nearly all core history operations are local and fast.
- Branches and tags are lightweight references over shared objects.
- The distributed model supports many collaboration topologies.
- Content addressing provides strong repository-integrity properties.
- The ecosystem is enormous: hosting, CI, editors, review, automation, and deployment systems commonly understand Git.
- Git exposes both high-level workflows and low-level primitives.

### Costs

- The command surface is large and historically inconsistent in places.
- The index, detached HEAD, ref namespaces, reset modes, and history rewriting can confuse new users.
- Large binary histories can make repositories expensive because Git is optimized primarily for source-like content and history.
- Distributed history makes some centralized locking and huge-asset workflows less natural.
- Powerful history-rewriting and cleanup commands can destroy uncommitted work if used without understanding the affected state.

## Performance characteristics

Git performance depends on object count, history shape, working-tree size, filesystem behavior, network latency, and the amount/type of repository content.

Important scaling techniques include:

- packfiles and delta compression;
- commit-graph acceleration;
- multi-pack indexes;
- reachability bitmaps;
- shallow clones for limited-history use cases;
- partial clone to avoid immediately downloading every object;
- sparse checkout to reduce the checked-out working tree;
- background maintenance;
- Git LFS or external asset systems for large binary content.

A repository with a few giant changing binaries can behave very differently from a source repository with millions of small text-file revisions, even when their current checkout sizes look similar.

## Reliability and recovery

Git's object graph and reflogs make many mistakes recoverable as long as objects have not been pruned and destructive working-tree changes have not erased uncommitted data.

Useful recovery concepts:

- `git reflog` can reveal commits that branches previously pointed to;
- a temporary recovery branch can preserve a found commit;
- `git fsck` can inspect repository connectivity and object validity;
- backups still matter because Git is version control, not a complete backup strategy;
- untracked or uncommitted working-tree content may have no recoverable Git object at all.

The safest habit before risky history surgery is to create an extra branch or tag pointing to the current commit.

## Security and trust boundaries

Git's integrity model and Git's trust model are different concerns.

Important security points include:

- object IDs detect content mismatch but do not authenticate an author;
- signed commits and signed tags can provide cryptographic identity evidence when keys and verification policy are managed correctly;
- credentials used for HTTPS/SSH remotes should be protected like other development secrets;
- repository configuration, hooks, build scripts, submodules, and project tooling can cross trust boundaries—treat untrusted repositories as untrusted code/content;
- `safe.directory` protections help prevent Git from trusting repositories owned by unexpected users in shared environments;
- `git fsck` and transfer-side fsck settings can detect malformed or problematic object graphs in appropriate workflows;
- secrets committed to history should be considered exposed even if a later commit deletes the file; history rewriting and credential rotation may both be required.

Traditional Git object naming is based on SHA-1, and Git has long-running work for SHA-256 repository formats. Hash migration is a repository-format concern; it should not be simplified into a claim that commit hashes are digital signatures.

## Common mistakes

### Treating `git add` as "tell Git this file exists"

`git add` updates the index with content for the next snapshot. Re-running it after editing a staged file matters because the working tree and index can differ.

### Confusing `origin/main` with `main`

`origin/main` is normally a remote-tracking reference updated by fetch. `main` is a local branch.

### Rebasing shared history casually

Rebase creates new commits. Coordinate before rewriting commits others may already use.

### Using `git reset --hard` or `git clean` without checking

These commands can permanently remove uncommitted work. Inspect status and create backups first.

### Committing generated secrets or credentials

Deleting them in the next commit does not remove them from earlier history.

### Assuming a merge conflict means Git is broken

A conflict means Git found competing changes it cannot safely resolve automatically.

### Keeping huge changing binaries directly in normal history

This can permanently inflate clone/storage costs. Consider Git LFS or an asset-oriented system.

### Memorizing command recipes without understanding state

Most Git confusion becomes easier when you ask: **working tree, index, object database, or ref—what is this command changing?**

## Ecosystem

Git is infrastructure for a large portion of the software ecosystem rather than a standalone developer utility.

It underpins:

- public open-source collaboration;
- code review and pull-request systems;
- continuous integration and deployment;
- release tagging and automated versioning;
- infrastructure-as-code repositories;
- package-source workflows;
- documentation systems;
- reproducible-build inputs;
- security and compliance tools that inspect repository history.

This ecosystem effect is one of Git's strongest practical advantages: choosing Git often means immediate compatibility with existing developer tooling.

## Learning path

### Beginner

1. repository, working tree, index, commit;
2. `status`, `diff`, `add`, `commit`, `log`;
3. local branches with `switch`/`branch`;
4. remotes, `fetch`, `push`, and simple merges.

### Intermediate

1. commit graph and ancestry;
2. merge versus rebase;
3. remote-tracking branches and refspec basics;
4. reflog and recovery;
5. tags, stash, cherry-pick, revert;
6. interactive staging and interactive rebase.

### Advanced

1. blobs, trees, commits, tags;
2. refs, HEAD, index format, and reflogs;
3. packfiles, commit-graph, bitmaps, maintenance;
4. partial clone and sparse checkout;
5. transfer protocols and server-side behavior;
6. signing, fsck, repository trust, and hash-format transition;
7. plumbing commands and custom automation.

## Authoritative sources

The best starting points are maintained by the Git project itself:

- [Git official site](https://git-scm.com/)
- [Pro Git book](https://git-scm.com/book/en/v2)
- [Git Internals — Plumbing and Porcelain](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Git Internals — Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- [Git Internals — Git References](https://git-scm.com/book/en/v2/Git-Internals-Git-References)
- [Git Internals — Packfiles](https://git-scm.com/book/en/v2/Git-Internals-Packfiles)
- [Git on the Server — The Protocols](https://git-scm.com/book/en/v2/Git-on-the-Server-The-Protocols)
- [Git command documentation](https://git-scm.com/docs)
- [Git index format](https://git-scm.com/docs/index-format)
- [Git pack format](https://git-scm.com/docs/gitformat-pack)
- [Git hash-function transition](https://git-scm.com/docs/hash-function-transition)
- [Canonical Git source repository](https://github.com/git/git)

## Related OpenDevIndex modules

- [Git LFS — large-file extension](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/git-lfs/entry)
- [GitHub CLI — GitHub workflows from the terminal](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/gh/entry)
- [GitHub Actions — repository automation and CI/CD](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/github-actions/entry)
- [CMake — build-system generation often used inside Git-managed projects](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/cmake/entry)
- [Ninja — fast build executor frequently used with generated project graphs](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/ninja/entry)

As taxonomy-v3 coverage expands, Git should gain typed relationships to repository hosting, source-control concepts, cryptographic signing, CI/CD, monorepo tooling, and alternative VCS modules.

## What to learn next

A strong next sequence is:

1. **Git LFS** if you work with large assets;
2. **GitHub CLI / forge tooling** if you collaborate through hosted repositories;
3. **CI/CD systems** to understand how commits trigger automated build and test pipelines;
4. **cryptographic signing** to separate repository integrity from author authentication;
5. **build systems and package managers** to understand how source history becomes reproducible software artifacts;
6. **distributed-systems concepts** if you want to understand why Git's DAG and synchronization model behave the way they do.

## Taxonomy

- Stable address: `tool/git`
- Kind: `tool`
- Domains: `cli`, `developer-tools`
- Status: `active`

## Verification

This deep-dive module was expanded and source-checked on **2026-09-01** using official Git documentation and the canonical Git repository. Version-sensitive behavior should always be checked against the current upstream documentation.

## Maintenance

Preserve the stable `tool/git` address. Future updates should prioritize factual changes in repository formats, protocols, security guidance, scaling features, and major workflow semantics rather than copying release-note trivia into the module.
