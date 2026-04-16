# Error tradeoff interpretation (Stage 3)

Positive class = Ready (`label_ready=1`).

## Type I vs Type II linkage
- **Type I (false Ready)**: false positives.
- **Type II (missed Ready)**: false negatives.

## Features whose *removal* increased false Ready (delta_fp > 0)
These signals likely helped the model **avoid** clearing borderline Not Ready weeks.

```
     dropped_feature  delta_fp  delta_fn  delta_tp  delta_tn       f1  roc_auc
  billed_utilization        31         0         0       -31 0.960854 0.995837
 non_billable_noshow        27         0         0       -27 0.965435 0.992874
revenue_per_kent_leg        24         0         0       -24 0.968900 0.996112
   high_acuity_share        23         0         0       -23 0.970060 0.994915
   total_volume_pool        22         0         0       -22 0.971223 0.998006
```


## Features whose *removal* increased missed Ready (delta_fn > 0)
These signals likely helped detect true Ready weeks.

```
     dropped_feature  delta_fp  delta_fn  delta_tp  delta_tn       f1  roc_auc
  billed_utilization        31         0         0       -31 0.960854 0.995837
 non_billable_noshow        27         0         0       -27 0.965435 0.992874
revenue_per_kent_leg        24         0         0       -24 0.968900 0.996112
   high_acuity_share        23         0         0       -23 0.970060 0.994915
   total_volume_pool        22         0         0       -22 0.971223 0.998006
```


## Caveat
This is ablation impact on a single snapshot and threshold; it is not a causal claim about operations.
