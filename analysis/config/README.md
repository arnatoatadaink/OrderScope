# Local analysis configuration

`analysis/config` contains non-secret local configuration guidance only. Machine-specific values and credentials must not be committed.

## Environment variables

Non-secret configuration:

- `ORDERSCOPE_DATA_ROOT` — mutable local data root. Operational WSL runs should point this to a WSL-native filesystem location; tests use temporary directories.
- `ORDERSCOPE_LOG_LEVEL` — one of `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`.
- `ORDERSCOPE_SEC_USER_AGENT` — SEC identification string. This is configuration, not a credential.

Registered secret variables:

- `ORDERSCOPE_SECRET_ALPACA_API_KEY`
- `ORDERSCOPE_SECRET_ALPACA_API_SECRET`

All future OrderScope credential names must use the `ORDERSCOPE_SECRET_` prefix and must be explicitly registered before an adapter reads them.

## Local-only credential procedure

1. Set credentials only in the local WSL process environment or a local shell/session mechanism that is excluded from Git.
2. Do not place credential values in `analysis/config`, committed dotenv files, CLI arguments, test fixtures, dumps, API responses, or generated manifests.
3. Provider adapters read only their explicitly registered credential variable at the point of use. Secret values are not stored in `LocalConfig`.
4. Logging/diagnostic code must use the config-safe projection or the environment redaction helper; every `ORDERSCOPE_SECRET_*` value is redacted.
5. Tests use synthetic credential values and must never read the operator environment.

`orderscope_local.config` implements this boundary. It deliberately does not load a committed secrets file or expose credentials through the HTTP application.
