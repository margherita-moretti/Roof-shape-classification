# 2. Variable Separability Analysis

Given a reference set of buildings already classified (e.g. flat vs. sloped, by visual inspection or a small hand-labelled sample), ranks every candidate variable produced by [stage 1](../1_roof_morphology) by how well it separates the two groups. The result of this analysis is used to decide which variable to carry forward into [stage 3](../3_ASA_index_classification).

---

## Method

Ranks candidate variables using the percentile-gap metric:

```
separability = max(|p75_A − p25_B|, |p75_B − p25_A|)
```

computed on **z-score normalized** values (mean/std of the pooled sample) so variables in different units  (degrees, bits, unitless coherence) are fairly comparable. Without normalization, a variable measured in degrees would trivially outrank one bounded in [-1, 1], regardless of which one actually separates the classes better.

Two outputs:
1. A ranking table (printed + saved as CSV).
2. A histogram grid (all candidate variables, saved as a single PNG).

The script also checks the classification-label field for values it doesn't recognise, so an unexpected label doesn't silently drop rows from the comparison.

---

## How to run

Open `variable_separability.py` and check `input_path` (the classified GeoPackage from stage 1) and `type_field` near the top match your file, then:

```bash
pip install -r ../requirements.txt
python variable_separability.py
# -> separability_output/separability_ranking.csv
# -> separability_output/histograms_grid.png
```

## Limitations

The separability ranking is a descriptive heuristic (percentile-gap on normalized values), not a formal statistical test, wich is used [stage 4](../4_ASA_index_validation).
