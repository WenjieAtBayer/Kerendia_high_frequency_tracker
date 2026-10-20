# Kerendia NBA × Speaker Program: Impact Insights
**Date:** October 19, 2026 (updated October 20, 2026) | **Prepared by:** Decision Intelligence Team | **Data through:** September 25, 2026

---

## Executive Summary

Since July 2026, the Next Best Action (NBA) engine has published a monthly **NBA dropdown list** in Veeva, recommending high-potential HCPs for speaker program invitations. This report measures what happens when HCPs on the list are actually invited to — and attend — a speaker program, compared to those who are not invited.

**Bottom line:** HCPs on the NBA dropdown list who go on to attend a speaker program show significantly higher prescribing activity than those who are not invited. The opportunity is clear — but the current bottleneck is the list-to-invite conversion rate (<1% for NBA HCPs), not program effectiveness.

**NBA vs Not NBA:** Compared with Segment A/B HCPs not on the NBA dropdown list, NBA HCPs have roughly 2x the baseline prescribing, are somewhat more likely to be invited (0.8–1.0% vs 0.6–0.7%), and — for Segment A writers — show much larger lift after attending (+2.60 vs +0.17 in July). Being on the list alone does not change prescribing; the value comes from directing engagement to the right HCPs (Section 3c).

**Field adoption:** Only **about 4% of territories** acted on their NBA dropdown list by inviting at least one listed HCP to a program they own within 60 days (26 of 693 in July, 29 of 666 in August). Across July–September, 41 of 714 territories (5.7%) acted at least once. Credit goes to the territory of the rep who owns the speaker program event, from Veeva (Section 2b).

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

## 2. The Funnel: From NBA List to Attendance

> **Correction (Oct 20, 2026):** The funnel counts below have been corrected after deduplicating `mv_speaker_nba` to 1 row per NPI x cycle. The prior version had inflated numbers (e.g., July showed 76 invited / 23 attended) due to duplicate NBA list rows per HCP. The corrected NBA numbers and a new Not NBA comparison group are shown below.

| Month | Group | HCPs | Invited (60d) | Attended (60d) | Invite Rate | Invite-to-Attend |
|-------|-------|------|---------------|----------------|-------------|-------------------|
| July 2026 | **NBA** | 4,355 | 43 | 12 | **0.99%** | **28%** |
| July 2026 | Not NBA | 26,625 | 178 | 51 | 0.67% | 29% |
| August 2026 | **NBA** | 6,260 | 51 | 11 | **0.81%** | **22%** |
| August 2026 | Not NBA | 24,945 | 141 | 44 | 0.57% | 31% |
| September 2026 | **NBA** | 6,150 | 18 | 2 | 0.29% | 11% |
| September 2026 | Not NBA | 24,215 | 52 | 15 | 0.21% | 29% |
| October 2026 | Both | 30,401 | 0 | 0 | Too early | Too early |

**Takeaway:** Once an HCP is invited, roughly **1 in 4 attend** — a healthy conversion rate. The constraint is upstream: less than 1% of HCPs on the NBA dropdown list receive a speaker program invitation within 60 days. Not NBA Segment A/B HCPs show a slightly lower invite rate (~0.2–0.7%) but a comparable invite-to-attend conversion (~29–31%). This confirms the bottleneck is program capacity, not NBA targeting specifically.

### 2b. Field Adoption: How Many Territories Act on the NBA Dropdown List?

To see whether reps act on NBA suggestions, we count territories (a proxy for reps) that **invited at least one HCP from their own NBA dropdown list to a speaker program event they own** within 60 days of the cycle date.

**How invitations are credited (updated Oct 20, 2026):** Most NBA HCPs are shared. **About 80% of HCPs on the NBA dropdown list are aligned to 2–4 territories**, and each aligned territory sees the HCP on its own list. Veeva records the **event owner** (the rep who requested the speaker program) and that rep's territory for every event. This is stored in the new `dim_event_owner` table and joins to 252 of the 253 events since July. A territory gets credit only when it owns the event that the HCP was invited to. So when two territories share an HCP, only the one that sent the invite counts as acting. This replaces the earlier lower/upper-bound range.

