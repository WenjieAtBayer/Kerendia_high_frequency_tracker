# Kerendia P2P NBA Speaker Program — Metric View Design Document

> **Catalog:** `ph-com-ai-us-prod-catalog-2553213839599380.sp_poc`  
> **Views:** `mv_speaker_nba` · `mv_speaker_nba_rx`  
> **Last updated:** October 20, 2026

---

## 1. Initiative Overview

The Kerendia P2P (Peer-to-Peer / Speaker Program) **NBA (Next Best Action)** initiative publishes a monthly **NBA dropdown list** in Veeva that recommends HCPs for speaker program invitations. The list is published on the 7th of each month (the NBA cycle date). The **universe** for both metric views is all Segment A and B HCPs (`CALL_PLAN_SEGMENT IN ('A_High_Potential_Writer', 'B_High_Potential_Non_Writer')`) present in each monthly cycle of the NBA list source table. Within that universe:

- **NBA** (`is_nba = TRUE`, `nba_group = 'NBA'`): HCPs on the NBA dropdown list (`ALERT_FLAG = 1`) in that cycle — the system's top recommendations.
- **Not NBA** (`is_nba = FALSE`, `nba_group = 'Not NBA'`): Segment A/B HCPs who were *not* on the NBA dropdown list in that cycle. They serve as a concurrent same-segment comparison group, anchored to the same cycle date.

NBA coverage of the A/B universe is approximately 14% (July) to 20% (August onward).

The reporting goal is end-to-end visibility from the NBA dropdown list to prescription impact, with the ability to compare NBA HCPs against Segment A/B peers not on the list:

```
Segment A/B Universe → NBA vs Not NBA → Invitation Sent → Program Attendance → NBRx / New Writer
```

---

## 2. Source Data

| Table | Schema | Grain | Key Columns |
|-------|--------|-------|-------------|
| `kerendia_sp_nba_integration_alerts` (NBA dropdown list source; table name is legacy) | `kerendia_nba_3` | 1 row per HCP × territory × scenario | `NPI_NUMBER` (double), `ALERT_DATE` (string), `ALERT_FLAG` (0 or 1), `CALL_PLAN_SEGMENT` |
| `fact_attendance` | `sp_poc` | 1 row per NPI × event | `npi` (string), `event_date`, `attended_flag` (boolean) |
| `fact_rx_hcp_week` | `sp_poc` | 1 row per NPI × week | `npi`, `week_ending_date`, `nbrx` |

**NPI join key:** `CAST(CAST(NPI_NUMBER AS BIGINT) AS STRING)` — the NBA list source stores NPI as `DOUBLE`, requiring two-step cast to match the `STRING` NPI in other tables.

