# L1-003 / SMOKE-007 PB-10 combined window authorization

Status: **TEMPLATE / NOT AUTHORIZED / DO NOT EXECUTE**.

This replaces the earlier two-approval proposal for a single same-session
window. One explicit approval may cover conditional checkpoint catch-up and
Phase B, within the fixed limits below. The script decides from fresh evidence
whether catch-up is needed and whether Phase B may start. Approval of this
template is not inferred from prior PB-08 or PB-09 preparation.

## Fixed scope

- Environment: live-canary; D1 `orderscope-state-live-canary` /
  `03c85865-1aa3-4b0c-b219-18987cd260a6`.
- Existing equity 1Min REGULAR IEX canary universe and priority, one active
  official REGULAR session. Cron, News-disabled policy, retention and budget
  configuration unchanged. No temporary control route, absence evidence,
  manual checkpoint update, schema change or historical campaign replay.
- If needed, maximum 16 observed normal scheduler opportunities to produce a
  current candidate. Restore checked-in shadow before the pause. If no
  candidate, close in shadow without proceeding.
- Phase B: shadow pause target three minutes, hard maximum five, entirely
  inside the same session; frozen one-row historical repeat-read; normal
  scheduler resume for at most 16 observed opportunities; restore checked-in
  shadow immediately on success or any failure.
- Every digest must stay within 40 external and 40 D1 operations, two jobs per
  tick, 100 bars and 10 pages per target job. A successful target job plan,
  attempt and accepted bar receipt must explain every minute of the frozen gap
  and any further checkpoint progression.
- Driver: `scripts/l1_003_pb10_combined_window.py`. It requires `--execute`
  and `--authorization-id`; without `--execute` it makes no remote calls.
  The authorization ID is an operator receipt, so execution must still be
  preceded by explicit user approval of this exact bounded scope.
- A same-session continuation after a safe stop must use a fresh read-only
  packet and `--entry-opportunities-limit` set to **16 minus already observed
  entry opportunities**. A new market session is outside this authority.

## Fresh inputs to freeze before single approval

| Input | Value / evidence |
|---|---|
| Active session date, open/close, calendar revision | UNFROZEN |
| Fresh read-only packet path and observation UTC/JST | UNFROZEN |
| PB branch commit, clean worktree, remote parity | UNFROZEN |
| Worker deployment/version and config hash | UNFROZEN |
| Five checkpoint versions, coverage/source frontiers and states | UNFROZEN |
| Unresolved attempts, control route 404 and health | UNFROZEN |
| Initial candidate or conditional catch-up need | UNFROZEN |
| Execution log path, operator and authorization reference | UNFROZEN |

The candidate and exact fresh gap cannot be copied from a closed-market packet.
The driver freezes them from observations inside the approved session. Any
missing input, unsafe baseline, stale candidate, changed checkpoint during the
pause, overlong pause, failed repeat-read, unclean attempt, budget breach,
unexplained minute, session close or exhausted opportunity bound stops the
window and restores shadow. A failed attempt is not authorization to retry in
another session.

After the single approval, run from the clean PB branch with working Node,
Wrangler and Cloudflare credentials (replace the reference and log path):

```bash
set -o pipefail
export PATH=/home/y/.nvm/versions/node/v24.21.0/bin:$PATH
export CLOUDFLARE_ENV=live-canary
export ORDERSCOPE_PB09_CUSTODY_DIR=/path/to/accepted/l1-003-smoke-007-20260915
PYTHONDONTWRITEBYTECODE=1 python3 scripts/l1_003_pb10_combined_window.py \
  --execute --authorization-id '<approved-reference>' \
  2>&1 | tee /tmp/orderscope-pb10-combined-<session>.log
```

Keep the generated read-only packet, export receipt directory and full run
log. If the process stops, verify health and D1 state before a same-session
continuation and decrement the remaining entry bound. Never reuse an old
packet or expand the 16/16 aggregate limits.
The driver checks the accepted local Phase A custody bytes and manifest before
any deployment; this directory may be outside an isolated Git worktree.

## Local review

Before an approval request: run Python acceptance tests, PB-09 packet tests,
the driver without `--execute`, shell/source checks and review the exact
script diff. Record the result here. A remote dry-run deploy may be done with
the checked-in temporary config before execution; it must not deploy.

Local acceptance on Sep 28: **PASS for preparation**. The Python receipt tests
cover exact gap plus later progression, missing accepted minute, failed attempt
and absent observed job plan. The driver invokes the canonical PB-09 candidate
rule in the local test. PB-09 packet tests pass; the driver without `--execute`
prints a dry-run notice without remote calls; missing authorization ID is
rejected before any remote call. The temporary config passed Wrangler
`deploy --dry-run`: live-canary D1 binding, IEX, News disabled, false absence
gate, unchanged two jobs / 100 bars / 10 pages, and no deployment. Python
syntax and `git diff --check` pass. The authorized live path has not run.

## Explicit authority

Authorization timestamp/reference: **NOT RECEIVED**.

Suggested single approval wording after the fresh fields are filled:
"Approve the L1-003 / SMOKE-007 PB-10 combined live-canary window for [session]:
conditional current checkpoint catch-up up to 16 normal scheduler
opportunities, then Phase B only when the script verifies its current entry;
shadow pause target three and maximum five minutes, frozen export repeat-read,
resume up to 16 normal opportunities, and immediate shadow safe-close on any
stop."
