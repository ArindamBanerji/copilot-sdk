# RL-CTRL reconciliation

## Diff table

| Element | Option B | Option C | Match |
|---|---|---|---|
| state_features | (bias, margin, 1-correct); normalized only by raw values | (correct, flipped); no normalization | False |
| action_space | binary scale {0.5,1.0} on lr_pos/lr_neg | alpha {0.25,0.5,0.75,1.0} | False |
| reward_function | least-squares prediction of correct; scale 0.5 when predicted <0.75 | incremental reward=(correct?-1:1) minus 0.5 under pressure, per (correct,flipped) action state | False |
| fqi_hyperparams | No ExtraTrees/FQI; np.linalg.lstsq | No ExtraTrees/FQI; tabular incremental action means | False |
| training_data | per-update rows of correct and margin; fit once from supplied training rows | online state/action reward counts during evaluation trajectory | False |
| action_application | controller.get_lr() before super().update_weights(); lr_pos/lr_neg = default*scale | monkey-patched update_weights; controller.begin(trace,correct) before original call; alpha applied to both rates | False |

## Resolution

All six A2 definition rows differ. The canonical identity-policy comparison was run through both live injection paths; see JSON for checkpoint curves. The prior 0.727 and 0.797 A2 results are not adjudicated because the definitions were not the same.

Verdict: trajectory-control evidence remains unresolved; neither prior A2 result is valid as a cross-implementation comparison.
