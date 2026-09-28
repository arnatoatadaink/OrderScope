# PB-10 BTCUSD Sunday activity review (read only)

Observed 2026-09-28 UTC. All times below are UTC, and provider data is Alpaca `crypto:us` BTC/USD, not a global BTC/USD consolidated market.

2026-09-27 was Sunday. The six missing 1-minute bars were 17:41, 17:44, 17:54, 18:01, 18:04, and 18:14. Re-reading the historical bars endpoint for 17:30–18:50 returned 73 bars, no next page, and the same six absences within the frozen 17:41–18:38 interval. For each missing minute, separate historical quotes and historical trades endpoint reads returned zero records and no next page. This supports an Alpaca venue activity/quote gap, not proof of a global BTC market halt or an API defect.

| Date | Day | 17:41–18:38 expected minutes | Bars | Zero-volume bars | Positive-volume bars | Volume (BTC) | Trade count |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-24 | Thu | 57 | 57 | 41 | 16 | 0.036415335 | 20 |
| 2026-09-25 | Fri | 57 | 57 | 42 | 15 | 0.013453920 | 18 |
| 2026-09-26 | Sat | 57 | 41 | 26 | 15 | 0.027073227 | 25 |
| 2026-09-27 | Sun | 57 | 51 | 31 | 20 | 0.002713183 | 24 |

Sunday volume in this window was roughly one fifth of Friday's and one thirteenth of Thursday's, though Saturday volume shows that weekend activity is variable. Zero-volume bars on all days show that lack of trades alone does not determine whether Alpaca emits a bar; Alpaca documents quote midpoint prices in zero-trade crypto bars. In the six absent Sunday minutes, no quotes were returned either. The minute immediately before/after the six gaps had volume (BTC) respectively: 0/0.000935; 0/0; 0.000064/0.000064; 0/0.000123; 0/0; 0/0.

At this UTC time on a weekday in late September, US equities' NYSE core session would be open (13:41–14:38 EDT, inside 09:30–16:00 EDT). On Sunday it was closed. Alpaca crypto trading is available 24/7, so the absence is not a scheduled crypto market closure. Since 2026-05, CME cryptocurrency futures also list 24/7 trading subject to maintenance, but that separate futures market does not establish whether Alpaca spot quotes/trades must exist in each minute.

Disposition: retain BTCUSD as a separate PARTIAL checkpoint and do not synthesize zero-volume bars or advance the checkpoint solely on this review. The six reproducible provider absences can be considered for the existing explicit absence-acknowledgement procedure, with exact baseline and policy checks, if BTCUSD is brought back into the five-symbol acceptance scope.
