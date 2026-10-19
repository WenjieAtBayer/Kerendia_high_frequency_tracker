# Kerendia P2P NBA Speaker Program — Metric View Design Document

> **Catalog:** `ph-com-ai-us-prod-catalog-2553213839599380.sp_poc`  
> **Views:** `mv_speaker_nba` · `mv_speaker_nba_rx`  
> **Last updated:** October 2026

---

## 1. Initiative Overview

The Kerendia P2P (Peer-to-Peer / Speaker Program) **NBA (Next Best Action)** initiative is a monthly alert system that recommends HCPs for speaker program invitations. Alerts are issued on the 7th of each month to HCPs who:
- Have `ALERT_FLAG = 1`
- Belong to `CALL_PLAN_SEGMENT` A or B
- Are in territories included in the Pharma Roster

The reporting goal is end-to-end visibility from alert to prescription impact:

```
NBA Alert → Invitation Sent → Program Attendance → NBRx / New Writer
```

---

## 2. Source Data

| Table | Schema | Grain | Key Columns |
|-------|--------|-------|-------------|
| `kerendia_sp_nba_integration_alerts` | `kerendia_nba_3` | 1 row per HCP × scenario | `NPI_NUMBER` (double), `ALERT_DATE` (string), `ALERT_FLAG`, `CALL_PLAN_SEGMENT` |
| `fact_attendance` | `sp_poc` | 1 row per NPI × event | `npi` (string), `event_date`, `attended_flag` (boolean) |
| `fact_rx_hcp_week` | `sp_poc` | 1 row per NPI × week | `npi`, `week_ending_date`, `nbrx` |

**NPI join key:** `CAST(CAST(NPI_NUMBER AS BIGINT) AS STRING)` — alerts store NPI as `DOUBLE`, requiring two-step cast to match the `STRING` NPI in other tables.

**Alert deduplication:** ~7,900–10,500 alert rows per month collapse to ~4,300–6,200 distinct NPIs (1.8× duplication from multiple scenario rows per HCP).

---

## 3. Decision Log

### 3.1 Why two metric views?

| Question | Answer |
|----------|--------|
| Can `mv_speaker_lift` (existing) cover NBA? | No — it anchors pre/post windows to the **event date**, not the alert date. It also only covers the invited cohort, not the full NBA-alerted population. |
| Should we extend `mv_speaker_nba` with Rx? | Source SQL would become prohibitively complex with a three-way join (alerts × attendance × weekly Rx). Separate views keep each focused. |

**Decision:** Two views — `mv_speaker_nba` for the invitation/attendance funnel, `mv_speaker_nba_rx` for Rx effectiveness.

### 3.2 Invitation window: 30 days vs 60 days

Analysis of July 2026 alerts showed:

| Window | NPIs Invited | NPIs Attended |
|--------|-------------|---------------|
| 30 days | 17 | 5 |
| 60 days | 43 | 12 |
| Any time after alert | 59 | 15 |

The 60-day window captures 2.5× more invitations. However, for early-read purposes, 30 days is sufficient as a "quick signal" indicator.

**Decision for `mv_speaker_nba`:** Include both 30d and 60d windows for invitations and attendance.

### 3.3 Rx window: 4 weeks vs 12 weeks

Rx data (`fact_rx_hcp_week`) lags — as of October 2026 it extends only to August 28, 2026. A 12-week post-window for July alerts requires data through late September.

**Decision:** Dual-window design in `mv_speaker_nba_rx`:
- **4-week (early read)** — provides actionable signal within ~6 weeks of alert
- **12-week (mature)** — the definitive measurement once data coverage is complete

### 3.4 Attendance window for mature metrics: 30 days → 60 days

The earlier funnel analysis showed that widening the attendance window from 30 to 60 days more than doubled the ATTENDED cohort (5 → 12 NPIs for July) while the invite-to-attend conversion rate remained stable (~28–30%).

**Decision:** The 12-week mature metrics use a **60-day attendance window** (vs 30-day for the early read), giving the full pipeline more time to complete.

### 3.5 Adaptive post-anchor

The post-Rx measurement window should not always start from the alert date. An HCP who attended a program 25 days after the alert needs their post-NBRx measured from the event, not from 25 days earlier.

