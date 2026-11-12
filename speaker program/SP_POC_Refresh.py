# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Configuration
# SP_POC Refresh Notebook
# Refreshes managed tables in ph-com-ai-us-prod-catalog-2553213839599380.sp_poc
# from their upstream sources.
#
# Owner: Wenjie Chen (as of Nov 2026). Full pipeline now runs from this notebook.
#
# Refresh order:  fact_attendance → hcp_xref → dim_event_owner → fact_rx_hcp_week → pre_post_lift
#
# Tables refreshed from this notebook:
#   - hcp_xref           (from kerendia_metric_views.fact_calls NPI-BH_ID bridge + dim_call_plan_target + V7 rx_matchable)
#   - fact_attendance     (from cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM via Snowflake federation)
#   - dim_event_owner     (from ANLT_BASE_FACT_EVNT_PRSNL_PROM SALE_ORG_NM — event-level owner territory)
#   - fact_rx_hcp_week   (from kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7)
#   - pre_post_lift      (derived from fact_attendance + fact_rx_hcp_week + kerendia_metric_views.fact_calls)
#
# Tables replaced by kerendia_metric_views (no longer in sp_poc):
#   - fact_calls          → kerendia_metric_views.fact_calls (Veeva via cph_db_prod federation)
#   - fact_trx_hcp_month  → kerendia_metric_views.fact_xponent_trx (Xponent via phcdw federation)

CATALOG = "ph-com-ai-us-prod-catalog-2553213839599380"
SCHEMA = "sp_poc"
V7_TABLE = f"{CATALOG}.kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7"
MV_SCHEMA = f"{CATALOG}.kerendia_metric_views"

# COMMAND ----------

# DBTITLE 1,Refresh fact_attendance from Veeva federation
# ETL: cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM → fact_attendance
# One row per HCP per Kerendia speaker event, via Snowflake federation (cph_db_prod).
# Source has event-level SALE_ORG_NM (owner territory) and HCP attributes.
# Nov 2026: Previously required Nicholas's Snowflake pipeline. Now refreshed directly via federation.
#
# GUARD: Check source row count before overwriting (same pattern as dim_event_owner).

_src_count = spark.sql("""
  SELECT COUNT(*) AS n
  FROM cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
  WHERE UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'
    AND HCP_NPI_NUM IS NOT NULL
    AND EVNT_START_DATE >= '2025-01-01'
""").collect()[0][0]

if _src_count > 0:
    print(f"Source has {_src_count} rows — refreshing fact_attendance")
    spark.sql("""
    CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance AS
    WITH base AS (
      SELECT
        HCP_NPI_NUM AS npi,
        EVNT_ID AS event_id,
        CAST(EVNT_START_DATE AS DATE) AS event_date,
        DATE_TRUNC('week', CAST(EVNT_START_DATE AS DATE)) AS week_ending_date,
        EVNT_TYP AS event_type,
        EVNT_FMT AS format,
        EVNT_TPIC_NM AS topic_raw,
        CASE WHEN UPPER(ATND) LIKE '%ATTEND%' THEN TRUE ELSE FALSE END AS attended_flag,
        CASE WHEN HCP_CALL_PLAN_TRGT_FLAG = 1 THEN TRUE ELSE FALSE END AS is_target,
        HCP_BAYER_SEG AS kerendia_segment,
        HCP_PRMRY_SPCL AS specialty,
        SALE_ORG_LVL_3_NM AS region,
        SALE_ORG_LVL_1_NM AS area,
        SALE_ORG_NM AS territory
      FROM cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
      WHERE UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'
        AND HCP_NPI_NUM IS NOT NULL
        AND EVNT_START_DATE >= '2025-01-01'
    ),
    classified AS (
      SELECT
        npi, event_id, event_date, week_ending_date, event_type, format, topic_raw,
        attended_flag, is_target, kerendia_segment, specialty, region, area, territory,
        CASE
          WHEN UPPER(topic_raw) LIKE '%CKD%' OR UPPER(topic_raw) LIKE '%CHRONIC KIDNEY%' THEN 'CKD'
          WHEN UPPER(topic_raw) LIKE '%HF%' OR UPPER(topic_raw) LIKE '%HEART FAILURE%' THEN 'HF'
          ELSE 'Other'
        END AS indication
      FROM base
    ),
    enriched AS (
      SELECT
        c.*,
        MIN(CASE WHEN attended_flag = TRUE THEN event_date END) OVER (PARTITION BY npi) AS first_attend_dt,
        SUM(CASE WHEN attended_flag = TRUE THEN 1 ELSE 0 END) OVER (PARTITION BY npi) AS exposure_count
      FROM classified c
    )
    SELECT * FROM enriched
    """)
    _result = spark.sql("SELECT COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis, CAST(MAX(event_date) AS STRING) AS max_date FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance").collect()[0]
    print(f"fact_attendance refreshed: {_result['rows']} rows, {_result['npis']} NPIs, max date {_result['max_date']}")
