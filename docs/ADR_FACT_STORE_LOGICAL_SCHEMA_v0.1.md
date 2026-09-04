# OrderScope — Fact Store Logical Schema ADR v0.1

Status: Proposed; acceptance pending I0-002 provenance types and contract fixtures
Date: 2026-09-04
Decision ID: `ADR-FACT-STORE-001`
Work item: `I0-005`

## 1. Scope

The Fact Store is the common logical persistence boundary for Market, Corporate and
Policy information. It stores observations and their support without turning derived
calculations or interpretation into observed facts.

This ADR fixes the logical records and invariants. It does not select SQLite table
layout, ORM, API paths, provider adapters, news-body retention implementation, or
Prediction storage. Those remain implementation decisions downstream.

The five records in this contract are distinct:

`Fact`, `Evidence`, `Relationship`, `DerivedMetric`, and `Interpretation`.

`Prediction` is intentionally outside this contract. A prediction and its realized
label must not be written as a Fact; a later realized label is a separate
`DerivedMetric` linked to the prediction by an explicit reference.

## 2. Record envelopes

### 2.1 Base record

Every record has the following identity and Store audit fields:

| Field | Meaning | Rule |
|---|---|---|
| `record_id` | Immutable UUID/UUID-like internal identifier | Never reused; stable across reprocessing |
| `record_type` | `fact`, `evidence`, `relationship`, `derived_metric`, or `interpretation` | Fixed by the record shape |
| `schema_version` | Version of this logical record | Required; additive changes require a new version |
| `subject_ref` | Internal entity/instrument/source reference | Must resolve in the source/entity registry when applicable |
| `accepted_at` | When validation accepted the record into the Store | Required; UTC |
| `created_at` | Local record creation time | Required; UTC |
| `supersedes_record_id` | Previous logical assertion replaced by this record | Nullable; history is append-only |

`record_id` generation and duplicate/update/conflict classification are finalized by
I0-004. Until then, this ADR requires stable identity semantics but does not prescribe
random UUIDs or a deterministic-ID algorithm.

### 2.2 Source provenance

Facts, Evidence and source-grounded Relationships additionally carry source
provenance. DerivedMetric and Interpretation records do not fabricate these fields;
their provenance is represented by explicit input/basis record references.

| Field | Meaning | Rule |
|---|---|---|
| `source_ref` | Canonical source or provider reference | No provider response body is embedded |
| `source_revision` | Provider/source revision or retrieval batch | Nullable only when the source has no revision concept |
| `content_hash` | Hash of the normalized source assertion or input payload | Used for idempotency and change detection |
| `event_time` | When the represented event occurred or is scheduled to occur | Nullable only when the source does not establish it; distinct from observation/publication |
| `observed_at` | When the source says the assertion was true/observed | Nullable when the source provides no such time |
| `published_at` | Source publication time | Nullable when not applicable or unknown |
| `filed_at` | Official filing time | Nullable when not applicable or unknown; never collapsed into `published_at` |
| `retrieved_at` | When OrderScope obtained the source | Required for acquired external records |
| `available_at` | Earliest time the source information could be consumed without look-ahead | Required for acquired external records |

Timestamps are UTC, RFC 3339 values with an explicit offset (normally `Z`). Unknown
external times remain null or an explicit unknown state; `retrieved_at` and
`accepted_at` must not be backfilled into an unknown event time, publication time or
filing time. Timestamp precision and source-reported timezone are supplied by I0-002.

## 3. Logical records

### 3.1 Fact

`Fact` is a source-grounded assertion about a subject at a point or interval.

Required fields beyond the base record and source provenance:

| Field | Meaning |
|---|---|
| `fact_type` | Versioned domain type, for example `filing_submitted`, `revenue`, `contract_announced`, `policy_implemented`, or `company_regime_change` |
| `value` | Typed scalar/object value; no untyped prose-only numeric coercion |
| `unit` | Currency, shares, percent, count, or other declared unit; nullable for non-quantitative facts |
| `period_start` | Start of the period to which the value applies; nullable when not applicable |
| `period_end` | End of the period to which the value applies; nullable when not applicable |
| `assertion_kind` | `observation`, `correction`, `amendment`, `withdrawal`, or `pending_review` |
| `extraction_confidence` | Extractor confidence when extraction was performed; nullable otherwise and separate from Evidence quality and regime strength |

Facts are immutable assertions. A correction, amendment, withdrawal, or revised
extraction creates a new record and points to the prior record with
`supersedes_record_id`; the prior row remains queryable. Current/effective status is
derived from the supersession chain and `assertion_kind`, never updated in place on a
prior Fact.

### 3.2 Evidence

`Evidence` records the durable support or contradiction for one or more records. It
may point to a permanent filing/source URL or to a temporary content reference. It
does not duplicate the entire provider response or news body.

Required fields beyond the base record and source provenance:

| Field | Meaning |
|---|---|
| `evidence_kind` | `supporting`, `contradicting`, `context`, or `extraction_span` |
| `target_record_ids` | One or more Fact/Relationship/DerivedMetric/Interpretation IDs |
| `locator` | Stable URL, accession/document reference, or bounded span locator |
| `excerpt_hash` | Hash of the cited normalized span, when a span exists |
| `quality_class` | `tier_1_official`, `provider`, `secondary`, or `unclassified` |
| `retention_class` | `durable_metadata`, `temporary_success`, or `temporary_exception` |