| Month | Territories with NBA HCPs | Avg NBA HCPs per Territory | Territories Acting (30d) | Territories Acting (60d) | **Territory Action Rate (60d)** | Territories with an Attendee (60d) |
|-------|---------------------------|----------------------------|--------------------------|--------------------------|---------------------------------|------------------------------------|
| July 2026 | 693 | 11.4 | 10 | 26 | **3.8%** | 8 |
| August 2026 | 666 | 15.8 | 19 | 29 | **4.4%** | 7 |
| September 2026 | 656 | 15.9 | 11 | 11 | 1.7%* | 2 |
| October 2026 | 657 | 15.9 | 0 | 0 | Too early | 0 |

*\* September's 60-day window is not yet complete; treat as provisional. "Avg NBA HCPs per Territory" counts a shared HCP once on each territory's list.*

**Cumulative (July–September):** 714 territories had at least one HCP on their NBA dropdown list. **41 (5.7%)** acted in at least one month, 24 acted in two or more months, and 1 acted in all three. The repeat count is approximate: one invitation can fall inside the 60-day windows of two consecutive cycles.

**Who sends the invites?** Of the NBA HCPs invited within 60 days, **67–78% were invited by a territory that has them on its list** (July 30 of 43, August 34 of 51, September 14 of 18). The rest were invited to events owned by a territory without that HCP on its NBA dropdown list, for example a neighboring territory or a different sales team running the program.

**For context, Not NBA:** 11% of territories (80 of 701) invited at least one of their Not NBA Segment A/B HCPs in July and 9% (67 of 709) in August. Each territory has ~64–68 Not NBA HCPs vs ~11–16 NBA HCPs on its list, so the chance of inviting at least one is naturally higher.

**Takeaway:** NBA adoption is concentrated in a small group of territories. **About 96% of territories did not invite a single HCP from their NBA dropdown list in a given month.** Broadening adoption across territories, not just adding invites in the few territories already acting, is the biggest lever for scaling the program.

> **Caveats:** (1) Territory is a proxy for the rep; one territory can have more than one rep. (2) Credit goes to the event owner. Co-hosts (1–3 team members per event) can also add attendees, but Veeva does not record which team member added each HCP. (3) We can't confirm that an invite was triggered by the NBA dropdown list rather than sent independently.

---

## 3. Prescribing Impact by Segment

> **Note:** The tables below cover **NBA HCPs only** (those with `nba_group = 'NBA'`). The NBA vs Not NBA comparison is in Section 3c.

We report different metrics for each segment because they measure different things:

- **Segment A (High Potential Writer):** These HCPs already prescribe Kerendia. The question is whether attending a speaker program increases their *prescribing volume*. We measure **NBRx lift** — the change in new prescriptions per HCP.
- **Segment B (High Potential Non-Writer):** These HCPs have never written Kerendia (or not in the past 12 months). The question is whether attending a speaker program causes them to *start prescribing*. We measure **new-writer conversion** — the share of HCPs who write their first script.

### How Lift Is Calculated

> **NBRx Lift** = average post-window NBRx per HCP − average pre-window NBRx per HCP
>
> - **Pre-window:** total Kerendia new prescriptions (NBRx) in the 4 weeks (28 days) *before* the NBA cycle date
> - **Post-window:** total Kerendia new prescriptions (NBRx) in the 4 weeks (28 days) *after* the engagement anchor date (first attended date if attended; first invite date if invited only; NBA cycle date if not invited)
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
- Invited-only and not-invited Segment A HCPs showed flat or near-zero lift, confirming the program attendance — not just being on the NBA dropdown list — is driving the change.

### 3b. Segment B — New-Writer Conversion (non-writers)

New writer = HCP with **zero Kerendia NBRx in the 12 months before the NBA cycle date** who wrote at least one script in the 4-week post-window.

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

> **† Note on August ATTENDED (0 new writers, 0.17 post-NBRx):** One of the 6 attended HCPs is classified as Segment B "non-writer" in the call plan but has been actively writing Kerendia since April 2026 (before the NBA cycle date). They correctly do not count as a "new writer" under our 12-month lookback. Their continued prescribing (1 script) produces the 0.17 average (1 ÷ 6). See Section 7 below for details on segment-label lag.

