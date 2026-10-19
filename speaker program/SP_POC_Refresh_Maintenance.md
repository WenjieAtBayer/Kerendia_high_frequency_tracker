# SP_POC Refresh Maintenance Guide

**Schema:** `ph-com-ai-us-prod-catalog-2553213839599380.sp_poc`
**Refresh Notebook:** [SP_POC_Refresh](/editor/notebooks/2185703631386802)
**Design Doc:** [NBA_Speaker_Program_Metric_Views_Design.md](/editor/files/1139238961821424)
**Last refreshed:** Oct 19, 2026 (fact_rx_hcp_week + pre_post_lift)

---

## 1. Table Inventory

All 6 managed tables were originally created on **Sep 25, 2026** by Nicholas Siebenlist from a single notebook (`804528127606154`, now inaccessible). Each was a one-time `CREATE OR REPLACE TABLE AS SELECT`.

| Table | Type | Rows | NPIs | Date Column | Source System |
|-------|------|------|------|-------------|---------------|
| `hcp_xref` | Dimension | 6,742 | 6,742 | N/A | Foundation/MDM + segment lists (Snowflake) |
| `fact_attendance` | Fact | 7,598 | 6,742 | `event_date` | CPH_DB_PROD.ANALYTICS_V2 (Snowflake) |
| `fact_calls` | Fact | 114,045 | 5,484 | `call_date` | Lynkuet/Veeva (Snowflake) |
| `fact_rx_hcp_week` | Fact | 170,463 | 3,049 | `week_ending_date` | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6` (UC) |
| `fact_trx_hcp_month` | Fact | 55,029 | 3,002 | `month_id` | Xponent FTP+non-FTP (Snowflake) |
| `pre_post_lift` | Derived | 6,742 | 6,742 | `anchor_dt` | fact_attendance + fact_rx_hcp_week + fact_calls |

---

## 2. Dependency Graph

```
EXTERNAL SOURCES                    UNITY CATALOG
┌──────────────────┐    ┌─────────────────────────────────────┐
│ Snowflake        │    │ kerendia_laad_based_lrx              │
│  CPH_DB_PROD     │    │   .kerendia_laad_based_lrx_v6       │
│  Lynkuet/Veeva   │    │   (NBRx weekly — refreshable in UC) │
│  Xponent         │    ├─────────────────────────────────────┤
│  Foundation/MDM   │    │ Xponent (TRx monthly)               │
└────────┬─────────┘    └───────────────────┬─────────────────┘
         │                                  │
         ▼                                  ▼
┌───────────────────────────────────────────────────────────────┐
│                    sp_poc MANAGED TABLES                       │
│                                                               │
│  1. hcp_xref ◄──── Foundation/MDM (Snowflake only)           │
│       │                                                       │
│       ├──► 2a. fact_attendance ◄── CPH_DB (Snowflake only)   │
│       ├──► 2b. fact_calls ◄────── Lynkuet (Snowflake only)   │
│       ├──► 2c. fact_rx_hcp_week ◄─ v6 (✅ REFRESHABLE IN UC) │
│       └──► 2d. fact_trx_hcp_month ◄ Xponent (Snowflake only) │
│                    │                                          │
│                    ▼                                          │
│            3. pre_post_lift (✅ REFRESHABLE IN UC)            │
└───────────────────────────────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│              METRIC VIEWS (auto-refresh on query)             │
│  mv_speaker_nba, mv_speaker_nba_rx, mv_speaker_lift, etc.    │
└───────────────────────────────────────────────────────────────┘
```

**Key:** Only `fact_rx_hcp_week` and `pre_post_lift` can be refreshed from within Databricks. The other 4 tables require Snowflake access via Nicholas's pipeline.

---

## 3. ETL Logic (from view column comments)

### 3.1 fact_rx_hcp_week

**Source:** `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6`

```sql
CREATE OR REPLACE TABLE sp_poc.fact_rx_hcp_week AS
SELECT
  v6.NPI AS npi,                          -- V6 has NPI column directly
  v6.PERIOD_ID AS week_ending_date,       -- STRING 'YYYYMMDD' → stored as-is
  v6.INDICATION_GROUP AS indication_group, -- Patient-level: T2D+CKD+CVD etc.
  SUM(v6.NBRX) AS nbrx                   -- Kerendia new prescriptions
FROM kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6 v6
INNER JOIN sp_poc.hcp_xref x
  ON v6.NPI = x.npi AND x.rx_matchable = TRUE
WHERE v6.PRODUCT_GROUP = 'KERENDIA'
  AND v6.PAY_TYPE != 'CASH'
  AND v6.PERIOD_TYPE IN ('W', 'X')
