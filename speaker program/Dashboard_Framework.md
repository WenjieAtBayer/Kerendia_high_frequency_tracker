# Kerendia Speaker Program High-Frequency Performance Tracker
## Dashboard Framework

**Objective:** Answer three fundamental questions about speaker program impact:
1. **Did behavior change?**
2. **How much did it change?**
3. **What factors drove the change?**

**Design principles:**
- Living tracker — refreshes automatically when upstream data updates (v6 weekly, attendance/calls monthly)
- NBA highlighted as a featured initiative within the broader program story
- Progressive disclosure — executive summary → category deep-dives → ad-hoc exploration (Genie space)
- Linked to Genie space for free-form Q&A beyond what the dashboard covers

---

## Page Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  P1  EXECUTIVE SUMMARY                                              │
│  "The story in 60 seconds"                                          │
│  KPIs + trend + NBA spotlight                                       │
├─────────────────────────────────────────────────────────────────────┤
│  P2  PROGRAM EFFECTIVENESS          ← Did behavior change?          │
│  Pre/post lift · new writers · Rx trend · 4w vs 12w                 │
├─────────────────────────────────────────────────────────────────────┤
│  P3  AUDIENCE SEGMENTATION          ← What factors drove it?        │
│  Segment A vs B · specialty · geography                             │
├─────────────────────────────────────────────────────────────────────┤
│  P4  FREQUENCY & EXPOSURE           ← How much did it change?       │
│  Dose-response · multi-event · rep follow-up                        │
├─────────────────────────────────────────────────────────────────────┤
│  P5  ENGAGEMENT JOURNEY             ← What's the conversion path?   │
│  Alert → invite → attend → Rx funnel · time-to-Rx                  │
├─────────────────────────────────────────────────────────────────────┤
│  P6  NBA INITIATIVE SPOTLIGHT       ← Is the newest initiative      │
│  NBA-specific funnel · lift · coverage · compared to overall        │
├─────────────────────────────────────────────────────────────────────┤
│  🔗  GENIE SPACE LINK                                               │
│  "Ask a question about this data" → Genie space for ad-hoc          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Metric Methodology & Rationale

Each page's header includes a methodology footnote. The rationale for metric selection:

**NBRx Lift** (P1, P2, P4): The primary outcome measure. Calculated as avg post-window NBRx/HCP minus avg pre-window NBRx/HCP using rolling monthly cohorts. Chosen over TRx because NBRx captures new prescribing decisions (behavioral change), while TRx includes refills (volume). The lift trend on P1 uses mv_speaker_lift which covers all programs, not just NBA.

**New-Writer Conversion** (P2, P6): For Segment B (non-writers), lift is meaningless (pre=0, post~0). Instead we measure whether they start prescribing at all. New writer = zero Kerendia NBRx in 12 months pre-event who wrote at least 1 script in the post-window.

**4-Week vs 12-Week Windows** (P6): 4w captures immediate signal (available sooner); 12w captures durable behavioral change (critical for Seg B who need more time to convert). Both shown on P6; P1-P4 use the overall program lift from mv_speaker_lift.

**Dose-Response / Exposure Bands** (P4): Tests whether repeat attendance amplifies lift. Based on exposure_band from mv_speaker_lift.

**Call Coverage** (P4): Measures rep follow-up within 30 days. Tests whether field reinforcement amplifies the program effect.

**NBA Funnel Counts** (P1, P5, P6): Absolute counts, not percentages, because invitation/attendance rates relative to the full A/B universe round to near zero. The invite-to-attend conversion (~23-30%) remains as a percentage because it is actionable. **All NBA funnel widgets must filter `nba_group = 'NBA'`** to show NBA-specific numbers; without this filter, counts include Not NBA HCPs.

**Caveats:**
- Small sample sizes for attended cohorts (5-17 HCPs per month)
- Segment B 4-week window likely understates conversion (non-writers need more time)
- Segment labels may be stale (7.8% of Seg B have recent Rx history)
- Oct data too recent for 60-day funnel completion

