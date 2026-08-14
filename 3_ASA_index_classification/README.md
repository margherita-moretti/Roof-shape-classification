# 3. ASA Index Classification

Applies a threshold on the ASA index to classify every building in the full dataset as flat or sloped — not just the manually-labelled reference sample.

Part of the pipeline described in the [repository root README](../README.md).

## Where the threshold comes from

The 0.6 cutoff is not fitted by any script in this repository, it comes from a calibration process on a larger sample not described in this repository.

- [stage 2](../2_variable_separability) uses it to rank candidate variables and confirm ASA separates the two classes better than the alternatives (which variable to use);
- [stage 4](../4_ASA_index_validation) uses it to quantify how well the 0.6 cutoff separates the two classes (effect size, significance) — see that folder for the important caveat that this evaluates the threshold on the same sample it was chosen from, not on held-out data.

This script is the step in between: it takes the variable (ASA) and the cutoff (0.6) as given, and applies that decision rule to every building, including the ones with no manual label.

## What it does

Reads the GeoPackage produced by [stage 1](../1_roof_morphology) (which already has `asp_asa` / `asp_asa_filtrata` computed per building) and adds a `classe` field:

- `ASA < 0.6` → **piano** (flat roof)
- `ASA ≥ 0.6` → **sloped** (pitched roof plane)
- ASA missing (too few valid pixels for that building) → left unclassified (`None`), never silently defaulted to either class

`classe` (this script's output, for every building) is deliberately a separate field from `tipo` (the manual reference labels, for a subset) — keeping them distinct is what makes stage 4's validation meaningful: it can compare the two rather than a field against itself.

## How to run

Open `asa_classification.py` and check `input_gpkg` points at stage 1's output, then:

```bash
pip install -r ../requirements.txt
python asa_classification.py
# -> output/edifici_classificati.gpkg
# + a console summary: counts per class and how many buildings were left unclassified
```

`ASA_FIELD` (default `asp_asa_filtrata`) and `ASA_THRESHOLD` (default `0.6`) are set near the top of the script.

## Next step

Curved vs. pitched sub-classification within the `sloped` group is a further refinement, not yet part of this script.

