# PV Rooftop Suitability — Roof Morphology Pipeline

Four-stage pipeline to classify industrial rooftops (flat / pitched / curved) from LiDAR-derived DSM data, for photovoltaic site-suitability assessment.

> Companion code for: *Industrial rooftops characterization for photovoltaic power plants through remote sensing and climate projections* — Politecnico di Milano.
> Author: Margherita Moretti.

---

## Pipeline

| Stage | Folder | What it does |
|---|---|---|
| 1 | [`1_roof_morphology/`](./1_roof_morphology) | Per-building statistics from a DSM/slope/aspect raster stack: MAD-filtered elevation, entropy, the Aspect Spatial Autocorrelation (ASA) index, roughness. |
| 2 | [`2_variable_separability/`](./2_variable_separability) | Given a reference set of hand-classified buildings, ranks candidate variables from stage 1 by how well they separate flat from non-flat roofs — used to calibrate the threshold applied in stage 3. |
| 3 | [`3_ASA_index_classification/`](./3_ASA_index_classification) | Applies the calibrated ASA threshold to classify every building in the full dataset as flat or pitched. |
| 4 | [`4_ASA_index_validation/`](./4_ASA_index_validation) | Discriminant validity check (R): Mann-Whitney U test comparing ASA between the manually-labelled reference classes, reporting effect size and significance. |

Each folder has its own README with setup and usage instructions. Stages 2–4 take the GeoPackage produced by stage 1 as input.

---

## The core idea

Flat roofs and pitched roofs look different in one specific way: on a flat roof, small DSM noise makes the aspect (exposure direction) essentially **random** from pixel to pixel; on a pitched roof, aspect is **locally coherent** — neighbouring pixels point the same way.

The **ASA (Aspect Spatial Autocorrelation) index** — an original approach devised for this project, not adapted from an existing published index — captures exactly that contrast: values near 1 indicate a coherent pitched surface, values near 0 indicate a locally random (flat) one. A threshold of 0.6 separates the two classes. Full details in [`1_roof_morphology/README.md`](./1_roof_morphology/README.md).

---

## Requirements

Stages 1–3 (Python):

```bash
pip install -r requirements.txt
```

Stage 4 (R): `sf`, `ggplot2` — not covered by `requirements.txt`, see [`4_ASA_index_validation/README.md`](./4_ASA_index_validation/README.md).

---

## Author

**Margherita Moretti** — Environmental Engineer & Geospatial Data Analyst
[LinkedIn](https://www.linkedin.com/in/margheritamoretti) · moretti-margherita@virgilio.it