---

## Page 1: Executive Summary

**Purpose:** Give leadership the story in 60 seconds. Every metric links to a deeper page.

### KPI Cards (top row)

| KPI | Source | Definition |
|-----|--------|-----------|
| Programs Held (YTD) | mv_speaker_attendance | COUNT(DISTINCT event_id) WHERE attended_flag = TRUE |
| Unique Attendees | mv_speaker_attendance | COUNT(DISTINCT npi) WHERE attended_flag = TRUE |
| Target Reach Rate | mv_speaker_attendance + mv_segment_universe | attendees / target_universe_hcps |
| Avg NBRx Lift (Attended vs Control) | mv_speaker_lift | avg_post_nbrx - avg_pre_nbrx, attended vs not |
| New Writers (YTD) | mv_speaker_lift | SUM(new_writers) for attended cohort |
| NBA Alert-to-Attend Rate | mv_speaker_nba | attended / alerted (60d). **Filter: `nba_group = 'NBA'`** |

### Trend Chart
- Monthly NBRx lift trend (attended vs control) — mv_speaker_lift by anchor_month
- Overlay: monthly attendance count — mv_speaker_attendance by event_month

### NBA Spotlight Card
- Mini funnel: Alerted → Invited → Attended → Lift (latest month with coverage)
- "Learn more →" links to Page 6

### Data Freshness Indicator
- Last Rx data date, last attendance data date, coverage status by month

---

## Page 2: Program Effectiveness

**Question answered:** Did behavior change? How much?

### Widget 2a: Pre/Post NBRx Comparison (bar chart)
- Source: mv_speaker_lift
- X-axis: cohort_group (Attended / Control)
- Bars: avg_pre_nbrx vs avg_post_nbrx
- Annotation: lift delta
- Filter: segment_code, anchor_quarter

### Widget 2b: NBRx Lift by Quarter (line chart)
- Source: mv_speaker_lift
- X-axis: anchor_quarter
- Lines: attended lift vs control lift
- Shows whether lift is growing, stable, or declining over time

### Widget 2c: New-Writer Conversion (Segment B focus)
- Source: mv_speaker_nba_rx (for NBA cohort) + mv_speaker_lift (for overall)
- Funnel visual: total Seg B → attended → wrote first Rx
- Filter: alert_month or anchor_quarter

### Widget 2d: 4-Week vs 12-Week Comparison (when available)
- Source: mv_speaker_nba_rx
- Side-by-side: lift_4w vs lift_12w by funnel_stage
- Coverage indicator per cell
- Answers: "Is the early signal durable?"

### Widget 2e: TRx Trend (volume context)
- Source: mv_speaker_trx + v_national_trx_month
- Attended vs control TRx indexed to program start
- Overlay: national TRx for market context

---

## Page 3: Audience Segmentation

**Question answered:** What factors drove the change? Who responds best?

### Widget 3a: Lift by Segment (horizontal bar)
- Source: mv_speaker_lift
- Rows: segment_code (A, B, C, D, E)
- Metric: avg_lift (NBRx) for attended
- Highlights Segment A as strongest responder

### Widget 3b: New-Writer Rate by Segment (Segment B breakdown)
- Source: mv_speaker_nba_rx
- Segment B only, by funnel_stage
- Shows conversion potential for non-writers

### Widget 3c: Lift by Specialty (bar chart)
- Source: mv_speaker_lift
- Rows: specialty (CARD, PCP, NEPH, ENDO, OTHER)
- Metric: avg_lift for attended
- Answers: "Which specialties respond most to programs?"

### Widget 3d: Geographic Heatmap (map or treemap)
- Source: mv_speaker_lift or mv_speaker_nba_rx
- Color: lift or new-writer rate
- Drill: area → region → territory
- Identifies high-performing and underperforming territories

### Widget 3e: Segment Universe Coverage (donut)
- Source: mv_segment_universe + mv_speaker_attendance
- What % of each segment has been reached by a program?

---

