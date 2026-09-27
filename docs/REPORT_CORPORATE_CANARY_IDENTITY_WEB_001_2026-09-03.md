# OrderScope — Corporate Canary identity registry調査（WEB-001）

Status: Web research complete; local registry implementation pending  
Web task: `WEB-001`  
Parent task: `W0-002`  
Registry proposal version: `corporate-canary-v0.1`  
Checked at: `2026-09-03T11:43:05Z`

## 1. 結論

Corporate CanaryをAMDとNVIDIAに固定するための外部identityを公式一次情報で確認した。

- AMD: legal name `ADVANCED MICRO DEVICES, INC.`、CIK `0000002488`、ticker `AMD`
- NVIDIA: legal name `NVIDIA CORPORATION`、CIK `0001045810`、ticker `NVDA`
- 両銘柄の対象securityは普通株であり、確認した年次報告書では`The Nasdaq Global Select Market`への登録が記載されている。
- 公式IR入口はAMDが `https://ir.amd.com/`、NVIDIAが `https://investor.nvidia.com/home/default.aspx` である。

本書の`instrument_id`はOrderScope内部registryに渡す設計提案であり、外部機関が発行した識別子ではない。CIK、ticker、legal name、security class、exchange、IR URLは外部事実として分離する。

## 2. Version付きregistry案

| registry_version | valid_from | valid_to | instrument_id（内部提案） | company_id（内部提案） | legal_name（公式表記） | security_class | ticker | registered_exchange | CIK | official_ir_url |
|---|---|---|---|---|---|---|---|---|---|---|
| `corporate-canary-v0.1` | `2026-09-03` | open | `us-sec-0000002488-common` | `sec-cik-0000002488` | Advanced Micro Devices, Inc. | Common Stock, $0.01 par value per share | `AMD` | The Nasdaq Global Select Market | `0000002488` | https://ir.amd.com/ |
| `corporate-canary-v0.1` | `2026-09-03` | open | `us-sec-0001045810-common` | `sec-cik-0001045810` | NVIDIA Corporation | Common Stock, $0.001 par value per share | `NVDA` | The Nasdaq Global Select Market | `0001045810` | https://investor.nvidia.com/home/default.aspx |

### 内部IDの判断

- `instrument_id`は現在tickerだけを主キーにせず、zero-padded CIKとsecurity classを材料にした不変候補とする。
- ticker、exchange、IR URLは変更可能なalias/source属性として有効期間を別管理する。
- 上表はschema実装ではない。`I0-001`でuniqueness、rename、複数share class、merge等の履歴意味論を確定する。
- legal nameの大文字小文字はSEC表示の差を正規化している。原文表示はEvidence欄を正とする。

## 3. Evidence

