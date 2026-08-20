# 4. ASA Index Validation

Discriminant validity check for the ASA index: does ASA actually differ between roof types, measured against the manually-assigned reference (`tipo`) — not the threshold-derived classification from [stage 3](../3_ASA_index_classification).

Part of the pipeline described in the [repository root README](../README.md).

The same `tipo` reference sample is used twice elsewhere in the pipeline: [stage 2](../2_variable_separability) uses it to pick ASA as the variable to classify on; the 0.6 threshold applied in stage 3 was chosen by hand by inspecting this same sample. This script is the check on that decision: how cleanly does ASA actually separate the two reference classes.

## What it does

`mann_whitney_evaluation.R` reads the GeoPackage produced by [stage 1](../1_roof_morphology) and runs a Mann-Whitney U test comparing `asp_asa_filtrata` between the two reference classes (field `tipo`: piano / sloped), reporting:

- U statistic, p-value
- Effect size (rank-biserial correlation r), which matters far more than the p-value here: with a reasonably sized sample, even a weak effect can produce a vanishingly small p-value, so p alone doesn't indicate how *well* ASA separates the classes — r does.
- A histogram of the two distributions, annotated with the test result, saved as a publication-ready figure.

## How to run

```r
install.packages(c("sf", "ggplot2"))  # once
```

Open `mann_whitney_evaluation.R`, check `input_gpkg`, `VARIABLE`, and `CLASS_FIELD` near the top match your file, then run the script:

```
Rscript mann_whitney_evaluation.R
```

```
# -> output/Mann_Whitney_Results.csv
# -> output/ASA_piano_vs_sloped.png
```

**Note (Windows):** use forward slashes in `input_gpkg` (`"C:/Users/..."`), not backslashes — R interprets `\` inside a quoted string as an escape sequence and will error on a literal Windows path.

## Interpreting the result

The rank-biserial r ranges from -1 to 1; conventional benchmarks are ~0.1 small, ~0.3 medium, ~0.5 large. It also has a direct concrete reading: `(1 − r) / 2` is the probability that a randomly picked pair from the two classes is ordered the "wrong" way round — i.e. `1 − (1−r)/2` is how often ASA correctly ranks a random piano/sloped pair, which is often easier to communicate than the r statistic alone.

## Limitation

`tipo` is the same sample the 0.6 threshold was chosen from — this test is therefore evaluated on the calibration sample itself, not on held-out data. The result reflects how cleanly the threshold fits the sample it was picked on; it is not yet an out-of-sample validation. A held-out subset (labelled but *not* looked at when choosing the threshold) would be needed to rule out optimistic bias from fitting and evaluating on the same data.