**What this means for Segment B:**
- The July invited-only cohort (3 HCPs) saw 1 new writer (33%) — a strong early signal, but an extremely small sample.
- August's attended cohort (6 HCPs) showed no new writers within 4 weeks. This is not surprising: Segment B are non-writers by definition, and the 4-week early read may be too short to capture the full decision-to-prescribe cycle for HCPs new to Kerendia.
- **The 12-week mature read is critical for Segment B.** Non-writers typically need more time — the first eligible patient encounter, formulary check, prior authorization, and initial prescription may span 6–10 weeks. A 4-week window likely understates conversion for this segment.
- Across both months, the base rate for Segment B not-invited is 0.3–0.4%, meaning the program needs to convert just 1 additional HCP out of ~6–12 to outperform the baseline — achievable but hard to measure with small n.

### 3c. NBA vs Not NBA — Isolating NBA's Contribution

To see what NBA adds, we compare HCPs on the NBA dropdown list against **Not NBA** HCPs — Segment A/B HCPs in the same monthly cycle who were *not* on the list. Both groups use the same cycle date as the anchor, the same funnel definitions, and the same 4-week windows. Source: `mv_speaker_nba_rx`, split by `nba_group`.

> **Note:** New-writer counts and rates in this section are pending reconfirmation (see the open item in the design doc). Lift and HCP counts are confirmed.

#### Segment A (writers) — 4-week NBRx lift

| Month | Cohort | NBA HCPs | NBA Pre → Post | **NBA Lift** | Not NBA HCPs | Not NBA Pre → Post | **Not NBA Lift** |
|-------|--------|----------|----------------|--------------|--------------|--------------------|------------------|
| July | Attended | 5 | 1.40 → 4.00 | **+2.60** | 6 | 0.33 → 0.50 | +0.17 |
| July | Invited Only | 9 | 1.11 → 0.89 | −0.22 | 26 | 0.38 → 0.65 | +0.27 |
| July | Not Invited | 3,006 | 0.081 → 0.084 | +0.004 | 7,105 | 0.045 → 0.046 | +0.000 |
| August | Attended | 4 | 1.00 → 2.25 | **+1.25** | 10 | 0.70 → 0.30 | −0.40‡ |
| August | Invited Only | 13 | 1.23 → 1.23 | 0.00 | 24 | 0.67 → 1.17 | +0.50‡ |
| August | Not Invited | 2,376 | 0.097 → 0.127 | +0.03 | 7,806 | 0.044 → 0.056 | +0.01 |

#### Segment B (non-writers) — 4-week new-writer conversion

| Month | Cohort | NBA HCPs | NBA New Writers | **NBA NW Rate** | Not NBA HCPs | Not NBA New Writers | **Not NBA NW Rate** |
|-------|--------|----------|-----------------|-----------------|--------------|---------------------|---------------------|
| July | Attended | 0 | — | — | 13 | 4 | 30.8% |
| July | Invited Only | 3 | 1 | 33.3% | 36 | 3 | 8.3% |
| July | Not Invited | 1,332 | 4 | **0.30%** | 19,439 | 20 | 0.10% |
| August | Attended | 6 | 0 | 0% | 19 | 2 | 10.5%‡ |
| August | Invited Only | 12 | 1 | 8.3% | 36 | 0 | 0%‡ |
| August | Not Invited | 3,849 | 14 | **0.36%** | 17,050 | 27 | 0.16% |

*‡ Not NBA August invited/attended cohorts have 79–92% 4-week data coverage; treat as provisional.*

#### Overall (all funnel stages, both segments)

| Month | NBA HCPs | NBA 4w Lift | Not NBA HCPs | Not NBA 4w Lift | 60d Invite Rate (NBA vs Not NBA) |
|-------|----------|-------------|--------------|-----------------|----------------------------------|
| July | 4,355 | **+0.008** | 26,625 | +0.001 | **0.99%** vs 0.67% |
| August | 6,260 | **+0.013** | 24,945 | +0.005 | **0.81%** vs 0.57% |

