# RISC-V

> An open-standard instruction set architecture built around a small base ISA plus optional extensions for processors ranging from embedded systems to general-purpose computing.

## What it is

RISC-V is an open-standard instruction set architecture (ISA). An ISA defines the software-visible contract between machine code and a processor: instructions, registers, data types, memory and privilege behavior, and other architectural rules that software and hardware implementations agree on.

RISC-V is designed as a family of related ISAs rather than one fixed processor design. Implementations start from a base integer ISA and may add standardized extensions for capabilities such as multiplication, atomics, floating point, vectors, compressed instructions, and privileged execution.

## Why it exists

RISC-V was created to provide a freely available ISA suitable for research, education, and real hardware implementation without tying the architecture to one vendor or one microarchitecture. The specification intentionally separates the architectural interface from implementation choices such as in-order versus out-of-order execution, ASIC versus FPGA, or a particular cache and pipeline design.

## How it works

A RISC-V processor implements a selected base ISA and an explicitly defined set of extensions. Software toolchains can target that architectural profile, while operating systems rely on the privileged architecture when supervisor or machine-level control is required. This modular structure lets small embedded cores implement a narrow feature set while larger systems can combine additional standardized capabilities.

The ISA is not itself a CPU core, chip, operating system, compiler, or emulator. Those are implementations and tools built around the architectural specification.

## Architecture and important concepts

- **Base ISA** — the required integer instruction-set foundation of a RISC-V implementation.
- **Extensions** — optional standardized capabilities layered on the base architecture.
- **Privilege levels** — architectural execution modes and control mechanisms defined by the privileged specification.
- **Profiles** — standardized combinations of ISA features intended to improve software portability across classes of implementations.
- **ISA versus microarchitecture** — RISC-V specifies software-visible behavior while leaving pipeline, cache, execution-unit, and many performance decisions to implementers.

## Typical use cases

- Embedded controllers and microcontrollers.
- Research and teaching in computer architecture.
- General-purpose processors and operating-system-capable systems.
- Custom accelerators that need a standardized programmable control architecture.
- Software and toolchain development using hardware, simulators, or emulators.

## Tools and ecosystem

RISC-V is supported by compilers, assemblers, debuggers, operating systems, simulators, FPGA implementations, commercial silicon, and emulators. QEMU can emulate RISC-V targets, which is useful when developing or testing software without a physical RISC-V machine.

## Alternatives and trade-offs

Other widely deployed instruction-set architectures include Arm and x86-64. Choosing an ISA affects software compatibility, toolchain maturity, available hardware, ecosystem support, power/performance goals, licensing constraints, and implementation flexibility. RISC-V's openness and modularity are major strengths, while the exact software and hardware experience still depends on the specific implementation and extension profile.

## Security and reliability considerations

Security properties cannot be inferred from the ISA name alone. They depend on the implemented privilege architecture, optional security-related extensions, memory protection, firmware, operating system, microarchitecture, toolchain, and system integration. Implementers should distinguish architectural guarantees from implementation-specific behavior and should track the ratification status of extensions they rely on.

## Learning path

A useful progression is: binary and assembly fundamentals → CPU registers and memory → instruction-set architecture → the RISC-V base integer ISA → calling conventions and toolchains → privileged architecture → virtual memory and operating-system support → optional extensions and microarchitecture.

## Knowledge graph

- `compatible-with` → `tool/qemu` — QEMU provides RISC-V emulation for development and testing workflows.

## Verification

This module was reviewed against RISC-V International's ratified specification library and the canonical ISA manual repository on **2026-08-31**. Ratified specifications should be preferred when describing stable architectural behavior; draft or developing extensions can still change.
