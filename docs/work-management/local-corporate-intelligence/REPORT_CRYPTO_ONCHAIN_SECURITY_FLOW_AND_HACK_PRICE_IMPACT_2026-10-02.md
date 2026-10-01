# OrderScope — Crypto On-chain Security Flow / Hack Price Impact Research Report

Date: 2026-10-02
Status: Planning / WBS-unreflected input
Reference case: NEAR Intents security incident, 2026-10-01

## 1. Purpose

This report defines a proposed OrderScope extension for detecting abnormal on-chain outflows before or around public disclosure of a crypto security incident, and for measuring the subsequent market-price impact on the affected token.

The design preserves the existing boundary between Fact, Derived Metric, Interpretation, and Prediction. It must not label an abnormal transfer as a hack without independent confirmation.

## 2. NEAR Intents reference case

Observed working chronology from the current investigation:

- 2026-10-01 around 17:00 JST: NEAR price down and open interest down. This is consistent with profit-taking / long-position reduction and does not by itself identify a security incident.
- 2026-10-01 around 22:00 JST: NEAR price down while open interest increases. This is consistent with new short positioning entering after the earlier deleveraging phase.
- NEAR Intents later disclosed an estimated USD 3.8 million exploit/loss, attributed to an interaction between Omni deposit/withdrawal infrastructure and a NEAR Intents smart contract.
- Public reporting states that approximately USD 3.87 million USDT left a BNB Chain contract used by the system over roughly six hours.
- The contract-side vulnerability was reported as patched, affected users were promised full compensation, and the base NEAR blockchain was not reported as the compromised component.
- Several cross-chain deposit/withdrawal routes were temporarily suspended while repairs continued.

The reference case therefore supports a two-stage market interpretation candidate:

1. pre-incident-disclosure deleveraging / profit-taking phase; then
2. security-event-related short positioning / risk repricing phase.

This remains an interpretation until exact transaction timestamps, market microstructure data, and publication timestamps are joined in one event record.

## 3. Proposed architecture

### 3.1 On-chain Fact layer

Add provider-neutral facts such as:

- `OnChainTransferFact`
- `ProtocolWalletFact`
- `ProtocolComponentFact`
- `OnChainServiceStatusFact`
- `SecurityDisclosureFact`

Minimum transfer fields:

- chain
- tx hash
- block / confirmation timestamp
- source address
- destination address
- token / asset
- native amount
- USD notional at event time
- wallet role when known
- protocol / project association
- provenance and source confidence

### 3.2 Wallet / component registry

Project monitoring must be cross-chain rather than token-chain-only. A project such as NEAR Intents may rely on BNB Chain, Ethereum, Solana, bridge infrastructure, settlement wallets, hot wallets, and protocol contracts.

The registry should support:

- treasury wallet
- hot wallet
- settlement wallet
- bridge / intent contract
- protocol-owned contract
- known service-provider wallet
- unknown / unresolved relationship

Registry relationships must be evidence-backed and versioned.

### 3.3 Abnormal-flow Derived Metrics

Initial candidate metrics:

- 5m / 15m / 60m net outflow
- outflow / wallet balance
- outflow / 30-day median
- rolling z-score
- destination dispersion
- burst transaction count
- new-destination ratio
- stablecoin concentration
- cross-chain bridge transition count

Fixed USD thresholds should be treated as provisional calibration inputs, not normative constants.

### 3.4 Interpretation layer

Proposed states:

- `ONCHAIN_ABNORMAL_FLOW_CANDIDATE`
- `ONCHAIN_ABNORMAL_FLOW_CONFIRMED`
- `SECURITY_INCIDENT_CANDIDATE`
- `SECURITY_INCIDENT_CONFIRMED`
- `SECURITY_FLOW_SHOCK`
- `TREASURY_REBALANCE_CANDIDATE`
- `BRIDGE_REBALANCE_CANDIDATE`
- `UNKNOWN_FLOW_ANOMALY`

The system must not convert `ONCHAIN_ABNORMAL_FLOW_CANDIDATE` directly into `SECURITY_INCIDENT_CONFIRMED`.

### 3.5 Market confirmation layer

Join the on-chain event with existing / planned crypto-market observations:

- token return
- BTC-relative return
- open-interest delta
- funding-rate delta
- liquidation flow
- volume / CVD where available
- spot-vs-perpetual divergence

Useful interpretation examples:

- price down + OI down: deleveraging / long reduction candidate
- price down + OI up: new short positioning candidate
- abnormal on-chain outflow + price down + OI up: stronger security-event repricing candidate

These relationships remain interpretations, not causal facts.

## 4. Detection stages

### Stage A — confirmed transaction monitoring

Start from confirmed chain data:

`confirmed tx -> known protocol wallet/component -> abnormal-flow metric -> candidate event -> market confirmation`

This stage should be implemented and calibrated first because it is easier to reproduce and audit.

### Stage B — mempool / pre-confirmation warning

Later extension:

`pending tx -> early candidate -> block confirmation -> confirmed event`

Mempool monitoring can potentially detect suspicious transfers before news becomes common knowledge, but it increases provider cost, false positives, reorg handling, and operational complexity.

## 5. Historical hack / exploit price-impact dataset

### 5.1 Are existing news reports sufficient?

