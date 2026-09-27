# Longer-trial change from baseline

Latest telemetry: 2026-09-27T22:55:12+00:00.

Deltas are **percentage points of relative humidity**, not relative percent changes. Baselines are the median cached reading before each reported opening. For an exactly timestamped milestone, use the first poll at or after the target and show its offset. Operator minute-level timestamps and sensor latency limit physical timing precision.

## Since opening

| Unit | Baseline | +10 min | +15 min | +20 min |
| --- | --- | --- | --- | --- |
| ID 1 · dark blue/purple PLA | 20% | 24% (Δ +4 pp; poll +12s) | 23% (Δ +3 pp; poll +12s) | 22% (Δ +2 pp; poll +12s) |
| ID 3 · black PLA | 19% | 26% (Δ +7 pp; poll +12s) | 24% (Δ +5 pp; poll +12s) | 23% (Δ +4 pp; poll +12s) |
| ID 2 · simulated swap | 22% | 25% (Δ +3 pp; poll +12s) | 24% (Δ +2 pp; poll +12s) | 24% (Δ +2 pp; poll +12s) |

## Since closing

| Unit | Baseline | +10 min | +15 min | +20 min |
| --- | --- | --- | --- | --- |
| ID 1 · dark blue/purple PLA | 20% | 23% (Δ +3 pp; poll +12s) | 22% (Δ +2 pp; poll +12s) | 22% (Δ +2 pp; poll +12s) |
| ID 3 · black PLA | 19% | 24% (Δ +5 pp; poll +16s) | 23% (Δ +4 pp; poll +16s) | 22% (Δ +3 pp; poll +16s) |
| ID 2 · simulated swap | 22% | 25–25% (Δ +3 to +3 pp; close-time window) | 24–24% (Δ +2 to +2 pp; close-time window) | 24–24% (Δ +2 to +2 pp; close-time window) |

ID 2 closed sometime after its 4:29 PM opening and shortly before 4:31 PM. Its post-close milestone cells span that two-minute timing uncertainty and use surrounding cached observations, rather than inventing a closing timestamp. These ranges do not exclude unobserved changes between polls.

Baseline-to-milestone deltas describe recovery magnitude. The scheduler's decision uses time continuously above the effective 20% threshold, which is a different clock; both are reported separately. Different desiccant histories and modified capacities confound direct comparisons among units.