**What this tells us about NBA's impact:**
- **NBA picks higher-value HCPs.** Among HCPs who were *not* invited, NBA HCPs already write ~2x more Kerendia NBRx (Segment A: 0.081–0.097 vs 0.044–0.045 per HCP) and Segment B NBA HCPs convert to new writers at 2–3x the organic rate (0.30–0.36% vs 0.10–0.16%). NBA targeting is concentrating on HCPs with more prescribing potential.
- **NBA HCPs are somewhat more likely to be invited** (0.8–1.0% vs 0.6–0.7%), but the gap is modest — field teams are not yet strongly prioritizing the NBA dropdown list when filling speaker program slots.
- **Segment A NBA attendees show far larger lift than Not NBA attendees** (+2.60 vs +0.17 in July; +1.25 vs −0.40 in August). NBA writers appear to respond more strongly to the program — the combination of NBA targeting plus attendance is where the lift concentrates.
- **Being on the list alone does not move prescribing.** NBA HCPs who were not invited show near-zero lift (+0.004 to +0.03), similar to Not NBA. The value of NBA comes from *directing* engagement, not from the list itself.
- **Segment B tells a different story so far:** Not NBA attendees show early new-writer conversion (31% July, 11% August) while NBA Segment B attendees show none yet (0 of 6 in August, none attended in July). Sample sizes are very small and new-writer figures are pending reconfirmation, so this is not yet evidence against NBA for non-writers — the 12-week read is needed.

**Caveats:** This is an observational comparison, not a randomized test. NBA and Not NBA HCPs differ at baseline (NBA HCPs prescribe more before the cycle date), so differences in lift partly reflect who NBA selects, not only the program effect. Attended cohorts are 4–19 HCPs per cell; results are directional.

---

## 4. Territory Highlights (Segment A, Attended)

Credited to the **inviting territory** (owner of the speaker program event in Veeva).