**Decision:** `post_anchor_date` adapts per HCP:
- First attended event date (if attended) → first invite date (if invited only) → alert date (if never invited)

---

## 4. Window Architecture

### 4.1 `mv_speaker_nba` — Invitation & Attendance Funnel

```
Alert Date
    │
    ├──── 30 days ────┤  ← invited_within_30d / attended_within_30d
    │                 │
    ├──────────── 60 days ────────────┤  ← invited_within_60d / attended_within_60d
    │                                 │
    ▼                                 ▼
 Jul 7                             Sep 5
```

Grain: 1 row per NPI × alert_date. Boolean flags for each window.

### 4.2 `mv_speaker_nba_rx` — Early-Read (4-week Rx)

```
              ◄── 4 wk pre ──►◄── 30d invite/attend ──►
              │                │                        │
              │   PRE-NBRx     │     FUNNEL MATCHING    │
              │   (baseline)   │                        │
    ──────────┼────────────────┼────────────────────────┼──────────────
         alert_date - 28d   alert_date            post_anchor_date
                                                        │
                                                        ├── 4 wk post ──►
                                                        │   POST-NBRx    │
                                                        │   (outcome)    │
                                                        ▼                ▼
                                                   anchor_date    anchor + 28d


    Post-anchor logic (early read):
    ┌─────────────────────────────────────────────────────────┐
    │  ATTENDED?  ──yes──►  post_anchor = first_attended_30d  │
    │      │                                                  │
    │      no                                                 │
    │      ▼                                                  │
    │  INVITED?   ──yes──►  post_anchor = first_invite_30d    │
    │      │                                                  │
    │      no                                                 │
    │      ▼                                                  │
    │  post_anchor = alert_date                               │
    └─────────────────────────────────────────────────────────┘
```

### 4.3 `mv_speaker_nba_rx` — Mature (12-week Rx)

```
          ◄────── 12 wk pre ──────►◄── 30d invite / 60d attend ──►
          │                        │                               │
          │      PRE-NBRx          │        FUNNEL MATCHING        │
          │      (baseline)        │    (wider attend window)      │
    ──────┼────────────────────────┼───────────────────────────────┼────────
     alert_date - 84d          alert_date                   post_anchor_12w
                                                                   │
                                                                   ├── 12 wk post ─────►
                                                                   │    POST-NBRx       │
                                                                   │    (outcome)       │
                                                                   ▼                    ▼
                                                              anchor_date_12w    anchor + 84d


    Post-anchor logic (mature):
    ┌─────────────────────────────────────────────────────────────┐
    │  ATTENDED within 60d?  ──yes──►  anchor = first_attend_60d  │
    │      │                                                      │
    │      no                                                     │
    │      ▼                                                      │
    │  INVITED within 30d?   ──yes──►  anchor = first_invite_30d  │
    │      │                                                      │
    │      no                                                     │
    │      ▼                                                      │
    │  anchor = alert_date                                        │
    └─────────────────────────────────────────────────────────────┘
```

### 4.4 Funnel Stage Divergence

The same HCP can be classified differently across the two funnels:

```
    Example: HCP invited on Day 10, attended on Day 45

    Early-read funnel (30d/30d):   INVITED_ONLY  (attended outside 30d window)
    Mature funnel (30d/60d):       ATTENDED       (attended within 60d window)

    Early-read post_anchor:        Day 10 (invite date)
    Mature post_anchor_12w:        Day 45 (attend date)
```

---

## 5. Coverage Flags

Both metric tiers include a **data completeness guard** — a boolean dimension computed against `MAX(week_ending_date)` from `fact_rx_hcp_week`:

```
    post_4w_complete  = (post_anchor_date + 28)    ≤ max_rx_date
    post_12w_complete = (post_anchor_date_12w + 84) ≤ max_rx_date
```

Aggregate measures `pct_4w_covered` and `pct_12w_covered` show the percentage of rows with full coverage for any given slice. Dashboard consumers should:

1. **Always show** 4-week early-read metrics with `pct_4w_covered` as a trust badge
2. **Gray out or annotate** 12-week mature metrics when `pct_12w_covered < 100%`
3. As Rx data refreshes weekly, coverage climbs automatically

