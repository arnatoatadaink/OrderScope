# L1-003 / SMOKE-007 Phase B — market-session authorization template

Status: **TEMPLATE / NOT AUTHORIZED / DO NOT EXECUTE**

Complete the variable fields from fresh evidence. A blank or stale field means
no execution. See PB-09 preparation for candidate rules and the bounded envelope.

## Reviewed scope (fixed)

- Environment: live-canary; DB orderscope-state-live-canary /
  03c85865-1aa3-4b0c-b219-18987cd260a6.
- Equity 1Min REGULAR / stock:iex:raw; existing canary universe and priority.
- Cron unchanged, News disabled, retention unchanged, 2 jobs/tick, 100 bars/job,
  10 pages/job; shared ceilings 40 external and 40 D1 operations per invocation.
- Explicit shadow pause target 3 minutes, maximum 5; same active session.
- Maximum 16 normal scheduler opportunities after resume; immediately safe-close.
- One historical row repeat-read through accepted custody; no purge/schema/
  manual checkpoint updates, no Sep25 absence gate, no continuous live mode.
- Previously accepted PB and Phase A evidence inherited, not repeated.

## Fresh evidence to freeze before approval

| Input | Fresh value / evidence |
|---|---|
| Observation UTC/JST and freshness deadline | UNFROZEN |
| Release commit / clean-worktree receipt | UNFROZEN |
| Worker deployment/version / config hash | UNFROZEN |
| Official calendar revision, active open/close | UNFROZEN |
| Selected coverage key and candidate-selection rationale | UNFROZEN |
| Current checkpoint version, coverage/source frontier, state | UNFROZEN |
| Five competing checkpoint identities | UNFROZEN |
| Unresolved attempts and control_path_ok | UNFROZEN |
| Entry-acquisition authority/acceptance, if needed | UNFROZEN — separate authority |
| Earliest/latest allowed pause start inside session | UNFROZEN |
| Concrete guarded execution procedure/script and local test receipt | UNFROZEN |
| Safe-close mechanism and deployment receipt collection | UNFROZEN |

## Runtime receipt fields (filled only during authorized PB-10)

Record actual effective pauseStart, checkpoint_before_pause, pre-resume checkpoint,
resumeAt, frozen fresh gap, scheduled timestamps/job ranges, inserted/matched
records and version progression. The pause-entry checkpoint must exactly equal
the active finalized frontier; pre-resume identity must be unchanged. Capture
export repeat identity, control-path before/during/after and budget receipts.

The gap is derived from the actual boundaries, never copied from an example.
Failure requires shadow safe-close and a fresh assessment; no scope expansion.

## Explicit user authority (required)

Authorization timestamp/reference: **NOT RECEIVED**.

After all input fields and local execution review are complete, ask approval
naming L1-003 / SMOKE-007, the selected session/key/entry checkpoint, effective
pause limits, exact frozen export range, normal resume bound and shadow safe-close.
Do not treat approval of PB-08, preparation, or a separate entry-acquisition
window as approval of this Phase B window.