GROUP BY v6.NPI, v6.PERIOD_ID, v6.INDICATION_GROUP
```

**Filters explained:**
- `PRODUCT_GROUP = 'KERENDIA'`: Only Kerendia scripts
- `PAY_TYPE != 'CASH'`: Exclude cash-pay (non-formulary)
- `PERIOD_TYPE IN ('W','X')`: Weekly aggregation types only
- `rx_matchable = TRUE`: NPIs that exist in both v6 and hcp_xref identity bridge

### 3.2 fact_attendance

**Source:** CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM (Snowflake)
- Includes event_type, format, indication (classified from EVNT_TPIC_NM)
- `attended_flag`: TRUE = attended, FALSE = invited-not-attended
- Enriched with `first_attend_dt` and `exposure_count` per NPI

### 3.3 fact_calls

**Source:** Lynkuet/Veeva (Snowflake)
- Joined to hcp_xref via BH_ID for NPI resolution
- `called_within_14d`: TRUE if call fell within 14 days after an attended event

### 3.4 fact_trx_hcp_month

**Source:** Xponent FTP + non-FTP (Snowflake)
- `trx = ROUND(SUM(TQTY)/30, 2)` — Total Rx scripts
- Monthly grain (YYYYMM string in `month_id`)

### 3.5 hcp_xref

**Source:** Foundation/MDM (Snowflake)
- Identity bridge: NPI ↔ BH_ID
- Includes `kerendia_segment`, `specialty`, `territory`, `region`, `area`
- `rx_matchable` flag: TRUE if NPI exists in v6 Rx data

### 3.6 pre_post_lift

**Source:** Derived from fact_attendance + fact_rx_hcp_week + fact_calls
- Per-NPI pre/post NBRx lift, anchored to first attended event date
- Controls (non-attended) get median anchor date from attended cohort
- See SP_POC_Refresh notebook cell 4 for full SQL

---

## 4. Recommended Refresh Cadence

| Table | Trigger | Cadence | Who |
|-------|---------|---------|-----|
| `hcp_xref` | New segment lists or roster changes | Quarterly | Nicholas (Snowflake) |
| `fact_attendance` | New speaker program events | Monthly (after each NBA alert) | Nicholas (Snowflake) |
| `fact_calls` | New Veeva call data | Monthly | Nicholas (Snowflake) |
| `fact_rx_hcp_week` | v6 table refresh | **Weekly** (when v6 updates) | **SP_POC_Refresh notebook** |
| `fact_trx_hcp_month` | Xponent monthly refresh | Monthly | Nicholas (Snowflake) |
| `pre_post_lift` | After any fact table refresh | After Rx or attendance refresh | **SP_POC_Refresh notebook** |

---

## 5. Refresh Procedure

### 5.1 UC-refreshable tables (use SP_POC_Refresh notebook)

1. **Check v6 freshness**: `SELECT MAX(WEEK_ENDING_DATE) FROM kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6`
2. **Run Cell 1** (Configuration)
3. **Run Cell 2** (Pre-refresh audit) — capture current row counts and max dates
4. **Run Cell 3** (Refresh fact_rx_hcp_week) — CTAS from v6
5. **Run Cell 5** (Post-refresh validation) — verify row count increased, max_date matches v6
6. **Run Cell 4** (Recompute pre_post_lift) — only if Cell 3 succeeded
7. **Run Cell 5 again** — verify pre_post_lift updated
8. **Run Cell 6** (NBA metric view coverage check) — verify coverage percentages improved

### 5.2 Snowflake-sourced tables

Coordinate with Nicholas Siebenlist to run the original pipeline. These tables require Snowflake credentials and cannot be refreshed from the SP_POC_Refresh notebook.

---

## 6. Refresh Log

| Date | Actor | Tables Refreshed | Notes |
|------|-------|-----------------|-------|
| Sep 25, 2026 | Nicholas Siebenlist | All 6 tables | Initial load from notebook 804528127606154 |
| Oct 19, 2026 | Wenjie (SP_POC_Refresh) | fact_rx_hcp_week, pre_post_lift | +4 weeks (Sep 4–25). Rows: 164,627→170,463. NPIs: 2,994→3,049. Fixed UNIX_DATE type mismatch in pre_post_lift. |

---

## 7. Coverage Impact Reference

With Rx data through Sep 25, 2026:

| Alert Month | 4w Coverage | 12w Coverage | Next Unlock |
|-------------|-------------|--------------|-------------|
| July 2026 | **100%** | 0% | 12w needs Sep 29 (4 days away — next v6 refresh) |
| August 2026 | **96–100%** | 0% | 12w needs late Nov |
| September 2026 | 0% | 0% | 4w needs ~Oct 14 |
| October 2026 | 0% | 0% | 4w needs ~Nov 11 |

---

## 8. Long-term Recommendations

1. **Automate fact_rx_hcp_week refresh**: Schedule SP_POC_Refresh notebook as a weekly Lakeflow Job triggered by v6 table updates
2. **Parameterize v6 version**: Add a notebook widget for the v6 table path in case v7/v8 is published
3. **Consolidate Snowflake pipeline**: Work with Nicholas to document or recreate the lost notebook for the 4 Snowflake-sourced tables
4. **Add row-count alerting**: Create alerts on fact_rx_hcp_week row count to detect stale data