**Coverage snapshot (post-refresh, Oct 19 2026 — Rx data through Sep 25):**

| Alert Month | 4w Coverage | 12w Coverage |
|-------------|-------------|--------------|
| July 2026 | **100%** | 0% (needs Sep 29 — 4 days short) |
| August 2026 | **96–100%** | 0% |
| September 2026 | 0% | 0% |
| October 2026 | 0% | 0% |

---

## 6. Early Findings (October 2026)

### July 2026 — 4-week early read (100% coverage after refresh)

| Funnel Stage | NPIs | Lift | New Writers | NW Rate |
|-------------|------|------|-------------|--------|
| ATTENDED | 5 | **+2.60** | 2 | **40.0%** |
| INVITED_ONLY | 12 | 0.00 | 1 | 8.3% |
| NOT_INVITED | 4,338 | 0.00 | 70 | 1.6% |

### August 2026 — 4-week early read (96–100% coverage, newly available after refresh)

| Funnel Stage | NPIs | Lift | New Writers | NW Rate |
|-------------|------|------|-------------|--------|
| ATTENDED | 10 | **+0.40** | 1 | **10.0%** |
| INVITED_ONLY | 25 | +0.08 | 3 | 12.0% |
| NOT_INVITED | 6,225 | +0.01 | 57 | 0.9% |

**Key insight:** The July ATTENDED cohort (5 NPIs) shows a dramatic +2.60 NBRx lift and 40% new-writer conversion. August’s ATTENDED cohort (10 NPIs), now visible after the refresh, confirms the signal with +0.40 lift and 10% new-writer rate — still well above the NOT_INVITED baseline.

### Alert-to-Invite Funnel (all months, 60-day window)

| Alert Month | NPIs Alerted | Invited | Attended | Invite Rate |
|-------------|-------------|---------|----------|-------------|
| July 2026 | 4,355 | 76 | 23 | 1.7% |
| August 2026 | 6,260 | 83 | 19 | 1.3% |
| September 2026 | 6,150 | 30 | 3 | 0.5% |
| October 2026 | 6,152 | 0 | 0 | 0.0% |

The invite rate is low (~1–2%) because speaker programs are capacity-constrained. The bottleneck is the alert-to-invite step, not program quality — once invited, ~28–30% attend.

### Top Territories

New Orleans (S LA Striker, W LA), Phoenix Central, and Mid-Atlantic showed the best end-to-end conversion from NBA alert to actual attendance.

### Data Refresh Log

| Date | Action | fact_rx_hcp_week | pre_post_lift |
|------|--------|-----------------|---------------|
| Sep 25, 2026 | Initial load (Nicholas) | 164,627 rows, max Aug 28 | 6,742 rows, post_nbrx 3,088 |
| Oct 19, 2026 | Refresh from v6 | 170,463 rows (+5,836), max Sep 25 | 6,742 rows, post_nbrx 3,164 (+76) |

---

## 7. Metric View Summary

### `mv_speaker_nba`

| Type | Name | Description |
|------|------|-------------|
| Dimension | `alert_month` | Month the alert was issued |
| Dimension | `territory` / `region` / `area` | Sales geography |
| Dimension | `call_plan_segment` | A or B segment |
| Dimension | `invited_within_30d` / `60d` | Invitation flag |
| Dimension | `attended_within_30d` / `60d` | Attendance flag |
| Measure | `invitations_sent_30d` / `60d` | Count of alerts → invitations |
| Measure | `invitation_rate_30d` / `60d` | Alert-to-invite % |
| Measure | `programs_attended_30d` / `60d` | Count of alerts → attendance |
| Measure | `invite_to_attend_30d` / `60d` | Invite-to-attend conversion % |

### `mv_speaker_nba_rx`

| Type | Name | Description |
|------|------|-------------|
| Dimension | `funnel_stage` | Early-read cohort (30d/30d) |
| Dimension | `funnel_stage_12w` | Mature cohort (30d/60d) |
| Dimension | `is_new_writer_4w` / `12w` | New writer flag |
| Dimension | `post_4w_complete` / `post_12w_complete` | Rx coverage flag |
| Measure | `avg_nbrx_lift_4w` / `12w` | Average NBRx lift |
| Measure | `new_writer_rate_4w` / `12w` | New writer conversion % |
| Measure | `pct_4w_covered` / `pct_12w_covered` | Data coverage % |

