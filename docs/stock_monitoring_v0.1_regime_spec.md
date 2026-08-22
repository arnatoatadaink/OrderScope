# Stock Monitoring Project v0.1 — Regime Engine仕様

## 1. 目的
企業を固定Sectorでのみ扱わず、事業構成・契約・CAPEX・売上・政策Exposure等の変化をRegimeとして時系列追跡する。

企業は複数Regimeを同時に保持可能。

## 2. Strength Type
- PROVISIONAL
- REVENUE_BASED

`strategic_strength` はv0.1では定量化しない。
売上に現れない内製技術・補完インフラ等はFact / Relationshipとして保持する。

## 3. Provisional Strength
### 0.25 — Emerging
- MVP
- pilot
- research
- feasibility
- evaluation
- small-scale trial

### 0.50 — Active Preparation
- new business unit
- dedicated organization
- financing
- CAPEX allocation
- facility conversion
- production preparation

### 0.75 — Commercial
- commercial contract
- major order
- customer agreement
- reported commercial revenue

Evidenceを単純加算しない。
原則として最も強いEvidenceを基準とする。

## 4. Revenue-based Strength
四半期セグメント売上が個別取得できる場合、Revenue-basedへ移行する。

MA4:
`MA4_i = mean(revenue_i for latest 4 quarters)`

Revenue Strength:
`strength_i = MA4_i / MAX(MA4_all_segments)`

Revenue Share:
`share_i = MA4_i / SUM(MA4_all_segments)`

最大事業は1.00。
複数事業が1.00近傍になることを許容する。

Latest Quarter Revenueも別途保持し、急変検知に利用する。

## 5. Confidence
Strengthとは別にEvidence Confidenceを保持する。

例:
```yaml
regime:
  type: ai_infrastructure
  strength: 0.75
  confidence: 0.98
```

## 6. Status
- EMERGING
- ACTIVE
- COMMERCIAL
- REVENUE_BASED
- INACTIVE
- REACTIVATING
- STALE

## 7. v0.1 Decay
対象: PROVISIONALのみ。

ルール:
- Supporting Evidenceが1年間ない場合 `strength × 0.5`
- 期間1年はv0.1固定
- Revenue-basedは時間減衰なし

例:
- 0.75 → 0.375
- 0.50 → 0.25
- 0.25 → 0.125

## 8. Contract Handling
契約期間が既知:
- effective_from / effective_untilを保持
- 契約履行中は単なるニュース欠如で減衰させない

契約期間が不明:
- Quarterly Earnings
- SEC
- Segment Revenue
- Management Disclosure
を優先して状態判定する。

売上未確認だけを理由に即減衰しない。
建設・設備転用・導入準備等が継続している場合は `CONTRACT_AWAITING_REVENUE` とする。

## 9. Negative Evidence
以下は明確な反証:
- contract cancelled
- project terminated
- business withdrawn
- business unit closed
- CAPEX withdrawn
- customer cancellation
- strategy abandoned

反証時:
`status = INACTIVE`

過去Strength / Evidenceは削除しない。

## 10. Reactivation
InactiveまたはDeclining Regimeに、
- policy tailwind
- major contract
- new customer
- successful product
- regulatory relief
- competitor exit
- commodity tailwind
等が出た場合:
`status = REACTIVATING`

ニュースだけでRevenue Strengthを書き換えない。

次回決算で売上回復が確認された場合:
REACTIVATING → ACTIVE / REVENUE_BASED

## 11. COMPANY_REGIME_CHANGE
Regimeは二値ではなくStrength Deltaで表す。

例:
```text
previous = 0.25
current  = 0.75
delta    = +0.50
```

この変化を `COMPANY_REGIME_CHANGE` Factとして保存する。

## 12. Strategic Relationship
売上額では補えないもの:
- proprietary chips
- internal AI infrastructure
- logistics
- proprietary data
- internal power
- vertical integration
- internal software/services

v0.1では数値化しない。

例:
```yaml
strategic_relationship:
  role: complementary_infrastructure
  supports:
    - cloud
    - ai_services
  evidence:
    - source_ref
```

## 13. Regime History
上書きせず履歴保存。

例:
```text
2025-Q1  0.25
2025-Q2  0.50
2026-Q1  0.75
2026-Q2  revenue_based
```

## 14. Future Research — v0.2+
以下のStage間期間を蓄積する。
- proposal
- research
- preparation
- invention
- pilot
- contract
- construction
- production
- sales
- revenue

目標:
`Expected Realization Time`

将来的に業界 / Realization Class別にDecay Start / Half-lifeを調整する。

候補Realization Class:
- software
- ai_model
- semiconductor_design
- semiconductor_manufacturing
- physical_infrastructure
- data_center
- energy
- mining
- biotech
- consumer_product

AIによって短縮しやすい工程と、建設・電力接続・規制・臨床試験等の物理/制度制約が強い工程を分離して扱う。
