# PB-10: 2026-09-28 equity-only continuation

## Scope and result

The user directed validation with symbols other than BTCUSD and without a 2026-09-02 historical replay. The temporary live canary universe contained AMD, NVDA, QQQ, and SPY. The previously frozen QQQ Phase B gap was `[2026-09-28T13:49:00.000Z, 2026-09-28T13:52:00.000Z)`, three fresh one-minute bars. No new pause or historical recovery control was used.

The bounded continuation ran under `user-2026-09-29-equity-excluding-BTCUSD` from release `07d5df23ac7e4aaee65cd05c4ade4303a7afe8a7`. Two normal scheduler opportunities were used, both with two successful summaries. On the second tick, QQQ advanced from v17 through 13:49Z to v18 through 15:28Z. Job `market-bars:ac736a941bbf6be4` had a successful, clean acquisition attempt and INSERTED/MATCHED receipts for every minute in `[13:49Z, 15:28Z)`, including the three frozen gap minutes. The job stayed within 100 bars and 10 pages.

The checked-in shadow configuration was redeployed at 15:54:52Z; safe close completed at 15:55:00Z. A separate read-only check at 15:55:15Z confirmed Worker shadow, IEX, News disabled, temporary controls closed, and zero unresolved acquisition attempts. Final equity checkpoints were COMPLETE: AMD v50 through 15:23Z, NVDA v67 through 15:23Z, QQQ v18 through 15:28Z, and SPY v50 through 15:32Z.

BTCUSD was excluded from the temporary scheduler universe. Its checkpoint remained PARTIAL v59, complete through 2026-09-27T17:41:00.000Z, with the same six missing one-minute ranges. BTCUSD acquisition attempts since 15:00Z remained zero at safe close and in the subsequent read-only check. Its gap requires separate disposition; this acceptance applies to the equity-only Phase B continuation.

## Implementation and checks

`src/universe.ts` adds the temporary `canary-equity-v0.1` profile. `scripts/l1_003_pb10_equity_resume_window.py` checks exact baseline identities, market session, shadow controls, scheduler budgets and attempts, QQQ receipts, BTCUSD immutability, and shadow safe close. The script requires `--execute`, an authorization id, and a bounded opportunity count. It leaves the checked-in `wrangler.jsonc` in shadow.

Local checks passed: Python guard tests, `src/universe.test.ts`, TypeScript typecheck, and `git diff --check`. The market calendar came from Alpaca. The final live deployment version was `25e295dc-9a6c-43ac-beec-d4900a0447c2`; the shadow version was `efef9f2c-4ba9-4b5e-890d-947b46519b02`.
