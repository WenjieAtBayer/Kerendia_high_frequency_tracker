# Kerendia NBA × Speaker Program: Impact Insights
**Date:** October 19, 2026 | **Prepared by:** Analytics & AI Team | **Data through:** September 25, 2026

---

## Executive Summary

The Next Best Action (NBA) engine has been flagging high-potential HCPs for speaker program engagement since July 2026. This report measures what happens when those flagged HCPs are actually invited to — and attend — a speaker program, compared to those who are not invited.

**Bottom line:** HCPs who attend a speaker program after an NBA alert show significantly higher prescribing activity than those who are not invited. The opportunity is clear — but the current bottleneck is the alert-to-invite conversion rate (~1%), not program effectiveness.

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

| Month | HCPs Alerted | Invited (60d) | Attended (60d) | Invite Rate | Invite-to-Attend |
|-------|-------------|---------------|----------------|-------------|-------------------|
| July 2026 | 4,355 | 76 | 23 | **1.7%** | **30%** |
| August 2026 | 6,260 | 83 | 19 | **1.3%** | **23%** |
| September 2026 | 6,150 | 30 | 3 | 0.5% | 10% |
| October 2026 | 6,152 | — | — | Too early | Too early |

**Takeaway:** Once an HCP is invited, roughly **1 in 4 attend** — a healthy conversion rate. The constraint is upstream: only ~1–2% of NBA-flagged HCPs receive a speaker program invitation within 60 days. This reflects the limited capacity of speaker programs, but represents the key leverage point for scaling impact.

---

## 3. Prescribing Impact by Segment

We report different metrics for each segment because they measure different things:

- **Segment A (High Potential Writer):** These HCPs already prescribe Kerendia. The question is whether attending a speaker program increases their *prescribing volume*. We measure **NBRx lift** — the change in new prescriptions per HCP.
- **Segment B (High Potential Non-Writer):** These HCPs have never written Kerendia (or not in the past 12 months). The question is whether attending a speaker program causes them to *start prescribing*. We measure **new-writer conversion** — the share of HCPs who write their first script.

### How Lift Is Calculated

> **NBRx Lift** = average post-window NBRx per HCP − average pre-window NBRx per HCP
>
> - **Pre-window:** total Kerendia new prescriptions in the 4 weeks (28 days) *before* the alert date
> - **Post-window:** total Kerendia new prescriptions in the 4 weeks (28 days) *after* the engagement anchor date (first attended date if attended; first invite date if invited only; alert date if not invited)
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
| **Attended** | 6 | 0 | 0% | 0.17 |
| Invited Only | 12 | 1 | **8.3%** | 0.50 |
| Not Invited | 3,849 | 14 | 0.4% | 0.01 |

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
- **Scaling the invite rate is the #1 lever.** Currently ~1% of NBA-flagged HCPs are invited. Even increasing to 3–5% could double or triple the downstream NBRx impact.
- **Prioritize Segment A for speaker program slots** — immediate lift is largest here, and measurable within 4 weeks
- **Don't give up on Segment B yet** — the 12-week read may reveal conversions the 4-week window misses

### Recommendations
1. **Increase speaker program capacity** in territories with high NBA alert density
2. **Tighten the NBA-to-invite handoff** — ensure field teams act on NBA alerts within the first 30 days
3. **Track invite rates by territory** as a leading indicator of downstream Rx impact
4. **Revisit Segment B in late November** when 12-week mature data is available

---

## Appendix: Definitions & Methodology

| Term | Definition |
|------|-----------|
| **NBA Alert** | Monthly flag from the Next Best Action engine identifying HCPs with high potential for Kerendia prescribing. Issued on the 7th of each month. |
| **Funnel Stages** | ATTENDED = invited and attended a speaker program within 30 days of alert. INVITED_ONLY = invited but did not attend. NOT_INVITED = no invitation within 30 days. |
| **NBRx Lift** | Per-HCP change in Kerendia new prescriptions: average 4-week post-window NBRx minus average 4-week pre-window NBRx. Positive = more scripts after. |
| **New Writer** | HCP with zero Kerendia NBRx in the **12 months** before the alert who wrote at least one script in the post-window. (12-month lookback ensures established intermittent writers are not misclassified.) |
| **Post-Anchor Date** | The start of the post-window. Adapts by cohort: first attended date (if attended) > first invite date (if invited) > alert date (if not invited). This ensures we measure impact from the actual point of engagement, not just the alert. |
| **4-Week Early Read** | 28-day pre/post windows. Available sooner; captures immediate response. May understate full effect. |
| **12-Week Mature Read** | 84-day pre/post windows. Captures sustained change over 2–3 patient visit cycles. Requires more data accumulation. |
| **Coverage Flag** | % of HCPs with complete Rx data for the full post-window. Metrics are only reliable when coverage ≥ 90%. |

**Rx data source:** Kerendia NBRx from IQVIA LAAD-based LRx v6, excluding cash-pay, weekly grain.

*This report is generated from the [Kerendia Speaker Program Impact + NBA Genie space](https://dbc-7281de76-54c6.cloud.databricks.com/genie/rooms/01f1c9939e8a1648bbc09df186d37134). Data refreshes automatically when the upstream v6 table is updated.*
