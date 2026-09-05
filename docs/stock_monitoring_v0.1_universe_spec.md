# Stock Monitoring Project v0.1 — Universe / 銘柄選定仕様

## 1. 基本方針
- 対象市場は米国
- 海外比較は米国上場Country ETF Proxy
- 初期Universeは約100 instrumentsで固定
- Universeと価格取得頻度を分離
- 企業Tickerは原則Regime Tracking対象
- ETF / Country Proxyは原則Regime Tracking対象外
- Theme / Character / Regimeはmany-to-many

## 2. Tier A — 1 minute
### Market / Benchmark
- SPY
- QQQ
- IWM
- RSP

### Sector Reference
- XLK
- XLF
- XLE
- XLI
- XLU

### AI Compute
- NVDA
- AMD
- AVGO
- CBRS

### AI Infrastructure
- VRT
- ANET
- CEG
- VST

### Hyperscaler
- MSFT
- GOOGL
- AMZN
- META

### Crypto / Regime-sensitive
- MSTR
- RIOT
- COIN
- BTCUSD

## 3. Tier B — 15 minute
### Remaining Sector ETFs
- XLC
- XLY
- XLP
- XLV
- XLB
- XLRE

### Semiconductor / AI Supply Chain
- MRVL
- INTC
- TSM
- ASML
- AMAT
- LRCX
- KLAC
- MU
- ARM

### Semiconductor Materials
- ENTG
- Q
- MKSI
- MTRN

### Datacenter / Power / Infrastructure
- ETN
- PWR
- GEV
- NEE

### Crypto / Mining / HPC Transition
- MARA
- CLSK
- CORZ
- IREN
- CIFR

## 4. Tier C — Daily
### Country Proxy
- EWJ
- EWU
- EWG
- EWC
- EWA
- MCHI
- EWT
- EWY
- INDA
- EWZ
- EWW

### Macro / Cross Asset
- TLT
- IEF
- HYG
- LQD
- GLD
- SLV
- USO
- ETHUSD

### Software
- ORCL
- PLTR
- CRM
- NOW
- SNOW

### Storage
- WDC
- STX
- SNDK

### Crypto Financial
- HOOD

### Financial
- JPM
- BAC
- GS
- SCHW
- COF

### Industrial / Real Economy
- CAT
- DE
- UPS
- FDX
- UNP

### Defense
- LMT
- RTX
- NOC
- GD

### Energy / Materials
- XOM
- CVX
- FCX
- NEM

### Consumer
- WMT
- COST
- HD
- TSLA

### Healthcare
- LLY
- UNH
- MRNA

## 5. 主Theme
- AI Compute
- Semiconductor Manufacturing
- Semiconductor Materials
- Memory / Storage
- Datacenter / Network
- Hyperscaler
- AI Software
- Datacenter Power
- Crypto Treasury
- Crypto Exchange / Financial Infrastructure
- Crypto Mining / HPC Transition

## 6. 特殊企業Character
- Asset Proxy
- Digital Asset Treasury
- Policy Sensitive
- Interest-rate Sensitive
- Commodity Sensitive
- Capital-market Dependent
- AI Infrastructure
- Data Center Operator
- Power Capacity Holder
- Cyclical
- Binary-event Biotech
- Highly Speculative Growth

## 7. Universe更新
v0.1では初期Universeを固定し、自動追加はしない。

将来候補Fact:
- 既存監視企業との相関構造急変
- 新規大口契約
- 新事業立上げ
- AI / HPC / Power / Cryptoへの転換
- 新規上場
- 政策変更によるExposure急増
- 既存テーマ代表性の喪失

## 8. Instrument例
```yaml
RIOT:
  asset_type: equity
  cadence:
    price: 1m
    corporate_event: event
    filing: event
    fundamental: quarterly
  themes:
    - crypto
    - bitcoin_mining
    - power_capacity
    - data_center
    - ai_hpc
  regime_tracking: true

EWJ:
  asset_type: etf
  cadence:
    price: 1d
  roles:
    - country_proxy
  represented_country:
    - JP
  regime_tracking: false
```