## Page 4: Frequency & Exposure

**Question answered:** How much exposure drives the most change? Is there a dose-response?

### Widget 4a: Lift by Exposure Band (bar chart)
- Source: mv_speaker_lift
- X-axis: exposure_band (1 event, 2 events, 3+)
- Metric: avg_lift
- Answers: "Do repeat attendees show more lift?"

### Widget 4b: Multi-Program Attendance Rate (KPI + trend)
- Source: mv_speaker_lift
- multi_program_attendees / total attendees over time
- Answers: "Are we getting repeat exposure?"

### Widget 4c: Rep Follow-Up (call coverage)
- Source: mv_speaker_lift + mv_speaker_calls
- % of attendees called within 14 days / 30 days post-event
- call_coverage_30d by territory
- Answers: "Are reps reinforcing the program message?"

### Widget 4d: Program Format Comparison
- Source: mv_speaker_attendance + mv_speaker_lift
- Lift by format (In-Person, Virtual, Hybrid)
- Lift by indication (CKD vs HF)
- Answers: "Which format works best?"

---

## Page 5: Engagement Journey

**Question answered:** Where does the funnel leak? What's the conversion path?

### Widget 5a: Full Journey Funnel (funnel chart)
- Combines mv_segment_universe → mv_speaker_nba → mv_speaker_nba_rx
- Stages: Segment A/B Universe (npis_universe from mv_speaker_nba) → NBA Alerted (npis_alerted) → Invited → Attended → Wrote Rx → Sustained Writer. **Filter: `nba_group = 'NBA'` for NBA-specific stages.**
- Drop-off % at each stage

### Widget 5b: Time-to-First-Rx (histogram)
- Source: mv_speaker_nba_rx (post_anchor_date vs first post-window Rx date)
- Distribution of days from attendance to first new script
- Answers: "How quickly does the program effect materialize?"
- NOTE: Requires new derived column in view — not yet available

### Widget 5c: Invite Rate by Territory (ranked bar)
- Source: mv_speaker_nba
- invitation_rate_60d by territory, sorted descending. **Filter: `nba_group = 'NBA'`** or split by nba_group.
- Identifies territories that act on NBA alerts vs those that don't

### Widget 5d: Monthly Funnel Trend (stacked area)
- Source: mv_speaker_nba
- Monthly: alerted, invited, attended stacked. **Filter: `nba_group = 'NBA'`** or split by nba_group.
- Shows whether the pipeline is growing or shrinking

---

## Page 6: NBA Initiative Spotlight

**Purpose:** Dedicated deep-dive for the newest and most-watched initiative.

### Widget 6a: NBA Funnel (large, prominent)
- Source: mv_speaker_nba
- Monthly funnel: Alerted → Invited (60d) → Attended (60d)
- With invite rate and attend conversion annotations

### Widget 6b: NBA Lift vs Overall Program Lift (comparison)
- Source: mv_speaker_nba_rx (NBA cohort) vs mv_speaker_lift (all-program cohort)
- Side-by-side lift for attended HCPs
- Answers: "Is NBA-driven attendance more or less effective than organic?"

### Widget 6c: Segment A Lift Detail (NBA)
- Source: mv_speaker_nba_rx WHERE call_plan_segment = 'A_High_Potential_Writer'
- Pre/post NBRx with actual script counts
- By month, with coverage indicator

### Widget 6d: Segment B New-Writer Detail (NBA)
- Source: mv_speaker_nba_rx WHERE call_plan_segment = 'B_High_Potential_Non_Writer'
- New-writer conversion by funnel stage, by month
- 4w vs 12w comparison
- Caveat footnote on segment-label lag (7.8%)

### Widget 6f: NBA vs Not NBA Comparison
- Source: mv_speaker_nba (invite rate, invite-to-attend) + mv_speaker_nba_rx (4w lift, new-writer rate)
- Side-by-side by `nba_group`: invitation_rate_60d, invite_to_attend_60d, avg_nbrx_lift_4w, new_writer_rate_4w
- By alert_month (rows) and nba_group (columns)
- Answers: "Are NBA-flagged HCPs performing differently than their non-flagged Segment A/B peers?"

