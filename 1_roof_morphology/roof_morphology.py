# -*- coding: utf-8 -*-
"""
Statistiche dei tetti da DSM/slope/aspect + poligoni edifici.

Per ogni edificio calcola:
- filtro MAD sul DSM per togliere i valori anomali (antenne, condizionatori...)
- entropia di elevazione, pendenza ed esposizione (su valori raggruppati in
  bin)
- indice ASA (Aspect Spatial Autocorrelation): quanto e' coerente la
  direzione di esposizione tra pixel vicini. Vicino a 1 = falda inclinata
  coerente, vicino a 0 = tetto piano/rumoroso. Indice che verrà poi utilizzato
  per isolare i tetti piani
- roughness (deviazione standard locale dell'elevazione)

Salva: un GeoPackage con le statistiche per edificio. Campi numerici come
FLOAT64 (DOUBLE).

"""

import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
import numpy as np
from scipy.spatial import cKDTree

# --------------------------------------------------
# INPUT - modifica questi percorsi con i tuoi
# --------------------------------------------------
raster_path = "data/dsm_clipped.tif"
slope_path = "data/slope_clipped.tif"
aspect_path = "data/aspect_clipped.tif"
buildings_path = "data/buildings.shp"

output_gpkg = "output/edifici_statistiche.gpkg"

# --------------------------------------------------
# PARAMETRI
# --------------------------------------------------
MAD_THRESHOLD = 3.0        # soglia z-score per il filtro MAD
ASA_K = 8                  # numero di vicini per l'indice ASA
ROUGHNESS_K = 12           # numero di vicini per la roughness
BIN_ELEVAZIONE = 0.25      # ampiezza bin (m) per l'entropia dell'elevazione
BIN_PENDENZA = 2.0         # ampiezza bin (gradi) per l'entropia della pendenza
BIN_ASPECT = 10.0          # ampiezza bin (gradi) per l'entropia dell'esposizione


# --------------------------------------------------
# FUNZIONI
# --------------------------------------------------
def is_valid(values, nodata):
    """True per i pixel utilizzabili: non NoData e non NaN.

    Gestisce tre casi: nodata non definito nel raster (None - allora conta
    solo NaN), nodata definito come NaN, e nodata definito come un numero
    normale (es. -9999) - in quest'ultimo caso i NaN "estranei" (es. su
    slope/aspect calcolati vicino a un buco nel DSM) vengono comunque
    esclusi, non solo il valore -9999 dichiarato."""
    values = np.asarray(values)
    not_nan = ~np.isnan(values) if np.issubdtype(values.dtype, np.floating) else np.ones(values.shape, dtype=bool)
    if nodata is None:
        return not_nan
    try:
        if np.isnan(nodata):
            return not_nan
    except TypeError:
        pass
    return not_nan & (values != nodata)


def entropy(values, bin_width=None):
    """Entropia di Shannon (base 2).

    Con dati continui (elevazione, pendenza, aspect) serve bin_width:
    altrimenti quasi ogni pixel ha un valore diverso da tutti gli altri,
    e l'entropia non è in grado di misurare quanto e' complessa 
    la superficie."""
    if len(values) == 0:
        return np.nan

    if bin_width is None:
        vals, counts = np.unique(values, return_counts=True)
    else:
        vmin, vmax = values.min(), values.max()
        if not np.isfinite(vmin) or not np.isfinite(vmax):
            return np.nan 
        if vmax <= vmin:
            return 0.0
        edges = np.arange(vmin, vmax + bin_width, bin_width)
        counts, _ = np.histogram(values, bins=edges)
        counts = counts[counts > 0]

    if len(counts) == 0:
        return np.nan

    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p)))


