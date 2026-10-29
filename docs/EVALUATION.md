# Evaluation and reproduction

## Planted delay under timestamp noise

Run from the repository root after `uv sync`:

```powershell
uv run python scripts/robustness_experiment.py
```

For each seed 0–9, the existing generator creates 500 cases. Its Interview Scheduled → Interview Completed waits are independently drawn from 240–480 hours; other waits use 4–72 hours. The experiment adds independent uniform jitter to every event timestamp, with amplitude 0, 24, 72 or 168 hours. The noise generator uses seed + 10000 and the same underlying draws across levels; each level starts from the original log. Times are converted to UTC before perturbation. No quality-probe rows are added. The generated CSV goes through the application's CSV parser and frame builder, then `insights` and `performance`.

The result is a hit if the app's highest **median** transition delay card selects the planted pair. The card considers all directly-following edges with at least 30 transition observations, including repeated observations from the same case. Ties use frequency and then the edge name. Jitter can reorder events, create new edges and remove planted adjacency; the experiment does not preserve the original trace order. Counts below are ranges across seeds, not confidence intervals.

Observed locally on 2026-10-29:

| Independent jitter per event | Hits | Eligible edges | Planted edge observations | Planted edge median, days |
| --- | ---: | ---: | ---: | ---: |
| 0 hours | 10/10 | 12–14 | 347–379 | 14.14–15.24 |
| ±24 hours | 10/10 | 13–16 | 281–316 | 14.27–14.86 |
| ±72 hours | 0/10 | 18–21 | 172–205 | 12.70–13.54 |
| ±168 hours | 0/10 | 18–23 | 118–140 | 7.80–10.06 |

At ±72 hours the winner was Screened → Interview Completed in six runs and Interview Scheduled → Offer in four. At ±168 hours winners varied; the script prints each miss. These new adjacencies can span the planted wait after events change order. The result tests one synthetic generator and one noise model, with a large built-in separation and ten seeds. It does not estimate performance on real hiring logs, compare algorithms, detect a causal bottleneck, or assess missing events, systematic clock bias, sampling uncertainty or other data errors. The planted transition's median after reordering describes the surviving observed adjacency, not the original injected durations.

## Real-log feasibility

[Van Dongen's BPI Challenge 2012 dataset](https://doi.org/10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f) is a real loan-application event log, not a hiring log. The [Eindhoven University record](https://research.tue.nl/en/datasets/bpi-challenge-2012/) identifies the creator and DOI. The [DataCite record](https://api.datacite.org/dois/10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f) lists “4TU General Terms of Use” and links its terms; it does not establish a Creative Commons license. The repository does not redistribute the log. The app imports CSV, not XES, so use would require an independently verified conversion and mapping; hiring-specific funnel, terminal and conformance rules would not automatically apply to a loan process. No BPI analysis or result is claimed here. Review the dataset's current terms before downloading or redistributing it.

## Other checks

The seed-42 demo has 800 eligible synthetic cases and intentionally excluded quality probes; see `tests/test_seed.py`. See [metric definitions](METRICS.md) for denominators and timing semantics. Tests and application setup are listed in the [README](../README.md).
