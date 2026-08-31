# Rust

Rust is a systems programming language focused on performance, reliability, and productive low-level development. Its ownership and borrowing model lets safe Rust prevent many memory-safety and data-race bugs at compile time without requiring a garbage collector.

## Why it matters

Rust targets software that needs tight control over memory and performance while still benefiting from strong static guarantees. It is used for command-line tools, network services, operating-system components, embedded software, WebAssembly, developer infrastructure, and other performance-sensitive systems.

## Core model

Rust tracks ownership of values and the lifetimes of references. The compiler checks borrowing rules so safe code cannot freely create dangling references or unsynchronized mutable aliasing. Rust also has `unsafe` features for operations that cannot be proven safe by the compiler; developers using them take responsibility for preserving the language's safety invariants.

Rust does not require a garbage collector or a language runtime for ordinary native code. Cargo provides dependency management, builds, testing, and package workflows, while rustup manages toolchains and targets.

## Good fit

- Native software where memory safety and predictable performance matter
- CLI and developer tools
- Networking and backend infrastructure
- Embedded systems and WebAssembly
- Components replacing or complementing C and C++

## Trade-offs

Ownership and lifetime rules create a learning curve, especially for complex shared data structures. Compile times and dependency graphs can become substantial in large projects. Rust's ecosystem is mature in many areas but not equally deep in every application domain.

## Alternatives

C and C++ provide lower-level control with fewer enforced safety guarantees. Go emphasizes simplicity and garbage-collected concurrency. Zig emphasizes explicit low-level control and C interoperability with a different safety and language model.

## Verification

Reviewed against the Rust project website, reference, and release information on 2026-08-31.
