# QEMU

QEMU is an open-source machine emulator and virtualizer. It can model complete systems—including CPUs, memory, storage, networking, and other devices—or run programs built for a different CPU architecture through user-mode emulation.

## Why it matters

QEMU is useful when software needs a machine that is different from the physical host: operating-system development, cross-architecture testing, embedded work, virtual machines, CI, firmware experiments, and security research are common examples.

## How it works

For full-system emulation QEMU presents a virtual machine to a guest operating system. Its Tiny Code Generator (TCG) can translate guest CPU instructions in software, which makes cross-architecture emulation possible. When host and guest environments allow it, QEMU can instead work with hardware virtualization accelerators such as KVM on Linux, Hypervisor Framework on macOS, or WHPX on Windows.

QEMU also provides a large device model ecosystem, including VirtIO devices designed for efficient virtualized I/O, plus block, network, display, USB, and other virtual hardware.

## Good fit

- Running or testing guest operating systems
- Cross-architecture development
- Virtualization stacks built with KVM or other accelerators
- Embedded and firmware development
- Reproducible VM-based CI and testing

## Trade-offs

Pure TCG emulation is flexible but can be substantially slower than hardware-assisted virtualization. QEMU exposes many machine and device options, so configuration can be complex. Some alternatives trade flexibility for simpler deployment or a narrower security/performance model.

## Alternatives and related projects

VirtualBox and VMware products target general desktop virtualization. Firecracker focuses on minimal microVMs. KVM is a Linux virtualization accelerator commonly used by QEMU rather than a complete replacement for QEMU's device and machine model.

## Verification

Reviewed against the QEMU master documentation on 2026-08-31.
