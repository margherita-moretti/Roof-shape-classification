# 3. ASA Index Classification

Applies a threshold on the ASA index to classify every building in the full dataset as flat or sloped, not just the manually-labelled reference sample.

Part of the pipeline described in the [repository root README](../README.md).

## What it does

Reads the GeoPackage produced by [stage 1](../1_roof_morphology) (which already has `asp_asa` / `asp_asa_filtrata` computed per building) and adds a `classe` field:

- `ASA < 0.6` → **flat** (flat roof)
- `ASA ≥ 0.6` → **sloped** (pitched roof plane)

`classe` (this script's output, for every building) is deliberately a separate field from `tipo` (the manual reference labels, for a subset).

## Notes

The 0.6 cutoff is not fitted by any script in this repository, it comes from a calibration process on a larger sample not described in this repository.

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