else:
    _existing = spark.sql("SELECT COUNT(*) FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance").collect()[0][0]
    print(f"WARNING: Snowflake source returned 0 rows — skipping fact_attendance refresh. Existing table has {_existing} rows.")

# COMMAND ----------

# DBTITLE 1,Rebuild hcp_xref from metric views
# ETL: Rebuild hcp_xref from fact_attendance + dim_call_plan_target + V7
# Base: all NPIs from fact_attendance (HCPs invited to Kerendia speaker programs — attendees + non-attendees).
# Enrichment: segment, territory, region, area from dim_call_plan_target (latest quarter Q3 or Q4).
# rx_matchable: NPIs with Kerendia Rx data in V7.
# Nov 2026: Previously required Nicholas's Snowflake MDM pipeline. Now built from UC + federation sources.
# NOTE: fact_attendance must be refreshed BEFORE this cell.

spark.sql("""
CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref AS
WITH att_npis AS (
  -- Speaker program universe: all HCPs who appear in fact_attendance (attended + non-attended)
  SELECT DISTINCT npi,
    MAX(specialty) AS specialty,
    MAX(region) AS region,
    MAX(area) AS area,
    MAX(territory) AS territory
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
  WHERE npi IS NOT NULL
  GROUP BY npi
),
bridge AS (
  -- NPI ↔ BH_ID bridge from call activity (for joining to call plan targets)
  SELECT npi, MAX(bh_id) AS bh_id
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_metric_views.fact_calls
  WHERE npi IS NOT NULL AND bh_id IS NOT NULL
  GROUP BY npi
),
plan_targets AS (
  -- Latest quarter targets per BH_ID (prefer Q4, fall back to Q3)
  SELECT bh_id, segment, territory, region, area, territory_id, plan_quarter,
    ROW_NUMBER() OVER (PARTITION BY bh_id ORDER BY plan_quarter DESC) AS rn
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_metric_views.dim_call_plan_target
  WHERE plan_quarter IN ('2026Q3', '2026Q4')
),
rx_npis AS (
  -- NPIs with Kerendia Rx data in V7 (rx_matchable = TRUE)
  SELECT DISTINCT NPI
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7
  WHERE PRODUCT_GROUP = 'KERENDIA' AND PERIOD_TYPE IN ('W', 'X') AND NBRX > 0
)
SELECT
  a.npi,
  b.bh_id,
  pt.segment AS kerendia_segment,
  a.specialty,
  TRUE AS target_flag,
  COALESCE(pt.territory, a.territory) AS territory,
  COALESCE(pt.region, a.region) AS region,
  COALESCE(pt.area, a.area) AS area,
  CASE WHEN rx.NPI IS NOT NULL THEN TRUE ELSE FALSE END AS rx_matchable
FROM att_npis a
LEFT JOIN bridge b ON a.npi = b.npi
LEFT JOIN plan_targets pt ON b.bh_id = pt.bh_id AND pt.rn = 1
LEFT JOIN rx_npis rx ON a.npi = rx.NPI
""")

