# 3. ASA Index Classification

🚧 **In progress.** This stage applies the ASA threshold calibrated in [stage 2](../2_variable_separability) to classify every building in the full dataset — not just the hand-labelled reference sample.

Part of the pipeline described in the [repository root README](../README.md).

## Planned approach

- **Input:** the GeoPackage produced by [stage 1](../1_roof_morphology) (`asp_asa` / `asp_asa_filtrata` computed for all buildings).
- **Rule:** `ASA < 0.6` → flat roof; `ASA ≥ 0.6` → pitched roof plane (threshold calibrated in stage 2).
- **Output:** the same GeoPackage with a classification field added (flat / pitched, plus any further sub-classes, e.g. curved roofs, still to be defined).

## Why it's a separate stage

Stages 1 and 2 answer "what do we measure?" and "which measurement separates the classes best?". This stage is the one that actually turns that into a decision rule applied to the whole dataset — kept separate so the classification logic (and its threshold) can be re-calibrated later without re-running the statistics computation.
