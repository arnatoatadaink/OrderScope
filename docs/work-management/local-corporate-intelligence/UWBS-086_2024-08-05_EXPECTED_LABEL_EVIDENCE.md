# UWBS-086 — 2024-08-05 Historical Replay Expected-Label Evidence

Status: **INDEPENDENT LABEL EVIDENCE — REPLAY INPUT EXCLUDED**

Packet: `uwbs-086-2024-08-05-global-risk-off-v0.1`

Expected label:

```text
regime = risk_off
alert  = true
```

This file is deliberately separate from classifier-input evidence. The sources below are post-event institutional reviews used only to define the expected historical label; they must not be supplied as classifier inputs.

## BIS Bulletin 90

Source: Bank for International Settlements, *The market turbulence and carry trade unwind of August 2024*, published 2024-08-27.

The BIS identifies 5 August 2024 as the peak of the stress episode. It describes a sharp global volatility event amplified by deleveraging and margin pressure, with yen-funded carry trades among the positions forced to unwind. The Bulletin notes that TOPIX lost about 12% in one day and that the VIX reached levels not seen since the Covid-19 period.

For UWBS-086 this is independent evidence that the bounded episode contains a genuine cross-asset **Risk-Off** state and should generate an alert.

External source:
`https://www.bis.org/publications/bulletin-90-market-turbulence-and-carry-trade-unwind-august-2024`

## BIS Quarterly Review — September 2024

Source: Bank for International Settlements, *Carry off, carry on*, September 2024 Quarterly Review.

The BIS review characterizes the early-August episode as de-risking / carry-trade unwinding with sharp equity losses, yen appreciation and a VIX spike. It also emphasizes that the episode was short-lived and that markets subsequently returned toward the prior risk-on environment.

This source supports two acceptance expectations:

1. the packet window must contain a true positive Risk-Off episode rather than ordinary volatility;
2. the model should not interpret the event as a permanent regime change merely because the stress was extreme.

External source:
`https://www.bis.org/publications/qr-202409/carry-off-carry-on`

## Independence rule

Neither BIS source is referenced by any `classifier_input` source ID in the packet manifest. The manifest loader rejects use of `expected_label` sources inside classifier lanes and rejects classifier-input sources as expected-label evidence.

## Safe boundary

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action is authorized by this evidence record.
