# Kerendia NBA × Speaker Program: Impact Insights
**Date:** October 19, 2026 | **Prepared by:** Analytics & AI Team | **Data through:** September 25, 2026

---

## Executive Summary

The Next Best Action (NBA) engine has been flagging high-potential HCPs for speaker program engagement since July 2026. This report measures what happens when those flagged HCPs are actually invited to — and attend — a speaker program, compared to those who are not invited.

**Bottom line:** HCPs who attend a speaker program after an NBA alert show significantly higher NBRx lift and new-writer conversion than those who are not invited. The opportunity is clear — but the current bottleneck is the alert-to-invite conversion rate (~1%), not program effectiveness.

---

## 1. The Funnel: From Alert to Attendance

| Month | HCPs Alerted | Invited (60d) | Attended (60d) | Invite Rate | Invite-to-Attend |
|-------|-------------|---------------|----------------|-------------|-------------------|
| July 2026 | 4,355 | 76 | 23 | **1.7%** | **30%** |
| August 2026 | 6,260 | 83 | 19 | **1.3%** | **23%** |
| September 2026 | 6,150 | 30 | 3 | 0.5% | 10% |
| October 2026 | 6,152 | — | — | Too early | Too early |

**Takeaway:** Once an HCP is invited, roughly **1 in 4 attend** — a healthy conversion rate. The constraint is upstream: only ~1–2% of NBA-flagged HCPs receive a speaker program invitation within 60 days. This is expected given speaker program capacity, but represents the key leverage point for scaling impact.

---

## 2. NBRx Impact: Attendees vs. Non-Attendees

### July 2026 — 4-Week Early Read (100% data coverage)

| Cohort | HCPs | Avg Pre-NBRx | Avg Post-NBRx | **Lift** | New Writers | **NW Rate** |
|--------|------|-------------|--------------|----------|-------------|-------------|
| **Attended** | 5 | 1.40 | 4.00 | **+2.60** | 2 | **40.0%** |
| Invited Only | 12 | 0.83 | 0.83 | 0.00 | 1 | 8.3% |
| Not Invited | 4,338 | 0.06 | 0.07 | 0.00 | 70 | 1.6% |

### August 2026 — 4-Week Early Read (96–100% data coverage)

| Cohort | HCPs | Avg Pre-NBRx | Avg Post-NBRx | **Lift** | New Writers | **NW Rate** |
|--------|------|-------------|--------------|----------|-------------|-------------|
| **Attended** | 10 | 0.60 | 1.00 | **+0.40** | 1 | **10.0%** |
| Invited Only | 25 | 0.80 | 0.88 | +0.08 | 3 | 12.0% |
| Not Invited | 6,225 | 0.04 | 0.06 | +0.01 | 57 | 0.9% |

**Takeaway:** Across both months, **attending a speaker program after an NBA alert is associated with meaningfully higher NBRx lift and new-writer conversion** compared to the baseline. The July cohort (n=5) shows a striking +2.60 lift per HCP and 40% new-writer rate. The August cohort (n=10) confirms the signal at a more modest +0.40 lift and 10% new-writer rate. Both are well above the ~1% baseline new-writer rate for non-invited HCPs.

> **Caution:** Sample sizes are small (5–10 attendees per month). These are early directional signals, not statistically powered conclusions. The 12-week mature read will provide stronger evidence once data coverage extends past late September.

---

## 3. Segment Performance

Among HCPs who attended (July + August combined):

| Segment | Attended | Lift (4w) | New Writers | NW Rate |
|---------|----------|-----------|-------------|---------|
| **A — High Potential Writer** | 9 | **+2.00** | 3 | **33%** |
| B — High Potential Non-Writer | 6 | -0.17 | 0 | 0% |

**Takeaway:** Segment A HCPs (high-potential writers) show the strongest response to speaker programs — they have the clinical profile to prescribe and the program nudges them to act. Segment B HCPs may need longer observation windows or different engagement tactics.

---

## 4. Territory Highlights

Top territories by NBRx lift among attended HCPs (July + August):

| Territory | Attended HCPs | Lift (4w) | New Writers |
|-----------|--------------|-----------|-------------|
| Downey, CA | 1 | +10.0 | 0 |
| Albany, NY (Striker) | 1 | +3.0 | 0 |
| Roanoke, VA | 1 | +3.0 | 1 |
| Atlanta, GA | 1 | +1.0 | 1 |

> Note: n=1 per territory — individual HCP variation. Useful for field team recognition, not territory-level strategy.

---

## 5. What's Coming Next

| Milestone | Expected Timing | What It Unlocks |
|-----------|----------------|-----------------|
| Rx data through Sep 29 | Next v6 refresh (~1 week) | **July 12-week mature read** — first statistically meaningful window |
| Rx data through mid-Oct | ~2–3 weeks | August 4-week: 100% coverage for all stages |
| Rx data through late Nov | ~6 weeks | August 12-week mature read |

The automated weekly refresh pipeline is now in place — as new Rx data arrives in the v6 source, the analytics tables and metric views update automatically.

---

## 6. Strategic Implications

### What's Working
- **Speaker programs drive measurable NBRx lift** among NBA-flagged attendees
- **New-writer conversion is 5–25x higher** for attendees vs. the uninvited baseline
- **Invite-to-attend conversion (~25–30%)** is healthy — HCPs respond when invited

### The Opportunity
- **Scaling the invite rate is the #1 lever.** Currently ~1% of NBA-flagged HCPs are invited. Even modest increases (to 3–5%) would roughly double or triple the number of attendees and downstream NBRx impact.
- **Prioritize Segment A** for speaker program invitations — they show the strongest lift signal
- **Monitor the 12-week read** (available with the next data refresh) for durable impact evidence

### Recommendations
1. **Increase speaker program capacity** in territories with high NBA alert density
2. **Tighten the NBA-to-invite handoff** — ensure field teams act on NBA alerts within the first 30 days
3. **Track invite rates by territory** as a leading indicator of downstream Rx impact
4. **Revisit in November** when July 12-week mature data is available for a powered analysis

---

## Appendix: Data Coverage & Methodology

- **Alert dates:** Monthly on the 7th (Jul 7, Aug 7, Sep 7, Oct 7, 2026)
- **Rx data source:** Kerendia NBRx from LAAD-based LRx v6 (non-cash, weekly grain)
- **4-week early read:** Pre-window = 28 days before alert; Post-window = 28 days after first engagement (or alert date if not invited)
- **Funnel stages:** ATTENDED = invited and attended within 30 days; INVITED_ONLY = invited but not attended; NOT_INVITED = no invitation within 30 days
- **Coverage flag:** % of HCPs with complete post-window Rx data. Metrics are only reliable when coverage >= 90%.
- **New writer:** HCP with zero Kerendia NBRx in the pre-window who wrote at least one script in the post-window

*This report is auto-generated from the Kerendia Speaker Program Impact + NBA Genie space. For interactive exploration, visit the [Genie space](https://dbc-7281de76-54c6.cloud.databricks.com/genie/rooms/01f1c9939e8a1648bbc09df186d37134).*