| Inviting Territory | Cycle | Pre NBRx | Post NBRx | Lift | Inviter on HCP's NBA list? |
|--------------------|-------|----------|-----------|------|----------------------------|
| 124B – Downey, CA ISS | July | 6 | 16 | +10 | Yes (shared with 536B Downey Striker) |
| 009B – Albany, NY ISS | August | 3 | 6 | +3 | Yes (shared with 560B Albany Striker) |
| 069B – Raleigh, NC ISS | August | 0 | 3 | +3 | No (HCP is on 173B Roanoke, VA's list) |
| 226B – Richmond S, VA ISS | July | 0 | 2 | +2 | Yes |

> Note: n=1 per territory — individual HCP variation. Useful for field team recognition, not territory-level strategy. *Corrected Oct 20, 2026: the earlier version showed each HCP's territory picked arbitrarily from their aligned territories and listed Albany and Roanoke under July.*

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
- **NBA targets higher-value HCPs** — NBA HCPs have ~2x the baseline NBRx of Not NBA Segment A/B HCPs, and NBA Segment A attendees show far larger lift than Not NBA attendees
- **Segment B requires patience** — the 4-week window is too short to judge non-writer conversion; the 12-week mature read will be the real test

### The Opportunity
- **Scaling the invite rate is the #1 lever.** Currently <1% of HCPs on the NBA dropdown list are invited. Even increasing to 3–5% could double or triple the downstream NBRx impact.
- **Prioritize Segment A for speaker program slots** — immediate lift is largest here, and measurable within 4 weeks
- **Don't give up on Segment B yet** — the 12-week read may reveal conversions the 4-week window misses

### Recommendations
1. **Increase speaker program capacity** in territories with many HCPs on the NBA dropdown list
2. **Tighten the NBA-to-invite handoff** — ensure field teams act on the NBA dropdown list within the first 30 days
3. **Track territory adoption as a leading indicator** — monitor the share of territories that invite at least one HCP from their own NBA dropdown list each month (currently ~4%), alongside HCP-level invite rates. Now available in `mv_speaker_nba_territory`
4. **Prioritize NBA HCPs when filling slots** — the NBA vs Not NBA invite-rate gap is modest today (0.8–1.0% vs 0.6–0.7%), yet NBA Segment A attendees deliver the strongest lift
5. **Revisit Segment B in late November** when 12-week mature data is available, including the NBA vs Not NBA new-writer comparison

---

## 7. Data Caveats & Known Limitations

### 7a. Segment Labels May Lag Actual Prescribing Behavior

The call plan segments ("A_High_Potential_Writer" and "B_High_Potential_Non_Writer") are assigned at a **point in time** during the call plan cycle. An HCP classified as Segment B when the list was built may have started prescribing Kerendia by the time they appear on the NBA dropdown list months later. We found:

- **427 out of 5,476 Segment B NPIs** (7.8%) are flagged `KERENDIA_WRITER_IN_LAST_12_MONTHS = 1` in the NBA dropdown list data itself — the upstream data recognizes them as writers even though the segment label says "non-writer."
- **77 Segment B NPIs** have actual Kerendia NBRx (new prescriptions) in the 12 months before their NBA cycle date in our IQVIA data.
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
| **NBA Dropdown List** | Monthly list of recommended HCPs from the Next Best Action engine, shown to reps as a dropdown in Veeva when planning speaker programs. Published on the 7th of each month (the NBA cycle date). HCPs on the list are the "NBA" group (`ALERT_FLAG = 1` in the source). |
| **Territory Action Rate** | Share of territories with at least one HCP on their NBA dropdown list in the cycle that invited at least one of those HCPs, within 60 days, to a speaker program event the territory owns. Credit goes to the event owner's territory from Veeva, so a shared HCP credits only the territory that sent the invite. Territory is a proxy for the rep. |
| **Not NBA** | Segment A/B HCPs in the same monthly cycle who were not on the NBA dropdown list (ALERT_FLAG = 0). Used as the comparison group, anchored on the same cycle date. |
| **Funnel Stages** | ATTENDED = invited and attended a speaker program within 30 days of the NBA cycle date. INVITED_ONLY = invited but did not attend. NOT_INVITED = no invitation within 30 days. |
| **NBRx Lift** | Per-HCP change in Kerendia new prescriptions: average 4-week post-window NBRx minus average 4-week pre-window NBRx. Positive = more scripts after. |
| **New Writer** | HCP with zero Kerendia NBRx in the **12 months** before the NBA cycle date who wrote at least one NBRx in the post-window. Uses NBRx (new scripts), not TRx (total scripts including refills). 12-month lookback ensures intermittent writers are not misclassified. |
| **Post-Anchor Date** | The start of the post-window. Adapts by cohort: first attended date (if attended) > first invite date (if invited) > NBA cycle date (if not invited). This ensures we measure impact from the actual point of engagement, not just the list date. |
| **4-Week Early Read** | 28-day pre/post windows. Available sooner; captures immediate response. May understate full effect. |
| **12-Week Mature Read** | 84-day pre/post windows. Captures sustained change over 2–3 patient visit cycles. Requires more data accumulation. |
| **Coverage Flag** | % of HCPs with complete Rx data for the full post-window. Metrics are only reliable when coverage ≥ 90%. |
| **Segment A** | Call plan segment "A_High_Potential_Writer" — HCPs with established Kerendia prescribing history. Report **lift** for this segment. |
| **Segment B** | Call plan segment "B_High_Potential_Non_Writer" — HCPs with clinical potential but no recent Kerendia prescribing. Report **new-writer conversion** for this segment. Note: ~7.8% may have started writing since the segment was assigned (see Section 7a). |

**Rx data source:** Kerendia NBRx from IQVIA LAAD-based LRx v6, all pay types including cash-pay (previously excluded; added Oct 20 — impact is negligible at 0.2% of total NBRx across 110 NPIs), weekly grain.

*This report is generated from the [Kerendia Speaker Program Impact + NBA Genie space](https://dbc-7281de76-54c6.cloud.databricks.com/genie/rooms/01f1c9939e8a1648bbc09df186d37134). Data refreshes automatically when the upstream v6 table is updated.*
