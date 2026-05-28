# Release Readiness: MisikkkiBot OSS 0.1.0

## Release Scope

MisikkkiBot OSS 0.1.0 is a clean-room, source-first MVP for local paper trading, replay inspection, risk decisions, audit logging, SQLite persistence, and sandbox-safe connector planning.

The release is not a live-trading product. It introduces no live-money broker, no withdrawal or transfer permission flow, no proprietary executable dependency, and no profitability claim.

## Verification Gate

Run these checks from the repository root before merging or publishing:

```powershell
uv sync
uv run pytest
python -m compileall apps packages tests
uv run misikkki paper-demo --max-bars 6
uv run misikkki verify-no-live
uv run misikkki-desktop --headless
```

Expected smoke evidence:

- `pytest` passes the full suite.
- `compileall` exits successfully for `apps`, `packages`, and `tests`.
- `paper-demo --max-bars 6` completes with paper orders, risk decisions, and no credentials.
- `verify-no-live` reports that live trading is not implemented in the MVP.
- `misikkki-desktop --headless` completes the desktop smoke path.

## QA Handoff

QA must verify the release candidate before public distribution or binary packaging. The minimum QA path is:

- Fresh clone from the release candidate branch.
- `uv sync` on a clean machine or clean virtual environment.
- Full automated test suite.
- Source-run paper demo and no-live negative smoke.
- Desktop headless smoke.
- Manual inspection that no credential, live endpoint, or withdrawal posture is required for the default path.

## Rollback Plan

This release candidate has no remote service, hosted database, production migration, or persisted external state.

If a release blocker is found before merge:

1. Keep the pull request open.
2. Push a corrective commit to the release candidate branch or close the pull request.
3. Do not make the repository public and do not tag a release.

If a blocker is found after merge but before public distribution:

1. Revert the merge commit on `main`.
2. Delete any pre-release tag that points to the bad commit.
3. Leave the repository private until QA re-approves a corrected candidate.

If a blocker is found after public distribution:

1. Publish a GitHub release note marking the affected tag as withdrawn.
2. Revert the offending commit or tag a patched source release.
3. Document the blocker, mitigation, and replacement tag in `CHANGELOG.md`.

## Post-Release Smoke

After merge and before any visibility change or release tag:

```powershell
git clone <release-repository-url>
cd misikkkibot-oss
uv sync
uv run pytest
uv run misikkki paper-demo --max-bars 6
uv run misikkki verify-no-live
uv run misikkki-desktop --headless
```

Record the commit SHA, command outputs, repository visibility, and tag or PR URL in the release issue.