_result = spark.sql("SELECT COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis, SUM(CASE WHEN rx_matchable THEN 1 ELSE 0 END) AS rx_matchable_count FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref").collect()[0]
print(f"hcp_xref rebuilt: {_result['rows']} rows, {_result['npis']} NPIs, {_result['rx_matchable_count']} rx_matchable")

# COMMAND ----------

# DBTITLE 1,Pre-refresh audit: current table state
# MAGIC %sql
# MAGIC -- Snapshot current state for comparison after refresh
# MAGIC SELECT 'hcp_xref' AS tbl, COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis,
# MAGIC        CAST(NULL AS STRING) AS max_date, SUM(CASE WHEN rx_matchable THEN 1 ELSE 0 END) AS extra_metric
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref
# MAGIC UNION ALL
# MAGIC SELECT 'fact_attendance', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(event_date) AS STRING), SUM(CASE WHEN attended_flag THEN 1 ELSE 0 END)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
# MAGIC UNION ALL
# MAGIC SELECT 'dim_event_owner', COUNT(*), COUNT(DISTINCT event_id), CAST(NULL AS STRING), CAST(NULL AS LONG)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.dim_event_owner
# MAGIC UNION ALL
# MAGIC SELECT 'fact_rx_hcp_week', COUNT(*), COUNT(DISTINCT npi),
# MAGIC        CAST(MAX(week_ending_date) AS STRING), SUM(nbrx)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week
# MAGIC UNION ALL
# MAGIC SELECT 'pre_post_lift', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(anchor_dt) AS STRING), SUM(post_nbrx_12wk)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.pre_post_lift

# COMMAND ----------

# DBTITLE 1,Refresh fact_rx_hcp_week from V7
# MAGIC %sql
# MAGIC -- ETL: kerendia_laad_based_lrx_v7 → fact_rx_hcp_week
# MAGIC -- Join: v7.NPI = hcp_xref.npi
# MAGIC -- Filters: PRODUCT_GROUP='KERENDIA', PERIOD_TYPE IN ('W','X'), rx_matchable=TRUE (cash-pay included)
# MAGIC -- Aggregation: SUM(NBRX) GROUP BY npi, week_ending_date, indication_group
# MAGIC -- Switched from V6 to V7 (Nov 2026): V7 is the source of truth, validated against lrx_nbrx.
# MAGIC
# MAGIC CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week AS
# MAGIC SELECT
# MAGIC   v7.NPI AS npi,
# MAGIC   v7.PERIOD_ID AS week_ending_date,
# MAGIC   v7.INDICATION_GROUP AS indication_group,
# MAGIC   SUM(v7.NBRX) AS nbrx
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7 v7
# MAGIC INNER JOIN `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref x
# MAGIC   ON v7.NPI = x.npi AND x.rx_matchable = TRUE
# MAGIC WHERE v7.PRODUCT_GROUP = 'KERENDIA'
# MAGIC   AND v7.PERIOD_TYPE IN ('W', 'X')
# MAGIC GROUP BY v7.NPI, v7.PERIOD_ID, v7.INDICATION_GROUP

# COMMAND ----------

# DBTITLE 1,Refresh dim_event_owner from attendance source
# ETL: dim_event_owner from ANLT_BASE_FACT_EVNT_PRSNL_PROM SALE_ORG_NM
# One row per Kerendia speaker event with the event owner territory.
# SALE_ORG_NM is event-level (verified: 1 per event), e.g. "A493 - Nashville, TN".
# The 4-char TERR_ID prefix matches the NBA dropdown list TERR_ID.
# Nov 2026: Previously used DOMAIN_DP_FACT_EVENTS_ACTIVITY (EMPLOYEE_NAME for rep name),
# but that table is inaccessible via federation (row-level security). Now derived from
# the attendance source which is accessible. owner_rep is not available from this source.
#
# GUARD: Check source row count before overwriting.

_src_count = spark.sql("""
  SELECT COUNT(DISTINCT EVNT_ID) AS n
  FROM cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
  WHERE UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'
    AND EVNT_START_DATE >= '2025-01-01'
    AND SALE_ORG_NM IS NOT NULL
""").collect()[0][0]