Evidence may be retained after temporary content deletion as metadata and hash. A
temporary body reference, expiry, deletion proof, and exception reason belong to the
I0-006 lifecycle contract.

### 3.3 Relationship

`Relationship` expresses an explicit, typed edge between two entities or records. It
is not a numeric metric and must not be inferred solely from co-occurrence.

Required fields beyond the base record, plus source provenance for externally asserted
relationships:

| Field | Meaning |
|---|---|
| `relationship_type` | Versioned type such as `issuer_of`, `partner_of`, `supplier_of`, `theme_related_to`, or `supports` |
| `from_ref` | Origin entity or record reference |
| `to_ref` | Target entity or record reference |
| `direction` | `directed` or `undirected` |
| `valid_from` | External validity start; nullable when unknown |
| `valid_to` | External validity end; nullable when unknown |
| `assertion_kind` | `assertion`, `correction`, `termination`, `contradiction`, or `pending_review` |

Strategic relationships that do not appear as revenue remain Relationships. Their
existence does not imply a quantitative `strategic_strength`. Corrections and endings
are new append-only records linked through `supersedes_record_id`; effective state is
derived rather than written back to an earlier Relationship.

### 3.4 DerivedMetric

`DerivedMetric` is deterministically calculated from versioned input records or
datasets. It must declare its method and all inputs needed for reconstruction.

Required fields beyond the base record:

| Field | Meaning |
|---|---|
| `metric_name` | Versioned metric identifier |
| `value` | Typed result |
| `unit` | Declared result unit; nullable only when the metric is unitless |
| `calculation_method` | Human-readable method identifier |
| `method_version` | Code/contract version |
| `input_record_ids` | Complete input-record lineage; may be empty only when dataset lineage is complete |
| `input_dataset_refs` | Complete versioned dataset lineage; may be empty only when record lineage is complete |
| `as_of` | Cutoff at which the calculation is valid |

Changing an input, method, or registry revision creates a new DerivedMetric record;
it never mutates the old result.

### 3.5 Interpretation

`Interpretation` is a qualified human or rule-based assessment over Facts,
Relationships, Evidence, or DerivedMetrics. It is not a source assertion.

Required fields beyond the base record:

| Field | Meaning |
|---|---|
| `interpretation_type` | Versioned assessment type |
| `statement` | Assessment text or structured assessment |
| `basis_record_ids` | Records supporting the assessment |
| `method` | Human, rule, or model provenance |
| `method_version` | Version of the rule/model/process; nullable only for explicitly identified human authorship |
| `assertion_kind` | `assessment`, `revision`, `rejection`, or `expiration` |

Interpretations must preserve their basis and assessment time. A revision, rejection
or expiration is a new record linked with `supersedes_record_id`; it cannot overwrite
the prior Interpretation or the Fact that motivated it. Regime strength, extraction
confidence and Evidence quality remain separate fields/concepts.

## 4. Invariants and acceptance tests

The first implementation must reject or flag records that violate any of these rules:

1. Every non-pending source-grounded Fact and externally asserted Relationship has at
   least one Evidence reference. Registry-internal structural edges must identify
   their registry assignment as basis and cannot masquerade as an external assertion.
2. A record has exactly one logical record type; `fact_type` cannot be used to encode a
   DerivedMetric or Interpretation.
3. Numeric values carry a declared unit where a unit is meaningful; missing values are
   null/unknown and are never guessed from neighboring records.
4. Normally `available_at <= retrieved_at <= accepted_at`. A late arrival has
   `available_at < accepted_at`; it is not rewritten as if it became available at
   acceptance time. If embargoed content is staged before availability, it remains
   ineligible for Store consumption until `available_at`. As-of queries exclude any
   record whose `available_at` is later than the cutoff.
5. A superseding record does not delete its predecessor, and an amendment retains the
   predecessor link and source reference.
6. DerivedMetric lineage is complete and method-versioned; Interpretation basis is
   explicit; neither may masquerade as a Fact.
7. Relationship validity gaps remain unknown when Evidence does not establish a
   boundary; observed/check time is not used as a fabricated `valid_from`.
8. Record serialization excludes credentials, provider response bodies, and durable
   raw news content.
9. `event_time`, `observed_at`, `published_at`, `filed_at`, `retrieved_at`,
   `available_at`, and `accepted_at` remain separate fields; one timestamp is never
   copied into another merely to satisfy nullability.

Minimum fixture coverage: one filing Fact with Evidence, one amended Fact, one
corporate Relationship, one DerivedMetric with two inputs, one Interpretation, one
contradicting Evidence record, and an as-of query demonstrating that history and
availability are preserved.

## 5. Consequences and downstream handoff

- I0-002 supplies the shared provenance value objects used by this envelope.
- I0-006 adds temporary-content expiry and deletion proof without changing these
  record types.
- E0/N1/O0 may extend the versioned type registries, but cannot collapse the record
  boundaries.
- L0-005 chooses a migration layout that can reconstruct these logical records and
  preserves append-only history.
- X0 queries may project these records into a timeline, but the projection is not a
  second source of truth.

This ADR moves to Accepted only after I0-002 defines the timestamp/provenance value
objects and contract fixtures demonstrate the invariants in section 4. A documentation
review alone does not complete the implementation evidence.

## 6. Related requirements and documents

- `REQ-FACT-001..003`
- `REQ-REG-020`, `REQ-REG-026`, `REQ-VER-013..014`
- `HIGH_LEVEL_DESIGN_v0.1.md`, section 5.10
- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`, `I0-002`〜`I0-007`
