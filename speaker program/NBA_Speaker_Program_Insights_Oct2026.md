# Kerendia NBA × Speaker Program: Impact Insights
**Date:** October 19, 2026 (updated October 20, 2026) | **Prepared by:** Analytics & AI Team | **Data through:** September 25, 2026

---

## Executive Summary

The Next Best Action (NBA) engine has been flagging high-potential HCPs for speaker program engagement since July 2026. This report measures what happens when those flagged HCPs are actually invited to — and attend — a speaker program, compared to those who are not invited.

**Bottom line:** HCPs who attend a speaker program after an NBA alert show significantly higher prescribing activity than those who are not invited. The opportunity is clear — but the current bottleneck is the alert-to-invite conversion rate (<1% for NBA HCPs), not program effectiveness.

---

## 1. Why Two Windows: 4-Week Early Read vs. 12-Week Mature

We measure Rx impact over two time horizons because prescribing behavior doesn't change overnight:

**4-Week Early Read (this report)**
- Captures the *immediate* prescribing response in the first 28 days after the engagement event
- Available sooner — we can report on July and August today
- Useful for directional signals: "Is there any early evidence of impact?"
- Limitation: may understate the full effect — some HCPs take weeks to see their next eligible patient, consult formulary, or complete a prior authorization

**12-Week Mature Read (coming soon)**
- Captures the *durable* prescribing response over 84 days — enough time for 2–3 patient visit cycles
- Better for measuring sustained behavioral change vs. one-time curiosity scripts
- More statistically robust — averages out week-to-week prescribing noise
- Limitation: requires more Rx data to accumulate. July's 12-week window needs data through Sep 29 — we currently have Sep 25 (4 days short). The next v6 data refresh will unlock it.

**Why both matter:** If the 4-week early read shows a signal but the 12-week mature read does not, it suggests the program creates a temporary bump that fades. If both show lift, it suggests a genuine behavioral shift. We need the mature read to confirm durability.

---

## 2. The Funnel: From Alert to Attendance

> **Correction (Oct 20, 2026):** The funnel counts below have been corrected after deduplicating `mv_speaker_nba` to 1 row per NPI x cycle. The prior version had inflated numbers (e.g., July showed 76 invited / 23 attended) due to duplicate alert rows per HCP. The corrected NBA numbers and a new Not NBA comparison group are shown below.

| Month | Group | HCPs | Invited (60d) | Attended (60d) | Invite Rate | Invite-to-Attend |
|-------|-------|------|---------------|----------------|-------------|-------------------|
| July 2026 | **NBA** | 4,355 | 43 | 12 | **0.99%** | **28%** |
| July 2026 | Not NBA | 26,625 | 178 | 51 | 0.67% | 29% |
| August 2026 | **NBA** | 6,260 | 51 | 11 | **0.81%** | **22%** |
| August 2026 | Not NBA | 24,945 | 141 | 44 | 0.57% | 31% |
| September 2026 | **NBA** | 6,150 | 18 | 2 | 0.29% | 11% |
| September 2026 | Not NBA | 24,215 | 52 | 15 | 0.21% | 29% |
| October 2026 | Both | 30,401 | 0 | 0 | Too early | Too early |

**Takeaway:** Once an HCP is invited, roughly **1 in 4 attend** — a healthy conversion rate. The constraint is upstream: less than 1% of NBA-flagged HCPs receive a speaker program invitation within 60 days. Not NBA Segment A/B HCPs show a slightly lower invite rate (~0.2–0.7%) but a comparable invite-to-attend conversion (~29–31%). This confirms the bottleneck is program capacity, not NBA targeting specifically.

---

## 3. Prescribing Impact by Segment

> **Note:** The tables below cover **NBA HCPs only** (those with `nba_group = 'NBA'`). A Not NBA comparison is now available via the `nba_group` dimension in `mv_speaker_nba_rx`.

We report different metrics for each segment because they measure different things:

- **Segment A (High Potential Writer):** These HCPs already prescribe Kerendia. The question is whether attending a speaker program increases their *prescribing volume*. We measure **NBRx lift** — the change in new prescriptions per HCP.
- **Segment B (High Potential Non-Writer):** These HCPs have never written Kerendia (or not in the past 12 months). The question is whether attending a speaker program causes them to *start prescribing*. We measure **new-writer conversion** — the share of HCPs who write their first script.

### How Lift Is Calculated

> **NBRx Lift** = average post-window NBRx per HCP − average pre-window NBRx per HCP
>
> - **Pre-window:** total Kerendia new prescriptions (NBRx) in the 4 weeks (28 days) *before* the alert date
> - **Post-window:** total Kerendia new prescriptions (NBRx) in the 4 weeks (28 days) *after* the engagement anchor date (first attended date if attended; first invite date if invited only; alert date if not invited)
> - A positive lift means HCPs wrote more Kerendia after the event than before

