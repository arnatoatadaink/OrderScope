# v0.1.0–v0.1.10 Final Tag Ledger — 2026-10-03

## Status

**TAG TARGETS FROZEN / TAG CREATION NOT AUTHORIZED**

This ledger freezes the intended semantic-version tag targets after exact-boundary validation and release reconstruction. It does not create or push any Git tag.

## Final tag targets

| Version | Tag target SHA | Release scope | Classification |
|---|---|---|---|
| `v0.1.0` | `99b08a0b5fa1bec5921dc42e630c579a4e83c401` | Original WBS/CP baseline | ACCEPTED / TAG READY |
| `v0.1.1` | `bada5bff803321427eb3c8eb1f3d159460ba5dd1` | Operational / runtime | ACCEPTED / TAG READY |
| `v0.1.2` | `f69c52bf574212d1506df81abc7b15694abb7922` | Macro / Carry | ACCEPTED / TAG READY |
| `v0.1.3` | `b4df4e911597d9f17bfa0a50b2057c24159dee9f` | Cross-market / competitor / official macro adapters | ACCEPTED / TAG READY |
| `v0.1.4` | `a798622f839b836f8b60f52dd700b8fd87147991` | AI Theme, `UWBS-062..066` | ACCEPTED / TAG READY |
| `v0.1.5` | `415de1f1dd42f70bd66992961cb43be7edba6ade` | Listing Compliance, `UWBS-067` | ACCEPTED / TAG READY |
| `v0.1.6` | `bfaf89c68daa656b7d75317f086458257cc94da9` | Crypto Market Structure, `UWBS-068..079` | ACCEPTED / TAG READY |
| `v0.1.7` | `423929ae1ff3fd7431260ffdab09810dc7105aa0` | Oil / Commodity / Cross-Asset, `UWBS-080..086` | ACCEPTED / TAG READY |
| `v0.1.8` | `d34d471b20d4f5be865b0414a42240ec7f3061d9` | Physical-SaaS, `UWBS-087..093` | ACCEPTED / TAG READY |
| `v0.1.9` | `fcfba651dbead9d035019e330f61986f5a1a60f7` | VIX / Cross-Asset Volatility, `UWBS-094..100` | ACCEPTED / TAG READY |
| `v0.1.10` | `c1e27d8367c490543e1d207f62d77f3bb5e8bc4e` | PB / active-market validation closeout, `PB-00..PB-10` | ACCEPTED / TAG READY |

## Important lineage notes

### v0.1.6

`bfaf89c68daa656b7d75317f086458257cc94da9` is the accepted cumulative v0.1.6 successor of v0.1.5. Its exact-boundary validation passed with Python 746 passed / 1 non-blocking deprecation warning and Worker 178 passed / 0 failed.

### v0.1.7–v0.1.9

These releases use their final reconstructed/tag-ready release heads, not the earlier historical feature-lane endpoints. Historical endpoints remain evidence anchors only.

- v0.1.7 historical endpoint: `33ca0587d6105202f791f0c8c6c4e9cd6da3ac3d`
- v0.1.8 historical endpoint: `ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325`
- v0.1.9 historical endpoint: `8151d1c2727fd22b0e9f0222f589cee666c99ffc`

The reconstructed release heads preserve the accepted cumulative semantic-version chain and include their release closeout documentation.

### v0.1.10 correction

The earlier candidate `b0cd43ec4ddcce4bd64303bafb2891ebe23c0dcf` is **SUPERSEDED / NOT A TAG TARGET** because it was reconstructed from historical v0.1.9 endpoint `8151d1c...` rather than the formal cumulative v0.1.9 release head.

The corrected boundary `c1e27d8367c490543e1d207f62d77f3bb5e8bc4e` is one commit ahead / zero behind from formal v0.1.9 `fcfba651...`, changes exactly the reviewed 16 PB closeout files, and passed exact-boundary validation:

```text
Python analysis tests   1097 passed
Python compileall       PASS
git diff --check        PASS
Worker tests            228 passed / 0 failed
TypeScript typecheck    PASS
```

## Annotated tag command set

The following commands are prepared for a future explicitly authorized tag-creation step only:

```bash
git tag -a v0.1.0 99b08a0b5fa1bec5921dc42e630c579a4e83c401 -m "OrderScope v0.1.0"
git tag -a v0.1.1 bada5bff803321427eb3c8eb1f3d159460ba5dd1 -m "OrderScope v0.1.1"
git tag -a v0.1.2 f69c52bf574212d1506df81abc7b15694abb7922 -m "OrderScope v0.1.2"
git tag -a v0.1.3 b4df4e911597d9f17bfa0a50b2057c24159dee9f -m "OrderScope v0.1.3"
git tag -a v0.1.4 a798622f839b836f8b60f52dd700b8fd87147991 -m "OrderScope v0.1.4"
git tag -a v0.1.5 415de1f1dd42f70bd66992961cb43be7edba6ade -m "OrderScope v0.1.5"
git tag -a v0.1.6 bfaf89c68daa656b7d75317f086458257cc94da9 -m "OrderScope v0.1.6"
git tag -a v0.1.7 423929ae1ff3fd7431260ffdab09810dc7105aa0 -m "OrderScope v0.1.7"
git tag -a v0.1.8 d34d471b20d4f5be865b0414a42240ec7f3061d9 -m "OrderScope v0.1.8"
git tag -a v0.1.9 fcfba651dbead9d035019e330f61986f5a1a60f7 -m "OrderScope v0.1.9"
git tag -a v0.1.10 c1e27d8367c490543e1d207f62d77f3bb5e8bc4e -m "OrderScope v0.1.10"
```

Before any future push, verify locally:

```bash
git show-ref --tags
git for-each-ref refs/tags/v0.1 --format='%(refname:short) %(objectname) %(subject)'
```

A future authorized push should be performed only after verifying every tag object resolves to the intended commit. Do not use force-update semantics for release tags.

## Explicit exclusions

This ledger does not authorize:

- creation or push of Git tags;
- force-moving any release tag;
- production provider activation;
- Worker/Cron deployment;
- D1 mutation;
- secret or credential changes;
- automated trading actions;
- history rewrite or force push.

The next planned semantic release remains `v0.1.11` for Crypto On-chain Event Intelligence (`UWBS-101..104`).