---

## 8. Genie Space Integration

Both views are added to the **Kerendia Speaker Program Impact + NBA** Genie space (`01f1c9939e8a1648bbc09df186d37134`) with:
- 5 text instructions covering initiative context, usage guidance, and funnel semantics
- 5 SQL examples for common questions
- 8 starter questions spanning all four reporting areas

All views use **MEASURE() syntax** for aggregation queries.

---

## 9. Data Lineage & Refresh Maintenance

> **Full details:** See [SP_POC_Refresh_Maintenance.md](/editor/files/2185703631386835) for the complete refresh guide including ETL logic, dependency graph, refresh procedures, and refresh log.
>
> **Refresh notebook:** [SP_POC_Refresh](/editor/notebooks/2185703631386802)

### 9.1 Table Inventory

All 6 managed tables in `sp_poc` were created on **Sep 25, 2026** by Nicholas Siebenlist from a single notebook (`804528127606154`, now inaccessible). Each is a one-time `CREATE OR REPLACE TABLE AS SELECT` — no incremental pipeline exists.

```
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        UPSTREAM SOURCES                                │
    │                                                                       │
    │  Snowflake / CPH_DB_PROD          Unity Catalog                       │
    │  ┌──────────────────────┐    ┌──────────────────────────────────────┐  │
    │  │ ANALYTICS_V2         │    │ kerendia_laad_based_lrx             │  │
    │  │  (attendance/events) │    │  .kerendia_laad_based_lrx_v6       │  │
    │  ├──────────────────────┤    │  (NBRx weekly — to Sep 25, 2026)   │  │
    │  │ Lynkuet / Veeva      │    ├──────────────────────────────────────┤  │
    │  │  (sales calls)       │    │ Xponent                            │  │
    │  ├──────────────────────┤    │  (TRx monthly)                     │  │
    │  │ Foundation / MDM      │    └──────────────────────────────────────┘  │
    │  │  (HCP identity)      │                                             │
    │  └──────────────────────┘                                             │
    └───────────────┬─────────────────────────────────┬─────────────────────┘
                    │                                 │
                    ▼                                 ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      sp_poc MANAGED TABLES                             │
    │                                                                       │
    │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐            │
    │  │  hcp_xref    │  │ fact_        │  │ fact_rx_hcp_week  │◄── v6     │
    │  │  (identity   │  │ attendance   │  │ (NBRx weekly)     │  STALE ⚠  │
    │  │   bridge)    │  │ (SP events)  │  ├───────────────────┤            │
    │  └──────┬───────┘  └──────────────┘  │ fact_trx_hcp_     │            │
    │         │          ┌──────────────┐  │ month (TRx)       │            │
    │         └─────────►│ fact_calls   │  └───────────────────┘            │
    │          (NPI join) │ (sales calls)│  ┌───────────────────┐            │
    │                    └──────────────┘  │ pre_post_lift     │            │
    │                                      │ (derived agg)     │            │
    │                                      └───────────────────┘            │
    └───────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    METRIC VIEWS (auto-refresh on query)                │
    │                                                                       │
    │  mv_speaker_nba        mv_speaker_nba_rx      mv_speaker_attendance   │
    │  mv_speaker_lift       mv_speaker_calls        mv_speaker_rx          │
    │  mv_speaker_trx        mv_branded_non_branded  mv_segment_universe    │
    └─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Freshness Audit (as of Oct 16, 2026)

| Table | Date Column | Max Date | Rows | NPIs | Upstream Source | Stale? |
|-------|------------|----------|------|------|----------------|--------|
| `hcp_xref` | N/A (dim) | — | 6,742 | 6,742 | Foundation/MDM + segment lists | Review quarterly |
| `fact_attendance` | `event_date` | Sep 23 | 7,598 | 6,742 | CPH_DB_PROD.ANALYTICS_V2 (Foundation events) | OK |
| `fact_calls` | `call_date` | Sep 18 | 114,045 | 5,484 | Lynkuet / Veeva (via hcp_xref NPI bridge) | OK |
| `fact_rx_hcp_week` | `week_ending_date` | **Aug 28** | 164,627 | 2,994 | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6` | **YES — 4 weeks behind** (v6 has Sep 25) |
| `fact_trx_hcp_month` | `month_id` | 202609 | 55,029 | 3,002 | Xponent FTP+non-FTP (ROUND(SUM(TQTY)/30, 2)) | OK |
| `pre_post_lift` | N/A (agg) | — | 6,742 | 6,742 | Derived from fact_attendance + fact_rx | Recompute after Rx refresh |