### Widget 6e: Coverage & Data Freshness
- Source: mv_speaker_nba_rx
- Heat grid: alert_month × funnel_stage → pct_4w_covered / pct_12w_covered
- Color: green (≥90%) → yellow (50-90%) → red (<50%)
- Answers: "Which metrics can I trust right now?"

---

## Cross-Cutting Filters (apply across all pages)

| Filter | Source | Values |
|--------|--------|--------|
| Time Period | Multiple | Quarter, Month, YTD, Rolling 12mo |
| Segment | mv_speaker_lift / mv_speaker_nba_rx | A, B, C, D, E / A_High_Potential_Writer, B_High_Potential_Non_Writer |
| Specialty | Multiple | CARD, PCP, NEPH, ENDO, OTHER |
| Geography | Multiple | Area → Region → Territory (drill-down) |
| NBA Group | mv_speaker_nba / mv_speaker_nba_rx | 'NBA', 'Not NBA' (filter or split) |
| Format | mv_speaker_attendance | In-Person, Virtual, Hybrid |
| Indication | mv_speaker_attendance | CKD, HF |

---

## Data Source Mapping

| Dashboard Widget Category | Primary Metric View(s) | Refresh Cadence |
|--------------------------|----------------------|-----------------|
| Attendance & reach | mv_speaker_attendance, mv_segment_universe | Monthly (Snowflake) |
| NBRx lift & new writers | mv_speaker_lift, mv_speaker_nba_rx | Weekly (v6 trigger) |
| TRx volume | mv_speaker_trx, v_national_trx_month | Monthly (Xponent) |
| Calls & follow-up | mv_speaker_calls | Monthly (Lynkuet) |
| NBA funnel | mv_speaker_nba | Monthly (alerts + attendance) |
| NBA Rx impact | mv_speaker_nba_rx | Weekly (v6 trigger) |
| Market context | v_national_nbrx_month, v_national_trx_month | Monthly |

---

## Gaps & Future Additions

| Gap | Impact | Resolution |
|-----|--------|-----------|
| Time-to-first-Rx post-attendance | Can't show distribution of days to first Rx | Add derived column to mv_speaker_nba_rx: MIN(rx.week_ending_date) in post-window |
| Sustained writer flag | Can't distinguish one-time vs repeat post-Rx | Add flag: post-window Rx in ≥2 distinct weeks |
| NBA vs organic comparison | ~~Can't compare NBA-driven vs non-NBA attendees~~ | **Resolved (Oct 20, 2026):** `nba_group` dimension in mv_speaker_nba and mv_speaker_nba_rx. Widget 6f shows side-by-side comparison. |
| Channel/format interaction | Limited format × indication × segment breakdown | May need a cross-tab metric view |
| Branded vs non-branded indication | mv_branded_non_branded exists but not in space | Add to space if CKD vs HF breakdown needed beyond attendance |

---

## Implementation Plan

| Phase | Scope | Pages | Timeline |
|-------|-------|-------|----------|
| **Phase 1** | Core story | P1 (Executive), P2 (Effectiveness), P6 (NBA Spotlight) | Week 1 |
| **Phase 2** | Segmentation & journey | P3 (Audience), P5 (Engagement Journey) | Week 2 |
| **Phase 3** | Depth & refinement | P4 (Frequency/Exposure), gap resolution | Week 3 |
| **Ongoing** | Growing tracker | New metrics, new months, 12w reads, additional initiatives | Continuous |

---

## Link to Genie Space

Every dashboard page should include a footer link:
> **Have a question not answered here?** [Ask the Genie space →](https://dbc-7281de76-54c6.cloud.databricks.com/genie/rooms/01f1c9939e8a1648bbc09df186d37134)

The Genie space supports free-form natural language queries across all 10 metric views, covering scenarios beyond the dashboard's fixed widgets.
