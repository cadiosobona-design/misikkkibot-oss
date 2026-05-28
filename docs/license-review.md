# License And Dependency Review

## Project License

First-party code is licensed under Apache-2.0.

## Runtime Dependencies

The MVP runtime intentionally uses only the Python 3.12 standard library.

| Component | License | Rationale |
| --- | --- | --- |
| Python standard library | Python Software Foundation License | Accepted standard runtime. |
| Tkinter | Python standard library wrapper for Tcl/Tk | Used only for the small local desktop launcher; no binary packaging in MVP. |
| SQLite | Public domain | Accessed through Python standard-library `sqlite3`. |

## Development Dependencies

| Component | License | Rationale |
| --- | --- | --- |
| pytest | MIT | Test runner for unit and integration tests. |

## Blocked Until Explicit Approval

- GPL-only, AGPL, SSPL, or proprietary SDK dependencies.
- Exchange SDKs with unclear licensing.
- Dependencies with telemetry that cannot be disabled.
- PyQt, unless the product intentionally changes to a GPL-compatible or commercial-license posture.

## SBOM And Audit Commands

Recommended release checks:

```powershell
uv sync
uv export --format requirements-txt --no-hashes > requirements.txt
uv run pytest
```

For a release candidate, add a CycloneDX SBOM and vulnerability scan from the locked dependency set before publishing binary packages. The MVP source release does not bundle proprietary runtime dependencies.