if _src_count > 0:
    print(f"Source has {_src_count} events — refreshing dim_event_owner")
    spark.sql("""
    CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.dim_event_owner
    COMMENT 'Kerendia speaker program events with event owner territory, derived from ANLT_BASE_FACT_EVNT_PRSNL_PROM SALE_ORG_NM via Snowflake federation. Join to fact_attendance on event_id. owner_territory_id matches the 4-character TERR_ID in the NBA dropdown list.'
    AS
    SELECT
      EVNT_ID AS event_id,
      MAX(TRIM(SPLIT(SALE_ORG_NM, ' - ')[0])) AS owner_territory_id,
      MAX(SALE_ORG_NM) AS owner_territory,
      MAX(SALE_ORG_LVL_1_NM) AS owner_area,
      MAX(FLD_FORCE_NM) AS owner_field_force,
      -- Backward-compat NULL columns (old DOMAIN_DP_FACT_EVENTS_ACTIVITY schema).
      -- mv_speaker_nba references o.owner_rep; keep these so CREATE OR REPLACE does not break it.
      CAST(NULL AS STRING) AS owner_rep,
      CAST(NULL AS STRING) AS owner_territory_type,
      CAST(NULL AS STRING) AS owner_employee_id,
      CAST(NULL AS INT) AS team_member_count
    FROM cph_db_prod.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
    WHERE UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'
      AND EVNT_START_DATE >= '2025-01-01'
      AND SALE_ORG_NM IS NOT NULL
    GROUP BY EVNT_ID
    """)
    _result = spark.sql("SELECT COUNT(*) AS rows, COUNT(DISTINCT event_id) AS events FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.dim_event_owner").collect()[0]
    print(f"dim_event_owner refreshed: {_result['rows']} events")
else:
    _existing = spark.sql("SELECT COUNT(*) FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.dim_event_owner").collect()[0][0]
    print(f"WARNING: Source returned 0 events — skipping dim_event_owner refresh. Existing table has {_existing} rows.")

# COMMAND ----------