| Source title | Publisher / actor | Canonical URL | Checked at | Effective/version date | Evidence class | Extracted fact | Unknowns | Local consequence |
|---|---|---|---|---|---|---|---|---|
| AMD Form 10-K/A filing detail, accession `0000002488-26-000021` | U.S. Securities and Exchange Commission / Advanced Micro Devices, Inc. filer | https://www.sec.gov/Archives/edgar/data/2488/000000248826000021/0000002488-26-000021-index.htm | 2026-09-03T11:43:05Z | filed 2026-02-04; period 2025-12-27 | official data | Filer CIKは`0000002488`。filer表示は`ADVANCED MICRO DEVICES INC`。 | CIKの将来変更は想定しないが、組織再編時の扱いはI0-001で定義が必要。 | CIK/submissions adapterのCanary keyにzero-padded CIKを渡す。 |
| AMD Form 10-K/A cover | U.S. Securities and Exchange Commission / Advanced Micro Devices, Inc. filer | https://www.sec.gov/Archives/edgar/data/2488/000000248826000021/amd-20251227.htm | 2026-09-03T11:43:05Z | fiscal year ended 2025-12-27 | official data | legal name、common stock class、ticker `AMD`、The NASDAQ Global Select Marketを確認。 | 本書では過去ticker履歴を調査していない。 | instrumentとticker aliasを分離し、tickerに有効期間を持たせる。 |
| AMD Investor Relations | Advanced Micro Devices, Inc. | https://ir.amd.com/ | 2026-09-03T11:43:05Z | 記載なし | official data | IR入口。Financial Results、SEC Filings、News & Eventsへの公式導線がある。 | archive URLの長期安定性、redirect、削除・更新挙動は未確認。 | E0-003のIR fallback入口候補。`WEB-008`でstable URLを別途評価する。 |
| NVIDIA Form 10-K filing detail, accession `0001045810-26-000021` | U.S. Securities and Exchange Commission / NVIDIA Corporation filer | https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/0001045810-26-000021-index.htm | 2026-09-03T11:43:05Z | filed 2026-02-25; period 2026-01-25 | official data | Filer CIKは`0001045810`。filer表示は`NVIDIA CORP`。 | CIKの将来変更は想定しないが、組織再編時の扱いはI0-001で定義が必要。 | CIK/submissions adapterのCanary keyにzero-padded CIKを渡す。 |
| NVIDIA Form 10-K cover | U.S. Securities and Exchange Commission / NVIDIA Corporation filer | https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm | 2026-09-03T11:43:05Z | fiscal year ended 2026-01-25 | official data | legal name、common stock class、ticker `NVDA`、The Nasdaq Global Select Marketを確認。 | 本書では過去ticker履歴を調査していない。 | instrumentとticker aliasを分離し、tickerに有効期間を持たせる。 |
| NVIDIA Investor Relations | NVIDIA Corporation | https://investor.nvidia.com/home/default.aspx | 2026-09-03T11:43:05Z | 記載なし | official data | IR入口。Financial Reports、SEC Filings、Quarterly Results、Newsへの公式導線がある。 | archive URLの長期安定性、redirect、削除・更新挙動は未確認。 | E0-003のIR fallback入口候補。`WEB-008`でstable URLを別途評価する。 |

## 4. 対象境界

Corporate Canaryに含めるもの:

- AMDの普通株instrumentと対応するcorporate identity
- NVIDIAの普通株instrumentと対応するcorporate identity
- 各社のSEC filer identityおよび公式IR入口

Corporate Canaryに含めないもの:

- `SPY`、`QQQ`: ETFであり、企業CIK・segment revenue・企業RegimeのCanary対象に混ぜない。
- `BTCUSD`: cryptoであり、corporate identity対象に混ぜない。
- ADR、option、bond、別share class: 今回の公式確認とregistry案の対象外。
- 過去ticker履歴、M&A後のsuccessor/predecessor関係: `I0-001`の履歴設計で扱う。

## 5. Handoff

### I0-001 source/entity registry

次のrecordを分離して実装する。

1. company entity: internal company ID、CIK、legal name、有効期間
2. instrument entity: internal instrument ID、security class、有効期間
3. listing/ticker alias: ticker、exchange、有効期間、Evidence
4. official source: IR入口URL、owner、source type、確認時刻、有効期間

`instrument_id`の提案値は実装前review対象とし、ticker変更でIDが変わらないこと、複数share classを誤統合しないことをcontract testにする。

### S0-002 CIK/submissions adapter

- AMD: `CIK0000002488`
- NVIDIA: `CIK0001045810`
- CIKは10桁zero-paddingを保持する。
- SEC endpoint・User-Agent・Fair Access条件は`WEB-005`の確認結果を待ち、ここでは接続条件を確定しない。

### E0-003 IR fallback

IR入口は確認済みだが、release/archiveのstable URL、pagination、更新・削除挙動は未確認である。`WEB-008`が完了するまでfallback adapterの取得仕様を確定しない。

## 6. 未解決事項

- `instrument_id`の正式なschema、命名規則、uniqueness制約は`I0-001`で未実装。
- historical ticker、旧法人、successor/predecessorの履歴は未調査。
- IR release/archive URLの永続性は未確認（`WEB-008`）。
- SEC接続条件と自動取得時の運用制約は未確認（`WEB-005`）。
- Web確認のみであり、endpoint取得、redirect、parser、idempotencyのローカル実測は行っていない。
