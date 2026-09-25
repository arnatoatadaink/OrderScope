# OrderScope — L1-003 PB-08 Complete Script Git Audit

Status: **BLOCKED ON EXECUTION SCRIPT — Git contains only a skeleton**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## Request and result

The local handoff asks for the complete PB-08 frontier catch-up change-window
script to replace `scripts/l1_003_pb08_frontier_catchup_change_window.sh`.
The operator could not locate that complete file. A check of the local file
system, all fetched Git refs and the path history found no complete equivalent.
The repository contains only a six-line, deliberately non-executable skeleton.
No replacement or remote catch-up was performed during this audit.

## Git evidence

- `git log --all --name-status -- scripts/l1_003_pb08_frontier_catchup_change_window.sh`
  shows one addition: `9cd8a21 Add PB-08 frontier catch-up script skeleton`.
  There is no later commit modifying that path.
- The file prints `This script is not complete; do not execute.` and exits 2.
- `git ls-tree -r --name-only HEAD scripts` contains no other PB-08
  change-window execution script.
- The PB-08 commits on the fetched refs provide planning tests, preflights,
  acceptance documents and the skeleton, but no complete runtime script.

## Existing components

| File | What it provides | Limit |
| --- | --- | --- |
| `scripts/l1_003_pb07_change_window.sh` | Prior bounded live scheduler observation, D1 checks, digest polling, final evidence checks and Shadow restoration | Frozen to PB-07's two September 23 jobs and v59→v61; not a PB-08 substitute |
| `scripts/l1_003_pb08_fresh_remote_preflight.sh` | Read-only live baseline, checkpoint, competition and attempt snapshot | Does not run the catch-up |
| `scripts/l1_003_pb08_entry_packet_preflight.sh` | Read-only entry-packet checks | Does not run the catch-up |
| `scripts/l1_003_pb08_local_acceptance.sh` and `src/pb08-frontier-*.test.ts` | Local planning and regression checks | Do not validate a complete PB-08 runtime script |

## Handoff implications

The handoff's statement that a complete script was generated outside GitHub
does not identify a retrievable file path. A filename search in the repository,
`/tmp`, and the local user's Downloads, Desktop, Documents, Projects and
`.codex` directories found no other PB-08 script. This does not establish
whether the text exists in an earlier Web session; it establishes that it is
not available as a file in the checked locations or in fetched Git history.

PB-08's frozen v61→v65 four-job plan is a September 25 snapshot. Before any
runtime execution, the script and operator must recheck the exact remote
entry and normal retention window. If the September 24 Regular open is no
longer retained, the handoff's acceptance conditions cannot be met as written.

## Requested Web-side resolution

1. If the complete script exists in the Web session, publish its full contents
   to the repository path above and provide the commit ID.
2. Otherwise, implement the PB-08 change-window script using the PB-07
   operator script as a reference, with the PB-08 four-step and 16-opportunity
   bounds and all handoff stop and Shadow-restoration checks.
3. Re-freeze the remote entry and retained session before scheduling execution;
   update the packet if the original frozen plan is stale.
4. Run shell syntax and local acceptance checks before requesting execution.

This audit does not authorize PB-09, PB-10 or Phase B pause/resume. The
handoff's bounded PB-08 authority and stop conditions remain the reference.
