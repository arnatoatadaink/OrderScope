# OrderScope v0.1.0–v0.1.11 Tag-Ready Status — 2026-10-03

Status: **ACCEPTED / TAG READY — NO GIT TAGS CREATED**

This document is the current release/tag-status authority for the session closeout on 2026-10-03.

## Current tag state

Repository tag inspection found no Git tag namespace. Therefore no `v0.1.x` Git tags are currently considered created or pushed.

`TAG READY` means the release boundary has been accepted and its intended target is frozen. It does not mean an annotated Git tag exists.

## Accepted / TAG READY targets

| Version | Target SHA | Status |
|---|---|---|
| `v0.1.0` | `99b08a0b5fa1bec5921dc42e630c579a4e83c401` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.1` | `bada5bff803321427eb3c8eb1f3d159460ba5dd1` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.2` | `f69c52bf574212d1506df81abc7b15694abb7922` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.3` | `b4df4e911597d9f17bfa0a50b2057c24159dee9f` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.4` | `a798622f839b836f8b60f52dd700b8fd87147991` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.5` | `415de1f1dd42f70bd66992961cb43be7edba6ade` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.6` | `bfaf89c68daa656b7d75317f086458257cc94da9` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.7` | `423929ae1ff3fd7431260ffdab09810dc7105aa0` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.8` | `d34d471b20d4f5be865b0414a42240ec7f3061d9` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.9` | `fcfba651dbead9d035019e330f61986f5a1a60f7` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.10` | `c1e27d8367c490543e1d207f62d77f3bb5e8bc4e` | ACCEPTED / TAG READY / TAG NOT CREATED |
| `v0.1.11` | `fce9a3a2e56783206d63dbcac0d8a65e50008c10` | ACCEPTED / TAG READY / TAG NOT CREATED |

## v0.1.11 cumulative validation

```text
crypto_onchain focused        33 passed
accepted crypto regression   111 passed
full analysis               1151 passed
compileall                    PASS
git diff --check              PASS
```

No shared Worker/runtime contract was changed by C0-001..004, so Worker/typecheck was not an additional REL-11X gate.

## Next-session boundary

The current session stops after v0.1.11 acceptance. No tag creation is authorized by this document.

Next implementation start:

```text
v0.1.12
REL-12A / A0-018 / UWBS-105
Macro release Fact / consensus / prior / revision contract
```

REL-12A is intentionally deferred to a separate session.