# DBTITLE 1,Recompute pre_post_lift
# MAGIC %sql
# MAGIC -- Recompute per-NPI pre/post lift anchored to first attended event date.
# MAGIC -- anchor_dt: first_attend_dt (attended) or median of all first_attend_dt (control pseudo-anchor)
# MAGIC -- pre_nbrx_8wk: SUM(nbrx) in 8 weeks (56 days) before anchor
# MAGIC -- post_nbrx_12wk: SUM(nbrx) in 12 weeks (84 days) after anchor
# MAGIC -- new_writer: zero pre-12mo Rx AND any post Rx
# MAGIC -- calls_30d_post: distinct calls within 30 days after anchor
# MAGIC
# MAGIC CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.pre_post_lift AS
# MAGIC WITH cohort AS (
# MAGIC   SELECT
# MAGIC     x.npi,
# MAGIC     x.kerendia_segment,
# MAGIC     x.specialty,
# MAGIC     x.area,
# MAGIC     x.region,
# MAGIC     CASE WHEN a.attended_flag = TRUE THEN 1 ELSE 0 END AS is_attended,
# MAGIC     COALESCE(a.exposure_count, 0) AS exposure_count,
# MAGIC     a.first_attend_dt,
# MAGIC     a.event_date
# MAGIC   FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref x
# MAGIC   LEFT JOIN (
# MAGIC     SELECT npi, event_date, attended_flag, first_attend_dt, exposure_count
# MAGIC     FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
# MAGIC   ) a ON x.npi = a.npi
# MAGIC ),
# MAGIC -- One row per NPI: attended get their first_attend_dt, controls get the median
# MAGIC anchored AS (
# MAGIC   SELECT
# MAGIC     npi, kerendia_segment, specialty, area, region,
# MAGIC     MAX(CASE WHEN is_attended = 1 THEN 1 ELSE 0 END) AS is_attended,
# MAGIC     COALESCE(MAX(exposure_count), 0) AS exposure_count,
# MAGIC     CASE
# MAGIC       WHEN MAX(CASE WHEN is_attended = 1 THEN 1 ELSE 0 END) = 1 THEN UNIX_DATE(MIN(first_attend_dt))
# MAGIC       ELSE (
# MAGIC         SELECT PERCENTILE_APPROX(first_attend_dt_long, 0.5)
# MAGIC         FROM (
# MAGIC           SELECT DISTINCT npi AS n, UNIX_DATE(first_attend_dt) AS first_attend_dt_long
# MAGIC           FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
# MAGIC           WHERE attended_flag = TRUE AND first_attend_dt IS NOT NULL
# MAGIC         )
# MAGIC       )
# MAGIC     END AS anchor_dt_raw
# MAGIC   FROM cohort
# MAGIC   GROUP BY npi, kerendia_segment, specialty, area, region
# MAGIC ),
# MAGIC with_anchor AS (
# MAGIC   SELECT *, DATE_FROM_UNIX_DATE(CAST(anchor_dt_raw AS INT)) AS anchor_dt
# MAGIC   FROM anchored
# MAGIC   WHERE anchor_dt_raw IS NOT NULL
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC   w.npi,
# MAGIC   w.kerendia_segment,
# MAGIC   w.specialty,
# MAGIC   w.area,
# MAGIC   w.region,
# MAGIC   w.is_attended,
# MAGIC   w.exposure_count,
# MAGIC   w.anchor_dt,
# MAGIC   COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN DATE_ADD(w.anchor_dt, -56) AND DATE_ADD(w.anchor_dt, -1)
# MAGIC     THEN rx.nbrx END), 0) AS pre_nbrx_8wk,
# MAGIC   COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN w.anchor_dt AND DATE_ADD(w.anchor_dt, 84)
# MAGIC     THEN rx.nbrx END), 0) AS post_nbrx_12wk,
# MAGIC   COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN w.anchor_dt AND DATE_ADD(w.anchor_dt, 84)
# MAGIC     THEN rx.nbrx END), 0)
# MAGIC   - COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN DATE_ADD(w.anchor_dt, -56) AND DATE_ADD(w.anchor_dt, -1)
# MAGIC     THEN rx.nbrx END), 0) AS nbrx_delta,
# MAGIC   CASE WHEN COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN w.anchor_dt AND DATE_ADD(w.anchor_dt, 84)
# MAGIC     THEN rx.nbrx END), 0)
# MAGIC     - COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN DATE_ADD(w.anchor_dt, -56) AND DATE_ADD(w.anchor_dt, -1)
# MAGIC     THEN rx.nbrx END), 0) >= 1 THEN TRUE ELSE FALSE END AS pct_changed,
# MAGIC   CASE WHEN
# MAGIC     COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN DATE_ADD(w.anchor_dt, -365) AND DATE_ADD(w.anchor_dt, -1)
# MAGIC       THEN rx.nbrx END), 0) = 0
# MAGIC     AND COALESCE(SUM(CASE WHEN rx.week_ending_date BETWEEN w.anchor_dt AND DATE_ADD(w.anchor_dt, 84)
# MAGIC       THEN rx.nbrx END), 0) > 0
# MAGIC   THEN TRUE ELSE FALSE END AS new_writer,
# MAGIC   COALESCE(c.calls_30d, 0) AS calls_30d_post
# MAGIC FROM with_anchor w
# MAGIC LEFT JOIN `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week rx
# MAGIC   ON w.npi = rx.npi
# MAGIC LEFT JOIN (
# MAGIC   SELECT npi, anchor_dt, COUNT(DISTINCT call_name) AS calls_30d
# MAGIC   FROM (
# MAGIC     SELECT fc.npi, fc.call_name, fc.call_date, wa.anchor_dt
# MAGIC     FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_metric_views.fact_calls fc
# MAGIC     INNER JOIN (
# MAGIC       SELECT npi, MIN(first_attend_dt) AS anchor_dt
# MAGIC       FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
# MAGIC       WHERE attended_flag = TRUE
# MAGIC       GROUP BY npi
# MAGIC       UNION ALL
# MAGIC       SELECT DISTINCT x2.npi, DATE_FROM_UNIX_DATE(CAST((
# MAGIC         SELECT PERCENTILE_APPROX(UNIX_DATE(fa2.first_attend_dt), 0.5)
# MAGIC         FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance fa2
# MAGIC         WHERE fa2.attended_flag = TRUE AND fa2.first_attend_dt IS NOT NULL
# MAGIC       ) AS INT)) AS anchor_dt
# MAGIC       FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref x2
# MAGIC       WHERE NOT EXISTS (
# MAGIC         SELECT 1 FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance fa3
# MAGIC         WHERE fa3.npi = x2.npi AND fa3.attended_flag = TRUE
# MAGIC       )
# MAGIC     ) wa ON fc.npi = wa.npi
# MAGIC     WHERE fc.call_date BETWEEN wa.anchor_dt AND DATE_ADD(wa.anchor_dt, 30)
# MAGIC   )
# MAGIC   GROUP BY npi, anchor_dt
# MAGIC ) c ON w.npi = c.npi
# MAGIC GROUP BY w.npi, w.kerendia_segment, w.specialty, w.area, w.region,
# MAGIC          w.is_attended, w.exposure_count, w.anchor_dt, c.calls_30d

