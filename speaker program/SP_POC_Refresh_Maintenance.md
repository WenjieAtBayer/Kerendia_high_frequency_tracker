# SP_POC Refresh Maintenance Guide

**Schema:** `ph-com-ai-us-prod-catalog-2553213839599380.sp_poc`
**Refresh Notebook:** [SP_POC_Refresh](/editor/notebooks/2185703631386936)
**Design Doc:** [NBA_Speaker_Program_Metric_Views_Design.md](/editor/files/2185703631386937)
**Last refreshed:** Nov 12, 2026 (full pipeline migration — all tables refreshed)
**Last updated:** November 12, 2026

---

## 1. Table Inventory

All managed tables were originally created on **Sep 25, 2026** by Nicholas Siebenlist from a single notebook (`804528127606154`, now inaccessible). As of **Nov 12, 2026**, the full pipeline is owned by Wenjie Chen and runs entirely from the SP_POC_Refresh notebook.

| Table | Type | Rows | NPIs | Date Column | Source System |
|-------|------|------|------|-------------|---------------|
| `hcp_xref` | Dimension | 14,972 | 14,972 | N/A | fact_attendance NPIs + dim_call_plan_target + V7 rx_matchable (UC) |
| `fact_attendance` | Fact | 31,047 | 14,972 | `event_date` | cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM (Snowflake federation) |
| `dim_event_owner` | Dimension | 3,259 | 3,259 | `event_id` | ANLT_BASE_FACT_EVNT_PRSNL_PROM SALE_ORG_NM (Snowflake federation) |
| `fact_rx_hcp_week` | Fact | 338,496 | 5,327 | `week_ending_date` | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (UC) |
| `pre_post_lift` | Derived | 14,972 | 14,972 | `anchor_dt` | fact_attendance + fact_rx_hcp_week + kerendia_metric_views.fact_calls |

**Replaced by kerendia_metric_views (no longer in sp_poc):**
| Old Table | Replacement | Notes |
|-----------|-------------|-------|
| `fact_calls` | `kerendia_metric_views.fact_calls` | 2.6M rows, fresh to Nov 6. Column: `call_name` (was `call_nm`). |
| `fact_trx_hcp_month` | `kerendia_metric_views.fact_xponent_trx` | `month_id` is INT (was STRING). CAST in v_fact_trx_hcp_month view. |

**Pending:** ~~v_fact_calls and v_fact_trx_hcp_month intermediate views still point to old sp_poc tables.~~ **RESOLVED Nov 12, 2026** — both views repointed to kerendia_metric_views. Old sp_poc.fact_calls and sp_poc.fact_trx_hcp_month can be dropped.

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

**Key:** As of Nov 12, 2026, ALL tables are refreshable from the SP_POC_Refresh notebook. The pipeline no longer depends on Nicholas's Snowflake pipeline.

---

## 3. ETL Logic (from view column comments)

### 3.1 fact_rx_hcp_week

