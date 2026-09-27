### Physical humidity recovery: 25% RH target

For this trace, recovery was defined as **reaching 25% RH or lower**. The longer-trial units started around 20% RH (individual baselines 19%, 20%, and 22%), making 25% approximately five percentage points above the representative starting humidity. Returning to the configured 20% drying trigger was not the success criterion. The 25% target was applied to the recorded readings; no configured trigger was changed. It is a common absolute target, not exactly baseline +5 points for every unit.

| Trial | Individual baseline | Time from opening to first observed reading ≤25% after excursion | Observed time above 25% (sampling-bounded) |
| --- | --- | --- | --- |
| AMS 2 Pro ID 0, black PLA-CF; one-minute opening | 17% | About 2m 52s | 1.0–1.7 min |
| AMS HT ID 128, black PC; one-minute opening | 10% | Never exceeded target (peak 21%) | None |
| AMS 2 Pro ID 1, dark blue/purple PLA; two-minute opening | 20% | About 6m 32s | 5.3–6.0 min |
| AMS 2 Pro ID 2, beige/gray PLA; simulated two-roll swap, no spools moved | 22% | About 8m 32s | 7.3–8.0 min |
| AMS 2 Pro ID 3, black PLA; roughly five-minute opening | 19% | About 11m 52s | 10.0–10.7 min |

All tested units were at or below 25% RH within 15 minutes of opening and remained there through the end of capture; the HT unit never exceeded 25%. Opening-relative times use approximate operator timestamps and first qualifying cached polls; they are not second-accurate physical recovery measurements. The scheduler's sustained-wait clock starts at the first above-trigger observation, not at lid opening; the last column is the corresponding observation-based comparison.

These observations support an adjustable **15-minute toggle-on starting value** with margin for the measured lid-opening transients. Backend default remains zero/off. This is not a guarantee across hardware, rooms, desiccant states, or repeated openings. If a configured trigger is near or below the closed-lid baseline, sustained humidity can appropriately initiate drying; that does not invalidate recovery to the 25% test target.

At 10/15/20 minutes after closing, deltas from individual baselines were +3/+2/+2 percentage points for ID 1, +5/+4/+3 for ID 3, and +3/+2/+2 for simulated ID 2 (close-time window used). Final RH was 22%, 22%, and 24%, respectively—all below the 25% recovery target.

The passive trace contains 129 cached API samples polled every 20 seconds, ending at 4:55:12 PM MDT on September 27, 2026. Ambient and queue drying were off; tested units had zero drying timers. This measured the deployed instance, not live execution of the final PR candidate. Tested 2 Pros have custom high-capacity desiccant; the HT has through-spool desiccant. Room RH was estimated around 60%; moisture loading and drying histories differed. These correlated observations on one H2D do not establish stock-AMS or P2S performance. The HT starting at 10% is a distinct low-baseline case. The configured 20% trigger context is retained only as supplementary operational context, not the primary recovery endpoint.

Recorder stopped; operator confirmed ambient drying restored and temporary API key revoked.