# COMMAND ----------

# DBTITLE 1,Post-refresh validation + view repoint notes
# MAGIC %sql
# MAGIC -- Compare refreshed state
# MAGIC SELECT 'hcp_xref' AS tbl, COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis,
# MAGIC        CAST(NULL AS STRING) AS max_date, SUM(CASE WHEN rx_matchable THEN 1 ELSE 0 END) AS extra_metric
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref
# MAGIC UNION ALL
# MAGIC SELECT 'fact_attendance', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(event_date) AS STRING), SUM(CASE WHEN attended_flag THEN 1 ELSE 0 END)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_attendance
# MAGIC UNION ALL
# MAGIC SELECT 'dim_event_owner', COUNT(*), COUNT(DISTINCT event_id), CAST(NULL AS STRING), CAST(NULL AS LONG)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.dim_event_owner
# MAGIC UNION ALL
# MAGIC SELECT 'fact_rx_hcp_week', COUNT(*), COUNT(DISTINCT npi),
# MAGIC        CAST(MAX(week_ending_date) AS STRING), SUM(nbrx)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week
# MAGIC UNION ALL
# MAGIC SELECT 'pre_post_lift', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(anchor_dt) AS STRING), SUM(post_nbrx_12wk)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.pre_post_lift
# MAGIC
# MAGIC -- Repoint intermediate views to kerendia_metric_views (requires MANAGE permission on views)
# MAGIC -- Run this cell from your session if the auto-refresh doesn't have permissions.
# MAGIC -- v_fact_calls: sp_poc.fact_calls → kerendia_metric_views.fact_calls (call_name AS call_nm)
# MAGIC -- v_fact_trx_hcp_month: sp_poc.fact_trx_hcp_month → kerendia_metric_views.fact_xponent_trx (CAST month_id AS STRING)

# COMMAND ----------

# DBTITLE 1,Verify NBA metric view coverage after refresh
# MAGIC %sql
# MAGIC -- Check updated coverage for mv_speaker_nba_rx
# MAGIC SELECT
# MAGIC   alert_month,
# MAGIC   funnel_stage,
# MAGIC   MEASURE(npis) AS npis,
# MAGIC   MEASURE(avg_nbrx_lift_4w) AS lift_4w,
# MAGIC   MEASURE(new_writers_4w) AS nw_4w,
# MAGIC   MEASURE(pct_4w_covered) AS cov_4w,
# MAGIC   MEASURE(avg_nbrx_lift_12w) AS lift_12w,
# MAGIC   MEASURE(new_writers_12w) AS nw_12w,
# MAGIC   MEASURE(pct_12w_covered) AS cov_12w
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.mv_speaker_nba_rx
# MAGIC GROUP BY alert_month, funnel_stage
# MAGIC ORDER BY alert_month, funnel_stage