Existing news reports are sufficient for a discovery/index layer, but not for a quantitative price-impact dataset by themselves.

News can provide:

- incident name
- approximate incident date
- affected protocol / token
- reported stolen amount
- exploit category
- public disclosure time when available
- patch / compensation / recovery information

News usually does not reliably provide:

- exact first malicious transaction timestamp
- exact first public on-chain observability timestamp
- exact first social / official disclosure timestamp
- standardized pre/post price windows
- OI / funding / liquidation state
- BTC-relative abnormal return
- whether the affected token was directly compromised or merely ecosystem-adjacent

Therefore the research dataset should combine news / security reports with market and chain data.

### 5.2 Proposed event dataset schema

Per incident:

- project
- token
- incident class
- affected component
- chain(s)
- first malicious tx time
- first detectable abnormal-flow time
- service-pause time
- first researcher/social disclosure time
- first official disclosure time
- loss USD
- loss / TVL
- loss / market cap
- compensation promised / completed
- patch status
- funds recovered percentage
- base-chain compromised boolean
- token return at +15m, +1h, +6h, +24h, +48h, +5d, +30d
- BTC-relative abnormal return for the same windows
- OI delta
- funding delta
- liquidation amount
- recovery time to pre-event price, if achieved

### 5.3 Existing research baseline

Useful prior empirical baselines include:

- New York Fed staff research on DeFi hacks: substantial price discovery can occur before public disclosure; roughly 36% of the eventual 24-hour decline in its sample occurred before common-knowledge announcement.
- Information & Management (2026) event-study research covering 2020-2025 security breaches reports an average abnormal token-price decline of roughly 14% on the event day in its sample.
- Earlier 51% attack event studies found immediate token declines around 12-15% for the attacked cryptocurrencies.
- Immunefi / related hack-impact datasets report persistent post-hack underperformance in many historical cases; however these samples include incidents much more severe than the current NEAR Intents case and must not be directly applied as a NEAR forecast.

Research references:

- https://www.newyorkfed.org/research/staff_reports/sr1153
- https://www.sciencedirect.com/science/article/pii/S0378720626001370
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3290016
- https://immunefi.com/blog/research/what-an-onchain-hack-actually-costs-2024-2025-update/

Incident references:

- https://www.theblock.co/news/ecosystems/2026-10-01-near-intents-halts-services-after-3-8-million-exploit-promises-full-compensation-417404
- https://unchainedcrypto.com/near-intents-pledges-full-compensation-after-a-bug-lets-an-attacker-drain-3-8-million/

## 6. NEAR incident persistence assessment

This section is scenario analysis, not a measured forecast.

Factors limiting long-tail damage:

- reported loss is approximately USD 3.8M, small relative to NEAR ecosystem scale;
- the base NEAR blockchain was not reported as compromised;
- contract-side vulnerability was reported patched quickly;
- full compensation was promised;
- service restoration was expected relatively quickly for the core service;
- recent NRR / spot-ETF demand provides a separate structural demand channel.

Factors that can extend the decline:

- prolonged outage of affected deposit/withdrawal routes;
- uncertainty about reimbursement timing or funding source;
- evidence that the vulnerability scope is broader than first reported;
- a second exploit / repeat incident;
- meaningful NRR outflows rather than continued inflows;
- persistent price-down + OI-up behavior indicating continued new short accumulation;
- BTC/crypto market-wide risk-off occurring simultaneously.

Working scenario bands:

- Mechanical / positioning effect: approximately 24-72 hours.
- Residual security-risk premium: several days to roughly one week if operations normalize and no new findings appear.
- Multi-week impairment: should require new negative evidence such as wider vulnerability scope, incomplete compensation, continued service impairment, or repeated incidents.

These durations are provisional scenario bands only. They should be replaced by empirical distributions from the historical exploit dataset.

## 7. NEAR-specific interpretation to test

Working hypothesis for the 2026-10-01 event:

1. ETF-rally profit-taking / deleveraging begins first.
2. Around 17:00 JST, price down + OI down is consistent with long reduction.
3. Abnormal on-chain outflows may already be observable during this interval; exact first detection time is not yet resolved.
4. Around 22:00 JST, price down + OI up is consistent with new short positioning.
5. Security-incident disclosure / wider awareness may therefore have amplified an already-existing correction rather than creating the initial top.

Acceptance of this hypothesis requires minute-level replay using exact on-chain timestamps and derivatives data.

## 8. Proposed implementation order

1. Historical incident dataset design and NEAR fixture.
2. Protocol wallet/component registry.
3. Confirmed-transaction ingestion.
4. Abnormal-flow metrics and candidate-state machine.
5. Join with price / OI / funding / liquidation observations.
6. Historical calibration against multiple incidents.
7. Only after calibration, consider mempool early-warning support.

## 9. Acceptance criteria

The extension is ready for formal WBS incorporation when:

- NEAR Intents is reproducible as an event fixture with exact timestamp provenance;
- abnormal flows can be detected without labeling ordinary treasury movement as a hack;
- market response windows are BTC-relative and session-independent for 24/7 crypto;
- price/OI state changes can distinguish deleveraging candidates from new-short candidates;
- historical incidents produce a documented distribution of immediate and persistent drawdowns;
- Fact / Derived Metric / Interpretation boundaries remain explicit;
- no live trading action is authorized by the detector.