### 9.3 ETL Logic (from view column comments)

**`fact_rx_hcp_week`** — the critical stale table:
```sql
-- Reconstructed from v_fact_rx_hcp_week column comments:
-- Source:  kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6
-- Filters: PRODUCT_GROUP = 'KERENDIA', PAY_TYPE != 'CASH', PERIOD_TYPE IN ('W','X')
-- NPI:     PROVIDER_ID (filtered to rx_matchable NPIs via hcp_xref)
-- Date:    PERIOD_ID cast to DATE as week_ending_date
-- NBRx:    SUM(NBRX) grouped by npi, week_ending_date, indication_group
```

**`fact_attendance`** — from Foundation speaker program events:
- Source: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
- Includes event_type, format, indication (classified from topic), attended_flag

**`fact_calls`** — from Lynkuet/Veeva:
- Joined to hcp_xref for NPI resolution (Lynkuet uses BH_ID)
- Includes `called_within_14d` flag (call within 14 days of attended event)

**`fact_trx_hcp_month`** — from Xponent:
- TRx = ROUND(SUM(TQTY)/30, 2) from FTP + non-FTP union
- Monthly grain (YYYYMM string)

**`pre_post_lift`** — derived aggregate:
- Per-NPI pre/post NBRx and TRx lift, anchored to first attended event
- Depends on fact_attendance + fact_rx_hcp_week; must be recomputed after Rx refresh

### 9.4 Maintenance Recommendations

**Immediate action — refresh `fact_rx_hcp_week`:**
The v6 source has 4 new weeks (Sep 4, 11, 18, 25) not yet in the fact table. Refreshing unlocks:
- July 4w coverage → 100%
- August 4w coverage → ~95%
- July 12w coverage → still 0% (needs Sep 29; one more v6 refresh will unlock it)

**Recommended refresh cadence:**

| Table | Refresh Trigger | Cadence | Dependencies |
|-------|----------------|---------|-------------|
| `hcp_xref` | New segment lists or roster changes | Quarterly | None (independent dim) |
| `fact_attendance` | New speaker program events | Monthly (after each NBA alert) | hcp_xref (for segment/territory) |
| `fact_calls` | New Veeva call data | Monthly | hcp_xref (for NPI bridge) |
| `fact_rx_hcp_week` | v6 table refresh | **Weekly** (when v6 updates) | hcp_xref (for rx_matchable filter) |
| `fact_trx_hcp_month` | Xponent monthly refresh | Monthly | hcp_xref (for rx_matchable filter) |
| `pre_post_lift` | After any fact table refresh | After Rx or attendance refresh | fact_attendance + fact_rx_hcp_week |

**Suggested refresh order (dependency chain):**
```
    1. hcp_xref           (identity bridge — refresh first if segments changed)
          │
          ├──► 2a. fact_attendance    (events — independent of Rx)
          ├──► 2b. fact_calls         (calls — independent of Rx)
          ├──► 2c. fact_rx_hcp_week   (NBRx — from v6, filtered by rx_matchable)
          └──► 2d. fact_trx_hcp_month (TRx — from Xponent, filtered by rx_matchable)
                        │
                        ▼
               3. pre_post_lift       (derived from attendance + Rx)
```

**Long-term:** The original notebook is lost. Create a consolidated refresh notebook that:
1. Documents each CTAS query with source table, filters, and join logic
2. Accepts a parameter for the v6 table version (in case v7/v8 is published)
3. Logs refresh timestamps and row counts for auditability
4. Can be scheduled as a monthly Lakeflow Job after each NBA alert cycle