**Source:** `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (switched from V6 on Nov 12, 2026)

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
- `PAY_TYPE`: All pay types included (cash-pay filter removed Oct 20, 2026 — cash-pay is 0.2% of total NBRx)
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

**Source:** fact_attendance NPIs (base universe) + kerendia_metric_views.fact_calls (NPI↔BH_ID bridge) + kerendia_metric_views.dim_call_plan_target (segment/territory by quarter, Q3/Q4) + V7 rx_matchable
- Built from fact_attendance NPIs to define the speaker program universe (attendees + non-attendees)
- Enriched with segment, territory, region, area from dim_call_plan_target (latest available quarter)
- `rx_matchable` flag: TRUE if NPI has Kerendia Rx data in V7

### 3.6 pre_post_lift

**Source:** Derived from fact_attendance + fact_rx_hcp_week + fact_calls
- Per-NPI pre/post NBRx lift, anchored to first attended event date
- Controls (non-attended) get median anchor date from attended cohort
- See SP_POC_Refresh notebook cell 4 for full SQL

---

## 4. Recommended Refresh Cadence

| Table | Trigger | Cadence | Who |
|-------|---------|---------|-----|
| `fact_attendance` | New speaker program events | Weekly (after each NBA cycle) | **SP_POC_Refresh notebook** (Snowflake federation) |
| `hcp_xref` | After fact_attendance refresh | Weekly | **SP_POC_Refresh notebook** (UC + federation) |
| `dim_event_owner` | New events | Weekly | **SP_POC_Refresh notebook** (Snowflake federation) |
| `fact_rx_hcp_week` | V7 table refresh | **Weekly** (when V7 updates) | **SP_POC_Refresh notebook** |
| `pre_post_lift` | After any fact table refresh | After Rx or attendance refresh | **SP_POC_Refresh notebook** |

---

## 5. Refresh Procedure

### 5.1 UC-refreshable tables (use SP_POC_Refresh notebook)

1. **Check V7 freshness**: `SELECT MAX(PERIOD_ID) FROM kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7`
2. **Run Cell 1** (Configuration)
3. **Run Cell 2** (fact_attendance refresh) — from cph_db_prod federation, with row-count guard
4. **Run Cell 3** (hcp_xref rebuild) — from fact_attendance + dim_call_plan_target + V7
5. **Run Cell 4** (Pre-refresh audit) — capture current row counts and max dates
6. **Run Cell 5** (Refresh fact_rx_hcp_week) — CTAS from V7
7. **Run Cell 6** (dim_event_owner refresh) — from ANLT_BASE_FACT_EVNT_PRSNL_PROM SALE_ORG_NM
8. **Run Cell 7** (Recompute pre_post_lift) — only if cells 2-5 succeeded
9. **Run Cell 8** (Post-refresh validation) — verify all tables updated
10. **Run Cell 9** (NBA metric view coverage check)

### 5.2 Snowflake-sourced tables (now owned)

As of Nov 12, 2026, all tables are refreshed from the SP_POC_Refresh notebook. fact_attendance and dim_event_owner use Snowflake federation (cph_db_prod) directly. hcp_xref is built from UC sources (fact_calls bridge + dim_call_plan_target). No coordination with Nicholas's pipeline is needed.

---

## 6. Refresh Log

| Date | Actor | Tables Refreshed | Notes |
|------|-------|-----------------|-------|
| Sep 25, 2026 | Nicholas Siebenlist | All 6 tables | Initial load from notebook 804528127606154 |
| Oct 19, 2026 | Wenjie (SP_POC_Refresh) | fact_rx_hcp_week, pre_post_lift | +4 weeks (Sep 4–25). Rows: 164,627→170,463. NPIs: 2,994→3,049. Fixed UNIX_DATE type mismatch in pre_post_lift. |
| Nov 8, 2026 | SP_POC weekly job | fact_rx_hcp_week, dim_event_owner (wiped) | Rx data through Oct 16. dim_event_owner wiped to 0 rows — Snowflake federation connection (cph_db_prod / snowflake_cdp) returned 0 rows. See Known Issues below. |
| Nov 12, 2026 | Wenjie | SP_POC_Refresh notebook | Added row-count guard to dim_event_owner cell: checks source row count before CREATE OR REPLACE; skips refresh and warns if source returns 0 rows. |
| Nov 12, 2026 | Wenjie (Genie Code) | **Full pipeline migration** | All 5 tables refreshed. V6→V7 swap (338K rows, 5,327 NPIs). fact_attendance via federation (31K rows, 14,972 NPIs, data through Nov+). dim_event_owner via SALE_ORG_NM (3,259 events, no longer uses DOMAIN_DP_FACT_EVENTS_ACTIVITY). hcp_xref rebuilt from fact_attendance + dim_call_plan_target + V7 (14,972 NPIs). pre_post_lift recomputed (14,972 NPIs, 488 new writers). Intermediate views v_fact_calls and v_fact_trx_hcp_month still point to old tables (MANAGE permission needed). |

---

## 6a. Known Issues (as of Nov 12, 2026)

### Snowflake Federation Connection (RESOLDED Nov 12, 2026)

The foreign catalog `cph_db_prod` (connection `snowflake_cdp`) was returning 0 rows from the SP_POC_Refresh service principal as of Nov 8. The user confirmed the connection works from their session. The `ANLT_BASE_FACT_EVNT_PRSNL_PROM` table is accessible from the notebook and returns 1.83M rows. The `DOMAIN_DP_FACT_EVENTS_ACTIVITY` table still returns 0 rows from the notebook (likely row-level security), so dim_event_owner now derives from `SALE_ORG_NM` in the attendance source instead.

### ~~Pending: v_fact_calls and v_fact_trx_hcp_month view repointing~~ RESOLVED Nov 12, 2026

Both intermediate views have been repointed to kerendia_metric_views sources. mv_speaker_calls now returns 408K rows (was 114K stale), mv_speaker_trx returns 191K rows with data through Oct 2026. Old sp_poc.fact_calls and sp_poc.fact_trx_hcp_month tables can now be dropped.

---

## 7. Coverage Impact Reference

With Rx data through Sep 25, 2026:

| NBA Cycle Month | 4w Coverage | 12w Coverage | Next Unlock |
|-------------|-------------|--------------|-------------|
| July 2026 | **100%** | 0% | 12w needs Sep 29 (4 days away — next v6 refresh) |
| August 2026 | **96–100%** | 0% | 12w needs late Nov |
| September 2026 | 0% | 0% | 4w needs ~Oct 14 |
| October 2026 | 0% | 0% | 4w needs ~Nov 11 |

---

## 8. Metric View Change Log

| Date | Actor | Views Changed | Description |
|------|-------|---------------|-------------|
| Oct 16, 2026 | Wenjie | mv_speaker_nba, mv_speaker_nba_rx | Initial creation. Universe = ALERT_FLAG = 1 only (HCPs on the NBA dropdown list). |
| Oct 20, 2026 | Wenjie | mv_speaker_nba, mv_speaker_nba_rx | **Universe expansion and dedup.** Changed via `ALTER VIEW` (permissions preserved). Universe expanded from NBA-only (ALERT_FLAG = 1) to all Segment A/B HCPs per monthly cycle. New dimensions: `is_nba` (MAX(ALERT_FLAG) = 1), `nba_group` ('NBA' / 'Not NBA'). Not NBA HCPs anchored to the same cycle date for all windows. `mv_speaker_nba` deduplicated to 1 row per NPI x cycle (was ~1.8x inflated). New measures: `hcp_cycles`, `npis_universe`, `npis_not_nba`, `nba_coverage_rate` (mv_speaker_nba); `npis_nba`, `npis_not_nba` (mv_speaker_nba_rx). `alerts` and `npis_alerted` now FILTER WHERE is_nba. All funnel/Rx measures are generic over the slice; dashboards must filter `nba_group = 'NBA'` for NBA-only numbers. |
| Oct 20, 2026 | Wenjie | mv_speaker_nba, mv_speaker_nba_rx, mv_speaker_nba_territory (new), dim_event_owner (new) | **Territory fix + inviting rep.** Removed `territory` (was `FIRST(TERR_DESC)`, an arbitrary pick for the ~80% of HCPs shared by 2–4 territories). Added `aligned_territories`, `n_aligned_territories`, `is_shared_hcp` to both views; added `inviting_territory`, `inviting_rep`, `invited_by_aligned_territory_30d/60d` dims and `shared_hcps`, `invitations_by_aligned_territory_60d`, `pct_invites_from_aligned_territory_60d` measures to mv_speaker_nba. New `mv_speaker_nba_territory` (NPI × cycle × territory) for territory adoption. Comments and display names now say "NBA dropdown list" instead of "alert" (column names unchanged). Applied with `CREATE OR REPLACE VIEW`; no object-level grants existed (catalog-inherited only). Prior DDL saved in `sp_poc._mv_ddl_backup`. Funnel and lift numbers unchanged. |

**Upstream dependency note:** All three NBA metric views depend on the NBA list source table (`kerendia_nba_3.kerendia_sp_nba_integration_alerts`) containing `ALERT_FLAG = 0` rows for Segment A/B HCPs. If the upstream feed ever stops publishing rows for HCPs not on the list, the Not NBA group will be empty and universe counts will drop to NBA-only levels.

---

## 9. Long-term Recommendations

1. **Automate full pipeline refresh**: Schedule SP_POC_Refresh notebook as a weekly Lakeflow Job
2. **Drop old tables**: sp_poc.fact_calls and sp_poc.fact_trx_hcp_month can now be dropped (views repointed to kerendia_metric_views)
3. **Add row-count alerting**: Create alerts on fact_rx_hcp_week and fact_attendance row counts to detect stale data
4. **Monitor federation**: Check that cph_db_prod federation connection stays healthy; the row-count guard protects against silent wipes
