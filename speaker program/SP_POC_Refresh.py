# Databricks notebook source
# DBTITLE 1,Configuration
# SP_POC Refresh Notebook
# Refreshes managed tables in ph-com-ai-us-prod-catalog-2553213839599380.sp_poc
# from their upstream sources.
#
# Refresh order:  hcp_xref (if needed) → fact tables (parallel) → pre_post_lift
# 
# Tables refreshable from this notebook (UC-to-UC):
#   - fact_rx_hcp_week   (from kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6)
#   - pre_post_lift      (derived from fact_attendance + fact_rx_hcp_week + fact_calls)
#
# Tables requiring Snowflake access (run Nicholas's original pipeline):
#   - hcp_xref           (Foundation/MDM)
#   - fact_attendance     (CPH_DB_PROD.ANALYTICS_V2)
#   - fact_calls          (Lynkuet/Veeva)
#   - fact_trx_hcp_month  (Xponent)

CATALOG = "ph-com-ai-us-prod-catalog-2553213839599380"
SCHEMA = "sp_poc"
V6_TABLE = f"{CATALOG}.kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6"

# COMMAND ----------

# DBTITLE 1,Pre-refresh audit: current table state
# MAGIC %sql
# MAGIC -- Snapshot current state for comparison after refresh
# MAGIC SELECT 'fact_rx_hcp_week' AS tbl, COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis, 
# MAGIC        CAST(MAX(week_ending_date) AS STRING) AS max_date, SUM(nbrx) AS total_nbrx
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week
# MAGIC UNION ALL
# MAGIC SELECT 'pre_post_lift', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(anchor_dt) AS STRING), SUM(post_nbrx_12wk)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.pre_post_lift

# COMMAND ----------

# DBTITLE 1,Refresh fact_rx_hcp_week from v6
# MAGIC %sql
# MAGIC -- ETL: kerendia_laad_based_lrx_v6 → fact_rx_hcp_week
# MAGIC -- Join: v6.NPI = hcp_xref.npi (v6.PROVIDER_ID is IQVIA ID, NOT NPI)
# MAGIC -- Filters: PRODUCT_GROUP='KERENDIA', PAY_TYPE!='CASH', PERIOD_TYPE IN ('W','X'), rx_matchable=TRUE
# MAGIC -- Aggregation: SUM(NBRX) GROUP BY npi, week_ending_date, indication_group
# MAGIC
# MAGIC CREATE OR REPLACE TABLE `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week AS
# MAGIC SELECT
# MAGIC   v6.NPI AS npi,
# MAGIC   v6.PERIOD_ID AS week_ending_date,
# MAGIC   v6.INDICATION_GROUP AS indication_group,
# MAGIC   SUM(v6.NBRX) AS nbrx
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6 v6
# MAGIC INNER JOIN `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.hcp_xref x
# MAGIC   ON v6.NPI = x.npi AND x.rx_matchable = TRUE
# MAGIC WHERE v6.PRODUCT_GROUP = 'KERENDIA'
# MAGIC   AND v6.PAY_TYPE != 'CASH'
# MAGIC   AND v6.PERIOD_TYPE IN ('W', 'X')
# MAGIC GROUP BY v6.NPI, v6.PERIOD_ID, v6.INDICATION_GROUP

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
# MAGIC   SELECT npi, anchor_dt, COUNT(DISTINCT call_nm) AS calls_30d
# MAGIC   FROM (
# MAGIC     SELECT fc.npi, fc.call_nm, fc.call_date, wa.anchor_dt
# MAGIC     FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_calls fc
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

# DBTITLE 1,Post-refresh validation
# MAGIC %sql
# MAGIC -- Compare refreshed state
# MAGIC SELECT 'fact_rx_hcp_week' AS tbl, COUNT(*) AS rows, COUNT(DISTINCT npi) AS npis,
# MAGIC        CAST(MAX(week_ending_date) AS STRING) AS max_date, SUM(nbrx) AS total_nbrx
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.fact_rx_hcp_week
# MAGIC UNION ALL
# MAGIC SELECT 'pre_post_lift', COUNT(*), COUNT(DISTINCT npi), CAST(MAX(anchor_dt) AS STRING), SUM(post_nbrx_12wk)
# MAGIC FROM `ph-com-ai-us-prod-catalog-2553213839599380`.sp_poc.pre_post_lift

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