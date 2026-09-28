# OrderScope v0.1.0..v0.1.3 Boundary Reconstruction — 2026-09-29

Status: **RESEARCH COMPLETE ENOUGH FOR RECONSTRUCTION PLAN; NO HISTORY REWRITE PERFORMED**

## 1. Purpose

Identify the historical implementation / acceptance boundaries needed to reconstruct clean release snapshots for `v0.1.0` through `v0.1.3`.

The release model is cumulative and functional:

- `v0.1.0`: original WBS/CP baseline, PB excluded.
- `v0.1.1`: operational/runtime UWBS extensions.
- `v0.1.2`: macro/carry UWBS lane.
- `v0.1.3`: cross-market / competitor / official macro adapters.

This investigation does not create tags, move refs, rewrite commits, or merge into `main`.

## 2. v0.1.0 — clean historical boundary found

The original Local Corporate Intelligence WBS comprises W0/L0/L1/I0/S0/E0/N0/N1/O0/X0. R0 is explicitly the later operational/recovery extension lane and PB is excluded from this release boundary.

Key final original-WBS acceptance evidence:

- `46ec6e5b87cbdb2d248971f9d311c4823c012b0f` — Accept X0-006 and track post-X0 operational gaps.
- `957ad31be5d13e56814ff77b110295f777762d40` — Accept L1-006 and advance N1-006 recall evaluation.
- `7f85da19813f49b51cc2c8dd8a94e03578699b23` — Accept O0-005 after local verification.
- `99b08a0b5fa1bec5921dc42e630c579a4e83c401` — Accept N1-006 real-data benchmark.

Immediately after the N1-006 acceptance, the UWBS-originated worker extension is formally incorporated:

- `e8fc59b4dea4780cbd588d65ed760f1fd3004e3b` — Incorporate UWBS-016 as W1-001 News Worker task.

Therefore the strongest existing-history boundary candidate for `v0.1.0` is:

```text
v0.1.0 candidate = 99b08a0b5fa1bec5921dc42e630c579a4e83c401
```

This is a naturally clean boundary because it closes the final identified original-WBS real-data benchmark immediately before the first UWBS-originated W1 incorporation.

## 3. v0.1.1 — logical scope is accepted, but final closeout is interleaved

Canonical scope:

```text
UWBS-001..004 -> R0-001..004
UWBS-016      -> W1-001 / formal operational orchestration boundary
UWBS-023..026 -> R0-006..009
```

Relevant operational evidence includes:

- `2beda8bfd8e6caf17e1f418467746913379b5252` — Add R0-009 local custody failure fixtures.
- `40fc688a1365231a86b382808e9b71fcd84c540d` — Accept R0-007 first remote custody transfer.
- `996f19f566d63f228e8ea43aaf35fb17f1ef789d` — Record R0-008 first remote ACK acceptance.
- `2ad52182a06187c83fd32b98ac5d679458fe7300` — W1-001 confirmation closeout.

The important topology issue is that the W1-001 final closeout occurs on 2026-09-14 after work belonging to v0.1.2/v0.1.3 has already entered the same historical line.

Therefore there is no single historical commit that simultaneously provides:

1. the complete `v0.1.1` functional scope, and
2. exclusion of later v0.1.2/v0.1.3 implementation.

For a clean reconstructed release, use the accepted operational commits as source commits and replay them onto the `v0.1.0` reconstructed parent in dependency order. The existing-history SHA must not be presented as a pure `v0.1.1` snapshot.

A useful pre-interleaving operational checkpoint is:

```text
996f19f566d63f228e8ea43aaf35fb17f1ef789d
```

but it is not sufficient by itself to represent the later W1-001 confirmation closeout.

## 4. v0.1.2 / v0.1.3 — historical order is explicitly interleaved

### v0.1.2 scope

```text
UWBS-011 -> A0-003
UWBS-012 -> A0-004
UWBS-013 -> A0-005
UWBS-014 -> A0-006
UWBS-015 -> A0-007
```

Observed implementation chronology:

- UWBS-011 starts at `e25391fd3cd8bdd7e40d77853e8a0572489e42e5` at 08:23 JST on 2026-09-14.
- UWBS-012 implementation/test/export follows, including final identifier fix `ac5473c123e44289433d237e455b7655f896b314`.
- UWBS-013 reaches exported contract `4747af279df1af3e358654b88a8f0da3eb9fb423`.
- UWBS-014 Canary fixture is added at `eef6befc227d9641bc178c30ea191d845a777649`.
- UWBS-015 provider survey is documented at `b49090d02bcc3274840f467cdf6fb6b0d5171fef`.

### v0.1.3 scope

```text
UWBS-027 -> A0-008
UWBS-028 -> A0-009
UWBS-029 -> A0-010
UWBS-030 -> A0-011
UWBS-031 -> A0-012
UWBS-032 -> A0-013
UWBS-033 -> A0-014
UWBS-034 -> A0-015
UWBS-035 -> A0-016
UWBS-036 -> A0-017
```

The first v0.1.3 work predates v0.1.2 implementation:

- `629d15c9ac57bd67ff94fba9345bd45820509cdd` — Implement UWBS-027 at 07:03 JST.
- `e47a4e7246077ffd093954240383daf19a251828` — Implement UWBS-028 at 07:04 JST.
- `3d8d6f00e317382732459926a30879a59f86bf9f` — Implement UWBS-029 at 07:28 JST.
- `d53d353e19c40b34a501cb3b587c851ccfc0b740` — Accept UWBS-031 at 08:22 JST.

Only after that does UWBS-011 begin at 08:23 JST.

Later v0.1.3 adapters resume after the v0.1.2 macro lane:

- `d932ef1f2f3119ed40ecfcf5b3eb42ce832ae4f8` — Accept UWBS-032 and stage UWBS-033.
- `ee061c021d0c39c9ffe25ee731491af78e5f945a` — Accept UWBS-033 and stage UWBS-034.
- `c68a3b3360b0e3b8a15df4c1d3338b8a8dedb576` — Accept UWBS-034 and decompose UWBS-035.
- `0a02add6777745fd65cc0800fd232f745401c583` — Accept UWBS-035 and UWBS-036 macro source adapters.

The formal WBS incorporation later records both macro and CBRS extensions together:

- `3bb42acd07325a52a7f596158892e986983ebc75` — docs: incorporate macro and CBRS A0 extensions.

### Consequence

A clean historical `v0.1.2` tag cannot be placed on the existing line without including part of the future `v0.1.3` scope.

A clean `v0.1.3` cumulative release can use the fully accepted source material, but if version purity is required it should be rebuilt on top of the reconstructed `v0.1.2` parent.

## 5. Reconstruction recommendation

If preserving functional version purity is more important than preserving existing commit SHAs, construct a new release lineage rather than force old chronological commits to serve as tags.

Recommended lineage:

```text
reconstructed-v0.1.0
  = original-WBS content through source boundary 99b08a0...

reconstructed-v0.1.1
  = replay only operational/runtime scope commits and accepted closeout content

reconstructed-v0.1.2
  = replay only UWBS-011..015 / A0-003..007 content

reconstructed-v0.1.3
  = replay UWBS-027..036 / A0-008..017 content
```

Do not replay acceptance documents blindly if they embed historical SHAs. During reconstruction:

1. freeze original refs and all source SHAs;
2. create a source-commit inventory per release scope;
3. replay implementation/test/documentation content in dependency order;
4. normalize embedded SHA references only after the reconstructed DAG is stable;
5. preserve `old SHA -> reconstructed SHA` mapping permanently;
6. run full regression after every reconstructed release boundary;
7. tag only the reconstructed acceptance commit, not intermediate replay commits.

## 6. Current boundary classification

| Version | Existing-history clean boundary? | Best current finding |
|---|---|---|
| v0.1.0 | **Yes** | `99b08a0b5fa1bec5921dc42e630c579a4e83c401` |
| v0.1.1 | **No, final closeout interleaved** | reconstruct from operational accepted commits; `996f19f...` is useful pre-interleaving checkpoint |
| v0.1.2 | **No, v0.1.3 begins first** | reconstruct UWBS-011..015 onto reconstructed v0.1.1 |
| v0.1.3 | **Not pure on old line; cumulative source complete** | final source acceptance includes `0a02add...`; rebuild on reconstructed v0.1.2 for purity |

## 7. No-op statement

This report performs no branch movement, no tag creation, no history rewrite, no `main` integration, no provider/runtime mutation and no PB reopening.
