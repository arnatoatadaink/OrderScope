# OrderScope v0.1.5 Release Manifest

Date: 2026-10-02
Release status: ACCEPTED / TAG READY

## Release boundary

- Version: `v0.1.5`
- Commit: `415de1f1dd42f70bd66992961cb43be7edba6ade`
- Boundary subject: `Reconstruct v0.1.5 listing compliance boundary`
- Lineage: cumulative reconstructed v0.1.0 -> v0.1.5

## Functional scope

v0.1.5 adds the cumulative UWBS-067 Listing Compliance / Earnings Repricing Canary layer on top of the previously accepted v0.1.0-v0.1.4 reconstructed release lineage.

The release boundary is accepted as a development/research analytical release. Listing-compliance interpretation, repricing thresholds, and exchange-specific generalization are not represented as universally validated market rules.

## Validation evidence

Exact-boundary validation at `415de1f1dd42f70bd66992961cb43be7edba6ade`:

- Python analysis suite: 635 passed, 1 non-blocking deprecation warning
- Python compileall: PASS
- `git diff --check`: PASS
- Worker suite: 178 passed, 0 failed
- TypeScript typecheck: PASS
- Working tree: clean

## Release classification

`v0.1.5` is ACCEPTED and TAG READY.

No Git tag is created by this manifest. Tag creation remains a separate explicit release action.