**NBA list deduplication:** The NBA list source table contains rows for all segments (A, B, C, D, E, and NULL) with both `ALERT_FLAG = 0` (not on the NBA list) and `ALERT_FLAG = 1` (on the NBA list). The metric views filter to Segment A/B only and deduplicate to 1 row per NPI × cycle using `GROUP BY npi, alert_date, alert_month` with `MAX(ALERT_FLAG)` to determine NBA status and `FIRST()` for segment, specialty, region, and area (these never vary across an HCP's rows). Per-cycle totals: ~26k–31k A/B HCPs per month, of which ~4,300–6,200 are on the NBA dropdown list.

**Shared HCPs and territory (updated Oct 20, 2026):** About 80% of NBA HCPs are aligned to 2–4 territories (`TERR_ID`), and each aligned territory sees the HCP on its own list. The earlier `FIRST(TERR_DESC) AS territory` picked one territory arbitrarily and has been removed. HCP-grain views now expose `aligned_territories`, `n_aligned_territories`, and `is_shared_hcp`. Territory analysis uses the new `mv_speaker_nba_territory` (see the Territory Adoption addendum at the end).

---

## 3. Decision Log

### 3.1 Why two metric views?

| Question | Answer |
|----------|--------|
| Can `mv_speaker_lift` (existing) cover NBA? | No — it anchors pre/post windows to the **event date**, not the NBA cycle date. It also only covers the invited cohort, not the full population on the NBA dropdown list. |
| Should we extend `mv_speaker_nba` with Rx? | Source SQL would become prohibitively complex with a three-way join (NBA list × attendance × weekly Rx). Separate views keep each focused. |

**Decision:** Two views — `mv_speaker_nba` for the invitation/attendance funnel, `mv_speaker_nba_rx` for Rx effectiveness.

### 3.2 Invitation window: 30 days vs 60 days

Analysis of the July 2026 NBA dropdown list showed:

| Window | NPIs Invited | NPIs Attended |
|--------|-------------|---------------|
| 30 days | 17 | 5 |
| 60 days | 43 | 12 |
| Any time after cycle date | 59 | 15 |

The 60-day window captures 2.5× more invitations. However, for early-read purposes, 30 days is sufficient as a "quick signal" indicator.

**Decision for `mv_speaker_nba`:** Include both 30d and 60d windows for invitations and attendance.

### 3.3 Rx window: 4 weeks vs 12 weeks

Rx data (`fact_rx_hcp_week`) lags — as of October 2026 it extends only to August 28, 2026. A 12-week post-window for the July cycle requires data through late September.

**Decision:** Dual-window design in `mv_speaker_nba_rx`:
- **4-week (early read)** — provides actionable signal within ~6 weeks of the cycle date
- **12-week (mature)** — the definitive measurement once data coverage is complete

### 3.4 Attendance window for mature metrics: 30 days → 60 days

The earlier funnel analysis showed that widening the attendance window from 30 to 60 days more than doubled the ATTENDED cohort (5 → 12 NPIs for July) while the invite-to-attend conversion rate remained stable (~28–30%).

**Decision:** The 12-week mature metrics use a **60-day attendance window** (vs 30-day for the early read), giving the full pipeline more time to complete.

### 3.5 Adaptive post-anchor

The post-Rx measurement window should not always start from the NBA cycle date. An HCP who attended a program 25 days after the cycle date needs their post-NBRx measured from the event, not from 25 days earlier.

**Decision:** `post_anchor_date` adapts per HCP:
- First attended event date (if attended) → first invite date (if invited only) → NBA cycle date (if never invited)

### 3.6 Not NBA comparison group

To evaluate whether the NBA dropdown list itself adds value, we need a concurrent comparison group of similar HCPs who were *not* on it. The NBA list source table already contains `ALERT_FLAG = 0` rows for Segment A/B HCPs not selected by the model in each cycle, providing a natural comparison pool.

**Decision:** Expand the metric view universe from NBA-only (`ALERT_FLAG = 1`) to all Segment A/B HCPs per cycle. Derive:
- `is_nba = MAX(ALERT_FLAG) = 1` per NPI × cycle (boolean)
- `nba_group = CASE WHEN is_nba THEN 'NBA' ELSE 'Not NBA' END` (string)

Not NBA HCPs are anchored to the same cycle date (the 7th of each month) for all invite/attend/Rx windows, so windows are directly comparable. Segment is unique per NPI × cycle (verified: no NPI appears in both A and B within the same cycle).

### 3.7 Deduplication of `mv_speaker_nba`

The original `mv_speaker_nba` grouped by `npi, alert_date, alert_month, call_plan_segment, specialty, territory, region, area` but did not collapse the multiple scenario rows per HCP in the NBA list source table. This produced ~7,900–10,500 rows per month for ~4,300–6,200 distinct NPIs (1.8× inflation). Funnel counts were overstated — e.g., July showed 76 "invited" rows vs 43 actual NPIs invited (60d window).

**Decision:** Deduplicate the inner NBA list subquery to 1 row per NPI × cycle using `GROUP BY npi, alert_date, alert_month` with `FIRST()` for dimension columns. This aligns `mv_speaker_nba` with the grain of `mv_speaker_nba_rx` (which already deduplicated). The `fact_attendance` join is now restricted to `event_date BETWEEN alert_date AND alert_date + 60` for consistency.

---

## 4. Window Architecture

### 4.1 `mv_speaker_nba` — Invitation & Attendance Funnel

```
NBA Cycle Date (alert_date)
    │
    ├──── 30 days ────┤  ← invited_within_30d / attended_within_30d
    │                 │
    ├──────────── 60 days ────────────┤  ← invited_within_60d / attended_within_60d
    │                                 │
    ▼                                 ▼
 Jul 7                             Sep 5
```

Grain: 1 row per Segment A/B NPI × cycle date. Boolean flags for each window. Includes both HCPs on the NBA dropdown list and Segment A/B HCPs not on it; use `nba_group` to distinguish.

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

| NBA Cycle Month | 4w Coverage | 12w Coverage |
|-------------|-------------|--------------|
| July 2026 | **100%** | 0% (needs Sep 29 — 4 days short) |
| August 2026 | **96–100%** | 0% |
| September 2026 | 0% | 0% |
| October 2026 | 0% | 0% |

---

## 6. Early Findings (October 2026, updated October 20)

> **Open item — new-writer figures need reconfirmation (Oct 20, 2026):** The prior version of this section reported 2 new writers (40% NW rate) among July NBA ATTENDED HCPs and 70 among July NBA NOT_INVITED HCPs. Current `mv_speaker_nba_rx` output gives 0 and 6. The Oct 20 view change (Decisions 3.6–3.7) does **not** explain this: it expanded the universe and deduplicated `mv_speaker_nba`, but did not modify the new-writer logic (`is_new_writer_4w` / `12w`), and NBA lift values and cohort sizes still match the prior version. The source of the discrepancy is unresolved. Treat all New Writers and NW Rate values below (July and August, both groups) as **unconfirmed** until reconciled; lift and NPI counts are confirmed.

### July 2026 — 4-week early read (100% coverage), NBA vs Not NBA

| nba_group | Funnel Stage | NPIs | Avg 4w Lift | New Writers (unconfirmed) | NW Rate (unconfirmed) |
|-----------|-------------|------|-------------|-------------|--------|
| **NBA** | ATTENDED | 5 | **+2.60** | 0 | 0.0% |
| **NBA** | INVITED_ONLY | 12 | 0.00 | 1 | 8.3% |
| **NBA** | NOT_INVITED | 4,338 | +0.005 | 6 | 0.1% |
| Not NBA | ATTENDED | 19 | +0.32 | 4 | 21.1% |
| Not NBA | INVITED_ONLY | 62 | +0.24 | 3 | 4.8% |
| Not NBA | NOT_INVITED | 26,544 | +0.0002 | 24 | 0.1% |

Overall 4w lift: NBA +0.008 vs Not NBA +0.001.

### August 2026 — 4-week early read (96–100% coverage), NBA vs Not NBA

| nba_group | Funnel Stage | NPIs | Avg 4w Lift | New Writers (unconfirmed) | NW Rate (unconfirmed) |
|-----------|-------------|------|-------------|-------------|--------|
| **NBA** | ATTENDED | 10 | **+0.40** | 0 | 0.0% |
| **NBA** | INVITED_ONLY | 25 | +0.08 | 1 | 4.0% |
| **NBA** | NOT_INVITED | 6,225 | +0.013 | 18 | 0.3% |
| Not NBA | ATTENDED | 29 | +0.21 | 2 | 6.9% |
| Not NBA | INVITED_ONLY | 60 | +0.22 | 1 | 1.7% |
| Not NBA | NOT_INVITED | 24,856 | +0.005 | 28 | 0.1% |

Overall 4w lift: NBA +0.013 vs Not NBA +0.005.

**Key insight:** NBA ATTENDED cohorts show the largest lift (+2.60 in July, +0.40 in August). Not NBA ATTENDED HCPs also show positive lift (+0.32 and +0.21) but smaller than NBA, suggesting NBA flagging may identify higher-potential HCPs. Both groups dramatically outperform their respective NOT_INVITED baselines.

### NBA List-to-Invite Funnel (all months, 60-day window, NBA vs Not NBA)

| NBA Cycle Month | Group | NPIs | Invited | Attended | Invite Rate | Invite-to-Attend |
|-------------|-------|------|---------|----------|-------------|-------------------|
| July 2026 | **NBA** | 4,355 | 43 | 12 | 0.99% | 28% |
| July 2026 | Not NBA | 26,625 | 178 | 51 | 0.67% | 29% |
| August 2026 | **NBA** | 6,260 | 51 | 11 | 0.81% | 22% |
| August 2026 | Not NBA | 24,945 | 141 | 44 | 0.57% | 31% |
| September 2026 | **NBA** | 6,150 | 18 | 2 | 0.29% | 11% |
| September 2026 | Not NBA | 24,215 | 52 | 15 | 0.21% | 29% |
| October 2026 | **NBA** | 6,152 | 0 | 0 | Too early | Too early |
| October 2026 | Not NBA | 24,249 | 0 | 0 | Too early | Too early |

NBA HCPs have a slightly higher invite rate than Not NBA peers (<1% vs ~0.2–0.7%), though both are low due to speaker program capacity constraints. Once invited, invite-to-attend conversion is similar (~22–31%) across both groups.

### Top Territories

New Orleans (S LA Striker, W LA), Phoenix Central, and Mid-Atlantic showed the best end-to-end conversion from the NBA dropdown list to actual attendance. *(Note: this territory ranking was based on the old arbitrary territory pick; re-check with `mv_speaker_nba_territory`.)*

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
| Dimension | `npi`, `alert_date`, `alert_month` | HCP, cycle date, cycle month |
| Dimension | `is_nba` / `nba_group` | NBA flag (boolean) / group label ('NBA' or 'Not NBA') |
| Dimension | `call_plan_segment` | A or B segment |
| Dimension | `specialty` | HCP specialty |
| Dimension | `aligned_territories` / `n_aligned_territories` / `is_shared_hcp` | All territories with the HCP on their NBA dropdown list (replaces the removed `territory`) |
| Dimension | `inviting_territory` / `inviting_rep` | Veeva event owner territory and rep for the HCP's first invite within 60d |
| Dimension | `invited_by_aligned_territory_30d` / `_60d` | Invited to an event owned by a territory that has the HCP on its list |
| Dimension | `region` / `area` | Sales geography |
| Dimension | `invited_within_30d` / `60d` | Invitation flag |
| Dimension | `attended_within_30d` / `60d` | Attendance flag |
| Measure | `hcp_cycles` | Total A/B HCP x cycle rows |
| Measure | `npis_universe` | Distinct A/B NPIs (NBA + Not NBA) |
| Measure | `alerts` / `npis_alerted` | Rows / distinct NPIs on the NBA dropdown list (FILTER WHERE is_nba). Column names are legacy; display names are "NBA HCP-Cycles" / "NBA HCPs" |
| Measure | `npis_not_nba` | Distinct NPIs not on the NBA dropdown list |
| Measure | `nba_coverage_rate` | Share of A/B universe on the NBA dropdown list |
| Measure | `shared_hcps`, `invitations_by_aligned_territory_60d`, `pct_invites_from_aligned_territory_60d` | Shared-HCP count and share of invites sent by a territory that has the HCP on its list |
| Measure | `invitations_sent_30d` / `60d` | Invited HCP x cycle rows (generic; split by nba_group) |
| Measure | `invitation_rate_30d` / `60d` | Invite % (generic; split by nba_group) |
| Measure | `programs_attended_30d` / `60d` | Attended HCP x cycle rows (generic; split by nba_group) |
| Measure | `attendance_rate_30d` / `60d` | Attend % (generic; split by nba_group) |
| Measure | `invite_to_attend_30d` / `60d` | Invite-to-attend conversion % |

### `mv_speaker_nba_rx`

| Type | Name | Description |
|------|------|-------------|
| Dimension | `is_nba` / `nba_group` | NBA flag / group label (same as mv_speaker_nba) |
| Dimension | `funnel_stage` | Early-read cohort (30d/30d) |
| Dimension | `funnel_stage_12w` | Mature cohort (30d/60d) |
| Dimension | `is_new_writer_4w` / `12w` | New writer flag |
| Dimension | `post_4w_complete` / `post_12w_complete` | Rx coverage flag |
| Measure | `npis` / `npis_nba` / `npis_not_nba` | Distinct NPIs: universe / NBA / Not NBA |
| Measure | `avg_nbrx_lift_4w` / `12w` | Average NBRx lift (generic; split by nba_group) |
| Measure | `new_writer_rate_4w` / `12w` | New writer conversion % (generic; split by nba_group) |
| Measure | `pct_4w_covered` / `pct_12w_covered` | Data coverage % |

**Note:** Funnel counts, rates, and Rx measures in both views are generic over the current slice. Group or filter by `nba_group` to compare NBA vs Not NBA. Dashboard widgets that previously showed NBA-only numbers must add `WHERE nba_group = 'NBA'`.

---

## 8. Genie Space Integration

Both views are added to the **Kerendia Speaker Program Impact + NBA** Genie space (`01f1c9939e8a1648bbc09df186d37134`) with:
- 5 text instructions covering initiative context, usage guidance, and funnel semantics
- 5 SQL examples for common questions
- 8 starter questions spanning all four reporting areas

All views use **MEASURE() syntax** for aggregation queries.

---

## 9. Data Lineage & Refresh Maintenance

> **Full details:** See [SP_POC_Refresh_Maintenance.md](/editor/files/2185703631386938) for the complete refresh guide including ETL logic, dependency graph, refresh procedures, and refresh log.
>
> **Refresh notebook:** [SP_POC_Refresh](/editor/notebooks/2185703631386936)

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
| `fact_attendance` | New speaker program events | Monthly (after each NBA cycle) | hcp_xref (for segment/territory) |
| `dim_event_owner` | Veeva event owner (rep) and territory | Weekly (SP_POC_Refresh) | cph_db_prod.ANALYTICS_V2.DOMAIN_DP_FACT_EVENTS_ACTIVITY |
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
4. Can be scheduled as a monthly Lakeflow Job after each NBA cycle
---

## Addendum: Territory Adoption — `mv_speaker_nba_territory` (Oct 20, 2026)

**Question:** How many reps (territories) act on their NBA dropdown list?

**Problem:** HCPs are shared. About 80% of NBA HCPs are aligned to 2–4 territories (`TERR_ID`), and any of them can invite the HCP. `fact_attendance.territory` is the HCP's single primary alignment, not the inviter.

**Inviting rep source:** `cph_db_prod.ANALYTICS_V2.DOMAIN_DP_FACT_EVENTS_ACTIVITY` (Veeva). `TERRITORY_NAME` and `EMPLOYEE_NAME` are event-level: the **event owner**, i.e. the rep who requested the speaker program. QC: territory never varies across attendees of one event; `EVENT_ID` joins 100% to `fact_attendance.event_id`; 252 of 253 events since July 2026 have an owner territory; the 4-character code (e.g. `124B` in `124B - Downey, CA Iss`) matches `TERR_ID` in the NBA list. Materialized as `sp_poc.dim_event_owner` (event_id, owner_territory_id, owner_territory, owner_territory_type, owner_rep, owner_employee_id, team_member_count), refreshed in SP_POC_Refresh.

**View:** `mv_speaker_nba_territory`, grain = 1 row per NPI × cycle date × aligned territory (`TERR_ID <> 'UNASSIGNED'`).

| Type | Name | Description |
|------|------|-------------|
| Dimension | `territory_id`, `territory`, `region`, `area` | Aligned territory (proxy for rep) |
| Dimension | `nba_group`, `call_plan_segment`, `alert_month` | Same as other NBA views |
| Dimension | `invited_by_this_territory_30d` / `_60d` | This territory owned an event the HCP was invited to within the window |
| Dimension | `invited_any_60d`, `is_shared_hcp`, `n_aligned_territories` | Invited by anyone; sharing |
| Measure | `territories` | Distinct territories with HCPs on their list |
| Measure | `territories_acting_30d` / `_60d` | Distinct territories that invited at least one HCP on their own list to an event they own |
| Measure | `territory_action_rate_30d` / `_60d` | territories_acting / territories |
| Measure | `territories_with_attendee_60d` | Territories with a listed HCP who attended one of their events |
| Measure | `hcps_on_list`, `hcp_territory_assignments`, `avg_hcps_per_territory` | List size |
| Measure | `hcps_invited_60d`, `hcps_invited_by_aligned_territory_60d` | Distinct HCPs invited by anyone / by an aligned territory |

**Results (NBA, 60d):** July 26 of 693 territories acted (3.8%), August 29 of 666 (4.4%), September 11 of 656 (1.7%, window incomplete). 67–78% of invited NBA HCPs were invited by a territory that has them on its list.

**Limitations:** Credit goes to the event owner; co-hosts can also add attendees, but the per-attendee inviter isn't recorded. Territory is a proxy for the rep.

**Rollback:** Prior DDL of `mv_speaker_nba` and `mv_speaker_nba_rx` is saved in `sp_poc._mv_ddl_backup`.