### 3a. Segment A — Prescribing Lift (existing writers)

#### July 2026 (100% data coverage)

| Cohort | HCPs | Pre NBRx/HCP | Post NBRx/HCP | **Lift** | Total Post NBRx |
|--------|------|-------------|--------------|----------|-----------------|
| **Attended** | 5 | 1.40 | 4.00 | **+2.60** | **20** |
| Invited Only | 9 | 1.11 | 0.89 | −0.22 | 8 |
| Not Invited | 3,006 | 0.08 | 0.08 | +0.004 | 253 |

#### August 2026 (92–100% data coverage)

| Cohort | HCPs | Pre NBRx/HCP | Post NBRx/HCP | **Lift** | Total Post NBRx |
|--------|------|-------------|--------------|----------|-----------------|
| **Attended** | 4 | 1.00 | 2.25 | **+1.25** | **9** |
| Invited Only | 13 | 1.23 | 1.23 | 0.00 | 16 |
| Not Invited | 2,376 | 0.10 | 0.13 | +0.03 | 302 |

**What this means for Segment A:**
- July attendees nearly **tripled** their prescribing rate (1.40 → 4.00 NBRx per HCP), producing a per-HCP lift of +2.60 new scripts. That's 5 HCPs generating 20 total post-program scripts vs. 7 pre-program.
- August attendees more than **doubled** their rate (1.00 → 2.25), generating 9 total post-program scripts from just 4 HCPs.
- Invited-only and not-invited Segment A HCPs showed flat or near-zero lift, confirming the program attendance — not just the alert itself — is driving the change.

### 3b. Segment B — New-Writer Conversion (non-writers)

New writer = HCP with **zero Kerendia NBRx in the 12 months before the alert** who wrote at least one script in the 4-week post-window.

#### July 2026 (100% data coverage)

| Cohort | HCPs | New Writers | **NW Rate** | Post NBRx/HCP |
|--------|------|-------------|-------------|---------------|
| Invited Only | 3 | 1 | **33.3%** | 0.67 |
| Not Invited | 1,332 | 4 | 0.3% | 0.02 |

*(No Segment B HCPs attended a program in July)*

#### August 2026 (100% data coverage)

| Cohort | HCPs | New Writers | **NW Rate** | Post NBRx/HCP |
|--------|------|-------------|-------------|---------------|
| **Attended** | 6 | 0 | 0% | 0.17† |
| Invited Only | 12 | 1 | **8.3%** | 0.50 |
| Not Invited | 3,849 | 14 | 0.4% | 0.01 |

> **† Note on August ATTENDED (0 new writers, 0.17 post-NBRx):** One of the 6 attended HCPs is classified as Segment B "non-writer" in the call plan but has been actively writing Kerendia since April 2026 (pre-dating the alert). They correctly do not count as a "new writer" under our 12-month lookback. Their continued prescribing (1 script) produces the 0.17 average (1 ÷ 6). See Section 7 below for details on segment-label lag.

**What this means for Segment B:**
- The July invited-only cohort (3 HCPs) saw 1 new writer (33%) — a strong early signal, but an extremely small sample.
- August's attended cohort (6 HCPs) showed no new writers within 4 weeks. This is not surprising: Segment B are non-writers by definition, and the 4-week early read may be too short to capture the full decision-to-prescribe cycle for HCPs new to Kerendia.
- **The 12-week mature read is critical for Segment B.** Non-writers typically need more time — the first eligible patient encounter, formulary check, prior authorization, and initial prescription may span 6–10 weeks. A 4-week window likely understates conversion for this segment.
- Across both months, the base rate for Segment B not-invited is 0.3–0.4%, meaning the program needs to convert just 1 additional HCP out of ~6–12 to outperform the baseline — achievable but hard to measure with small n.

---

## 4. Territory Highlights (Segment A, Attended)

| Territory | Month | Pre NBRx | Post NBRx | Lift |
|-----------|-------|----------|-----------|------|
| Downey, CA | July | 3 | 13 | +10 |
| Albany, NY (Striker) | July | 1 | 4 | +3 |
| Roanoke, VA | July | 0 | 3 | +3 |

> Note: n=1 per territory — individual HCP variation. Useful for field team recognition, not territory-level strategy.

---

## 5. What's Coming Next

| Milestone | Expected | What It Unlocks |
|-----------|----------|-----------------|
| July 12-week mature read | Next v6 refresh (~1 week) | **Durable lift confirmation for July** — are the early signals sustained? |
| August 4-week: 100% all stages | ~2 weeks | Clean early read for all August cohorts |
| August 12-week mature read | Late Nov 2026 | Durable lift for larger August cohort |
| Segment B mature conversion | Late Nov 2026 | **Critical test** — do non-writers convert given more time? |

The automated weekly refresh pipeline is now in place — as new Rx data arrives in the v6 source, the analytics tables and metric views update automatically.

---

