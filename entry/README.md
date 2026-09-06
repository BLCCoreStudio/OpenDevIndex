# Apache Subversion

Apache Subversion (SVN) is a centralized version control system. A repository server is the authoritative history boundary, commits create globally ordered revisions, and working copies carry local administrative state for checked-out paths.

## Where it fits

Subversion is a strong fit when a team values centralized repository authority, path-based access control, sparse working copies for large trees, globally meaningful revision numbers, or explicit locking workflows for merge-hostile assets.

## Core model

- Repository history is organized as revisions of a versioned filesystem.
- Branches and tags are conventionally represented as cheap repository copies of paths.
- Versioned properties carry metadata such as ignore rules, externals, merge tracking, and lock expectations.
- Working copies can be sparse and do not normally contain the complete repository history.
- Commits require access to the authoritative repository and create one new repository revision.

## Operational boundaries

Subversion's centralized model changes failure and governance trade-offs compared with distributed systems such as Git. Repository availability sits on the commit path, backup/restore is repository-centric, and path authorization can be significantly more granular than common whole-repository clone access.

For migration or architecture decisions, compare repository authority, history identity, branch/tag semantics, authorization, sparse access, binary locking, backup, and CI source identity rather than treating centralized and distributed version control as interchangeable.

## Authoritative references

- [Apache Subversion project](https://subversion.apache.org/)
- [Apache Subversion documentation](https://subversion.apache.org/docs/)
- [Apache Subversion source mirror](https://github.com/apache/subversion)