def local_aspect_coherence(aspect_deg, coords, k=8):
    """Indice ASA (Aspect Spatial Autocorrelation): media pesata (per
    distanza inversa) del coseno della differenza di aspect tra ogni
    pixel e i suoi k vicini piu' prossimi. Vicino a 1 = direzioni
    coerenti (falda), vicino a 0 = direzioni casuali (tetto piano)."""
    n = len(aspect_deg)
    if n < 3:
        return np.nan

    theta = np.deg2rad(aspect_deg)
    U = np.column_stack((np.cos(theta), np.sin(theta)))
    tree = cKDTree(coords)
    k_actual = min(k + 1, n)
    distances, indices = tree.query(coords, k=k_actual)

    local_I = np.zeros(n)
    for i in range(n):
        ui = U[i]
        Ii = 0.0
        wsum = 0.0
        for j_idx, j in enumerate(indices[i]):
            if i == j:
                continue
            w = 1.0 / (distances[i, j_idx] + 1e-10)
            Ii += w * np.dot(ui, U[j])
            wsum += w
        local_I[i] = Ii / wsum if wsum > 0 else np.nan

    return float(np.nanmean(local_I))


def roughness_knn(z_vals, coords, k):
    """Deviazione standard media dei k vicini piu' prossimi in elevazione."""
    n = len(z_vals)
    if n < 3:
        return np.nan

    z = np.array(z_vals, dtype=float)
    tree = cKDTree(coords)
    k_actual = min(k + 1, n)
    distances, indices = tree.query(coords, k=k_actual)

    local_std_vals = np.zeros(n)
    for i in range(n):
        neigh_mask = distances[i] > 0
        neigh_idx = indices[i][neigh_mask]
        if len(neigh_idx) > 1:
            local_std_vals[i] = np.std(z[neigh_idx])
        else:
            local_std_vals[i] = np.nan

    return float(np.nanmean(local_std_vals))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    output_dir = os.path.dirname(output_gpkg) or "."
    os.makedirs(output_dir, exist_ok=True)

    # ---- load data ----
    gdf = gpd.read_file(buildings_path)
    src_dsm = rasterio.open(raster_path)
    src_slope = rasterio.open(slope_path)
    src_aspect = rasterio.open(aspect_path)


    dsm_fill = src_dsm.nodata if src_dsm.nodata is not None else np.nan
    slope_fill = src_slope.nodata if src_slope.nodata is not None else np.nan
    aspect_fill = src_aspect.nodata if src_aspect.nodata is not None else np.nan

    float_fields = [
        "z_min", "z_max", "z_range",
        "entropia", "entropia_filtrata",
        "pend_media", "pend_media_filtrata",
        "pend_var", "pend_var_filtrata",
        "pend_entropia", "pend_entropia_filtrata",
        "asp_entropia", "asp_entropia_filtrata",
        "asp_asa", "asp_asa_filtrata",
        "varianza", "roughness", "n_pixels",
    ]

    for f in float_fields:
        gdf[f] = np.nan

    # ---- loop edifici ----
    for idx, row in gdf.iterrows():
        geom = [row.geometry]

        dsm_img, dsm_transform = mask(src_dsm, geom, crop=True)
        slope_img, _ = mask(src_slope, geom, crop=True)
        aspect_img, _ = mask(src_aspect, geom, crop=True)

        dsm_data = dsm_img[0]
        slope_data = slope_img[0]
        aspect_data = aspect_img[0]

        mask_poly = geometry_mask(geom, out_shape=dsm_data.shape, transform=dsm_transform, invert=True)

        # ---- elevazione ----
        dsm_vals = dsm_data[mask_poly]
        dsm_vals = dsm_vals[is_valid(dsm_vals, dsm_fill)]
        if len(dsm_vals) == 0:
            continue

        gdf.at[idx, "entropia"] = entropy(dsm_vals, bin_width=BIN_ELEVAZIONE)

        # ---- filtro MAD ----
        median_z = np.median(dsm_vals)
        mad = np.median(np.abs(dsm_vals - median_z))
        if mad == 0:
            mad = 1e-6

        z_score = 0.6745 * np.abs(dsm_data - median_z) / mad
        filtered_patch = np.where(z_score <= MAD_THRESHOLD, dsm_data, dsm_fill)

        filtered_vals = filtered_patch[mask_poly]
        filtered_vals = filtered_vals[is_valid(filtered_vals, dsm_fill)]

        gdf.at[idx, "entropia_filtrata"] = entropy(filtered_vals, bin_width=BIN_ELEVAZIONE)
        gdf.at[idx, "n_pixels"] = len(filtered_vals)

        if len(filtered_vals) > 0:
            gdf.at[idx, "z_min"] = float(np.min(filtered_vals))
            gdf.at[idx, "z_max"] = float(np.max(filtered_vals))
            gdf.at[idx, "varianza"] = float(np.var(filtered_vals))
            gdf.at[idx, "z_range"] = float(np.ptp(filtered_vals))
        else:
            gdf.at[idx, "z_range"] = 0.0

        # ---- pendenza ----
        slope_vals = slope_data[mask_poly]
        slope_vals = slope_vals[is_valid(slope_vals, slope_fill)]

        gdf.at[idx, "pend_media"] = np.mean(slope_vals) if len(slope_vals) else np.nan
        gdf.at[idx, "pend_entropia"] = entropy(slope_vals, bin_width=BIN_PENDENZA)
        gdf.at[idx, "pend_var"] = np.var(slope_vals) if len(slope_vals) > 1 else np.nan

        slope_filt = slope_data.copy()
        slope_filt[~is_valid(filtered_patch, dsm_fill)] = slope_fill
        slope_vals_f = slope_filt[mask_poly]
        slope_vals_f = slope_vals_f[is_valid(slope_vals_f, slope_fill)]

        gdf.at[idx, "pend_media_filtrata"] = np.mean(slope_vals_f) if len(slope_vals_f) else np.nan
        gdf.at[idx, "pend_entropia_filtrata"] = entropy(slope_vals_f, bin_width=BIN_PENDENZA)
        gdf.at[idx, "pend_var_filtrata"] = np.var(slope_vals_f) if len(slope_vals_f) > 1 else np.nan

        # ---- aspect + ASA ----
        rows, cols = np.where(mask_poly)

        aspect_all = aspect_data[mask_poly]
        valid = is_valid(aspect_all, aspect_fill)
        aspect_vals = aspect_all[valid]
        coords = np.column_stack([rows[valid], cols[valid]])

        gdf.at[idx, "asp_entropia"] = entropy(aspect_vals, bin_width=BIN_ASPECT)
        gdf.at[idx, "asp_asa"] = local_aspect_coherence(aspect_vals, coords, k=ASA_K)

        aspect_filt = aspect_data.copy()
        aspect_filt[~is_valid(filtered_patch, dsm_fill)] = aspect_fill

        aspect_all_f = aspect_filt[mask_poly]
        valid_f = is_valid(aspect_all_f, aspect_fill)
        aspect_vals_f = aspect_all_f[valid_f]
        coords_f = np.column_stack([rows[valid_f], cols[valid_f]])

        gdf.at[idx, "asp_entropia_filtrata"] = entropy(aspect_vals_f, bin_width=BIN_ASPECT)
        gdf.at[idx, "asp_asa_filtrata"] = local_aspect_coherence(aspect_vals_f, coords_f, k=ASA_K)

        # ---- roughness ----
        rows_filt, cols_filt = np.where(mask_poly & is_valid(filtered_patch, dsm_fill))
        coords_filtered = np.column_stack([rows_filt, cols_filt])
        gdf.at[idx, "roughness"] = roughness_knn(filtered_vals, coords_filtered, k=ROUGHNESS_K)

    # ---- salvataggi ----
    if "fid" in gdf.columns:
        gdf = gdf.drop(columns=["fid"])

    for f in float_fields:
        gdf[f] = gdf[f].astype("float64")

    gdf.to_file(output_gpkg, driver="GPKG")

    print("Elaborazione completata")
    print(f"Statistiche salvate: {output_gpkg}")


if __name__ == "__main__":
    main()
