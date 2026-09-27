# UWBS-098 — MSTR 30-day option-implied-volatility normalization

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Scope

UWBS-098 defines a source-neutral contract for MSTR 30-day option-implied volatility.

The contract deliberately keeps MSTR equity-option IV distinct from BTC implied volatility even though the two will be compared later by UWBS-099.

## Accepted model boundary

The observation records:

- MSTR equity as the explicit underlying;
- exact 30-day horizon;
- annualized IV percent;
- normalized fractional representation;
- explicit provider/methodology lineage;
- Fact evidence lineage and provenance.

Supported methodology labels:

- `atm_option_surface`
- `delta_neutral_composite`
- `provider_composite`

## Non-goals

UWBS-098 does not infer:

- MSTR price direction;
- BTC price direction;
- MSTR/BTC IV differential;
- embedded leverage or NAV premium;
- Risk-On / Risk-Off regime;
- causal linkage between BTC and MSTR volatility.

Those interpretations belong to later tasks, especially UWBS-099.

No provider activation, paid procurement, Worker/Cron/D1 mutation, PB execution, or trading action is authorized by this implementation.
