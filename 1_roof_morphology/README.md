# 1. Roof Morphology Statistics

Computes per-building statistics from a DSM/slope/aspect raster stack — the first stage of the pipeline described in the [repository root README](../README.md).

For each building footprint, `roof_morphology.py`:
1. Applies a Median Absolute Deviation (MAD) outlier filter to the DSM.
2. Computes elevation / slope / aspect entropy (Shannon entropy on discretized values), raw and MAD-filtered.
3. Computes the **Aspect Spatial Autocorrelation (ASA)** index.
4. Computes KNN-based surface roughness.
5. Writes a GeoPackage of per-building statistics (numeric fields as float64).

---

## Method

### Flat-roof detection: the ASA index

Detecting flat roofs from local aspect coherence, rather than from slope alone, was an original approach devised for this project — not an adaptation of an existing published index. The idea: on a flat roof, small DSM noise makes the aspect (exposure direction) essentially **random** from pixel to pixel. On a pitched roof, aspect is **locally coherent** — neighbouring pixels point the same way. The ASA index below was designed to capture exactly that contrast.

For each pixel, ASA is the inverse-distance-weighted mean of `cos(Δaspect)` with its *k* nearest neighbours (dot product between unit aspect vectors), then averaged over the building:

```
ASA_i = Σ_j [ w_j · (u_i · U_j) ] / Σ_j w_j
```

- **ASA → 1**: locally coherent aspect → sloped roof plane
- **ASA → 0**: locally random aspect → flat / noisy roof

A threshold of **0.6** separates the two classes (calibrated in stage 2, applied in stage 3). This is a distance-weighted circular coherence measure, using unit-vector dot products avoids the 0°/360° wrap-around problem.

### MAD outlier filter

```
Zscore = 0.6745 · |z − median(z)| / MAD
MAD = median|z- median(z)|
Zscore > 3 → pixel set to NoData
```

Median and MAD are computed per building, from interior pixels only.

### Entropy

Shannon entropy of elevation / slope / aspect, computed on **discretized (binned)** values — a continuous raster fed directly into an entropy calculation just counts unique pixel values, which mostly measures building size rather than surface complexity. Bin widths are configurable (defaults: 0.25 m elevation, 2° slope, 10° aspect).

---

## Output fields

| Field | Description |
|---|---|
| `z_min`, `z_max`, `z_range`, `varianza` | Elevation stats, MAD-filtered |
| `entropia`, `entropia_filtrata` | Elevation entropy, raw / MAD-filtered |
| `pend_media`, `pend_media_filtrata` | Mean slope, raw / filtered |
| `pend_var`, `pend_var_filtrata` | Slope variance, raw / filtered |
| `pend_entropia`, `pend_entropia_filtrata` | Slope entropy, raw / filtered |
| `asp_entropia`, `asp_entropia_filtrata` | Aspect entropy, raw / filtered |
| `asp_asa`, `asp_asa_filtrata` | Aspect Spatial Autocorrelation index, raw / filtered |
| `roughness` | Mean local (KNN) std of elevation |
| `n_pixels` | Valid pixel count (QA field) |

---

## How to run

Open `roof_morphology.py` and edit the path variables near the top (`raster_path`, `slope_path`, `aspect_path`, `buildings_path`) to point at your files, then:

```bash
pip install -r ../requirements.txt
python roof_morphology.py
# -> output/edifici_statistiche.gpkg
```

### Data

dsm.tif, slope.tif, aspect.tif: co-registered rasters, same resolution/extent, clipped to the study area. Derived from national LiDAR DSM data (up to 1 m resolution), Piano Straordinario di Telerilevamento (PST), distributed via the Ministero dell'Ambiente e della Sicurezza Energetica geoportal. Licence: CC BY 4.0.
buildings.shp: building footprint polygons. Derived from the volumetric units class of the Database Topografico (DBGT), Geoportale della Lombardia.Licence: CC BY 4.0.

---

## Notes

- **No full-extent raster output, by design.** This script only writes the per-building statistics (GeoPackage) — it never builds a DSM/aspect raster covering the full input extent. An earlier version did build one (two full-size arrays in memory before writing), but for a large DSM this is a multi-gigabyte allocation - a ~23,000 × 38,000 px raster needs ~3.5 GB per array, ~7 GB for both — which failed intermittently depending on available RAM at run time. Since success then depended on machine state rather than the code itself, the full-mosaic step was dropped in favour of a version that behaves identically regardless of input size or free memory. If you need a visual of the MAD-filtered surface for a figure, export it separately for just the buildings you need.
- Handles rasters with no NoData value declared in their metadata (falls back to NaN internally) and rasters with stray NaN pixels even when NoData *is* declared as an ordinary sentinel value (e.g. near DSM gaps) - both are filtered out consistently.

## Limitations

- Bin widths and *k* values are reasonable defaults, not values tuned against this specific dataset.
- ASA is computed via k-nearest-neighbours (KDTree) rather than a fixed-size raster window - a related but not identical notion of "local neighbourhood."