## 6. Strategic Implications

### What's Working
- **Segment A (writers) show strong lift after attending** — prescribing volume nearly triples in July, doubles in August
- **Invite-to-attend conversion (~25–30%)** is healthy — once invited, HCPs respond
- **Segment B requires patience** — the 4-week window is too short to judge non-writer conversion; the 12-week mature read will be the real test

### The Opportunity
- **Scaling the invite rate is the #1 lever.** Currently <1% of NBA-flagged HCPs are invited. Even increasing to 3–5% could double or triple the downstream NBRx impact.
- **Prioritize Segment A for speaker program slots** — immediate lift is largest here, and measurable within 4 weeks
- **Don't give up on Segment B yet** — the 12-week read may reveal conversions the 4-week window misses

### Recommendations
1. **Increase speaker program capacity** in territories with high NBA alert density
2. **Tighten the NBA-to-invite handoff** — ensure field teams act on NBA alerts within the first 30 days
3. **Track invite rates by territory** as a leading indicator of downstream Rx impact
4. **Revisit Segment B in late November** when 12-week mature data is available

---

## 7. Data Caveats & Known Limitations

### 7a. Segment Labels May Lag Actual Prescribing Behavior

The call plan segments ("A_High_Potential_Writer" and "B_High_Potential_Non_Writer") are assigned at a **point in time** during the call plan cycle. An HCP classified as Segment B when the list was built may have started prescribing Kerendia by the time the NBA alert fires months later. We found:

- **427 out of 5,476 Segment B NPIs** (7.8%) are flagged `KERENDIA_WRITER_IN_LAST_12_MONTHS = 1` in the alert data itself — the upstream data recognizes them as writers even though the segment label says "non-writer."
- **77 Segment B NPIs** have actual Kerendia NBRx (new prescriptions) in the 12 months before their alert in our IQVIA data.
- **107 additional Segment B NPIs** have Kerendia TRx (refills/renewals) but zero NBRx — they manage existing patients but haven't initiated new ones.

**Impact on reporting:** When you see non-zero post-NBRx for Segment B cohorts with 0 new writers (e.g., August ATTENDED: 0 new writers but 0.17 post-NBRx), it's because a subset of Segment B HCPs were already writing before the program. Our 12-month lookback correctly excludes them from the new-writer count. The segment label is stale, but the metric is accurate.

### 7b. Small Sample Sizes

Attended cohorts are small (5–10 HCPs per month). Results are directional, not statistically powered. Confidence will improve as:
- More months accumulate (Sep, Oct cohorts)
- 12-week mature reads become available
- Invite rates increase, growing the attended pool

---

## Appendix: Definitions & Methodology

| Term | Definition |
|------|-----------|
| **NBA Alert** | Monthly flag from the Next Best Action engine identifying HCPs with high potential for Kerendia prescribing. Issued on the 7th of each month. |
| **Funnel Stages** | ATTENDED = invited and attended a speaker program within 30 days of alert. INVITED_ONLY = invited but did not attend. NOT_INVITED = no invitation within 30 days. |
| **NBRx Lift** | Per-HCP change in Kerendia new prescriptions: average 4-week post-window NBRx minus average 4-week pre-window NBRx. Positive = more scripts after. |
| **New Writer** | HCP with zero Kerendia NBRx in the **12 months** before the alert who wrote at least one NBRx in the post-window. Uses NBRx (new scripts), not TRx (total scripts including refills). 12-month lookback ensures intermittent writers are not misclassified. |
| **Post-Anchor Date** | The start of the post-window. Adapts by cohort: first attended date (if attended) > first invite date (if invited) > alert date (if not invited). This ensures we measure impact from the actual point of engagement, not just the alert. |
| **4-Week Early Read** | 28-day pre/post windows. Available sooner; captures immediate response. May understate full effect. |
| **12-Week Mature Read** | 84-day pre/post windows. Captures sustained change over 2–3 patient visit cycles. Requires more data accumulation. |
| **Coverage Flag** | % of HCPs with complete Rx data for the full post-window. Metrics are only reliable when coverage ≥ 90%. |
| **Segment A** | Call plan segment "A_High_Potential_Writer" — HCPs with established Kerendia prescribing history. Report **lift** for this segment. |
| **Segment B** | Call plan segment "B_High_Potential_Non_Writer" — HCPs with clinical potential but no recent Kerendia prescribing. Report **new-writer conversion** for this segment. Note: ~7.8% may have started writing since the segment was assigned (see Section 7a). |

**Rx data source:** Kerendia NBRx from IQVIA LAAD-based LRx v6, excluding cash-pay, weekly grain.

*This report is generated from the [Kerendia Speaker Program Impact + NBA Genie space](https://dbc-7281de76-54c6.cloud.databricks.com/genie/rooms/01f1c9939e8a1648bbc09df186d37134). Data refreshes automatically when the upstream v6 table is updated.*
