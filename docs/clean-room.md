# Clean-Room Provenance

This repository implements the approved MisikkkiBot OSS MVP as original source code.

## Referenced Binary Evidence

The source product plan records the following static-only evidence:

- Filename: `misikkkibot.exe`
- SHA-256: `A93843E27AD644BE605C7A94934645B5F4C9074BAF639330C459D9EE5140AA93`
- Static inference only: unsigned PyInstaller/Python desktop trading-bot indicators and module-name hints.

## Allowed Inputs

- Approved CEO product plan from [GST-60](/GST/issues/GST-60#document-plan).
- CTO technical execution plan from [GST-61](/GST/issues/GST-61#document-plan).
- Public documentation for Python, SQLite, exchange sandbox concepts, and open-source licensing.
- Original implementation decisions made inside this repository.

## Prohibited Inputs

- Executing the binary.
- Decompiling, unpacking, or dynamically probing the binary.
- Copying binary resources, strings, UI layouts, hidden implementation, or behavior traces.
- Claiming parity with the proprietary binary.

## Implementation Statement

All source files in this repository are first-party clean-room code written to satisfy the approved MVP requirements. The implementation is paper-first, inspectable, auditable, and intentionally excludes live-money trading.
