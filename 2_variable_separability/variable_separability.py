# -*- coding: utf-8 -*-
"""
Confronto tra variabili per separare tetti piani e non piani.

Legge un layer di edifici gia' classificato (campo tipo_2 = "piano",
"falde"/"falda", "curvo", ...) e per ogni variabile numerica calcola
quanto separa bene il gruppo "piano" dal resto, usando la stessa metrica
a gap tra percentili gia' usata nel paper per scegliere l'indice PV
migliore (25esimo percentile di un gruppo vs 75esimo dell'altro).

Salva una tabella CSV con la classifica e una griglia di istogrammi
(mai a schermo, sempre su file).

Autore: Margherita Moretti
"""

import csv
import os

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")  # non aprire mai una finestra, salva sempre su file
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------
# INPUT - modifica questi valori
# --------------------------------------------------
input_path = r"C:\Users\user\OneDrive - Politecnico di Milano\fotovoltaico_OneDrive\caso_studio\morphology.gpkg"
type_field = "tipo"
output_dir = r"C:\Users\user\OneDrive - Politecnico di Milano\fotovoltaico_OneDrive\caso_studio\separability_output"
n_bins = 30

# Estendi questi due insiemi se usi altre etichette (es. "piano_irregolare")
FLAT_LABELS = {"piano"}
NONFLAT_LABELS = {"falde", "falda", "curvo"}


# --------------------------------------------------
# FUNZIONI
# --------------------------------------------------
def separability_score(vals_a, vals_b):
    """Gap tra percentili: max(|p75_a - p25_b|, |p75_b - p25_a|).
    Piu' alto = separazione migliore. Va calcolato su valori normalizzati
    (vedi zscore_normalize) quando le variabili hanno unita' diverse,
    altrimenti una variabile in gradi (0-90) vince sempre su una tra
    -1 e 1, indipendentemente da chi separa meglio davvero."""
    a25, a75 = np.percentile(vals_a, [25, 75])
    b25, b75 = np.percentile(vals_b, [25, 75])
    return float(max(abs(a75 - b25), abs(b75 - a25)))


def zscore_normalize(vals_a, vals_b):
    """Normalizza (z-score) usando media e deviazione standard dei due
    gruppi uniti - lo stesso passaggio che fai nel paper per rendere
    confrontabili indici diversi."""
    pooled = np.concatenate([vals_a, vals_b])
    mu, sd = pooled.mean(), pooled.std()
    if sd == 0:
        return vals_a - mu, vals_b - mu
    return (vals_a - mu) / sd, (vals_b - mu) / sd


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    os.makedirs(output_dir, exist_ok=True)

    gdf = gpd.read_file(input_path)
    if type_field not in gdf.columns:
        raise ValueError(f"Campo '{type_field}' non trovato. Colonne disponibili: {list(gdf.columns)}")

    # ---- controllo etichette ----
    label_counts = gdf[type_field].value_counts(dropna=False)
    unknown = set(label_counts.index.astype(str)) - FLAT_LABELS - NONFLAT_LABELS
    print(f"Conteggio etichette in '{type_field}':")
    print(label_counts.to_string())
    if unknown:
        print(f"\nATTENZIONE - etichette non in FLAT_LABELS/NONFLAT_LABELS (escluse da "
              f"entrambi i gruppi): {unknown}\n  -> se vanno incluse, aggiungile agli insiemi "
              f"in cima allo script.")

    is_flat = gdf[type_field].isin(FLAT_LABELS)
    is_nonflat = gdf[type_field].isin(NONFLAT_LABELS)
    print(f"\nPiano: {int(is_flat.sum())} edifici | Non piano: {int(is_nonflat.sum())} edifici "
          f"| Esclusi/non etichettati: {len(gdf) - int(is_flat.sum()) - int(is_nonflat.sum())}\n")

    candidate_vars = [
        c for c in gdf.columns
        if c not in (type_field, "geometry") and np.issubdtype(gdf[c].dtype, np.number)
    ]

    # ---- classifica di separabilita' ----
    rows = []
    for var in candidate_vars:
        vals_flat = gdf.loc[is_flat, var].dropna().values
        vals_nonflat = gdf.loc[is_nonflat, var].dropna().values
        if len(vals_flat) < 5 or len(vals_nonflat) < 5:
            continue  # troppi pochi dati per fidarsi di un percentile

        norm_flat, norm_nonflat = zscore_normalize(vals_flat, vals_nonflat)
        rows.append({
            "variable": var,
            "separability": separability_score(norm_flat, norm_nonflat),
            "median_flat": float(np.median(vals_flat)),        # unita' originali, solo per leggibilita'
            "median_nonflat": float(np.median(vals_nonflat)),
            "n_flat": len(vals_flat),
            "n_nonflat": len(vals_nonflat),
        })

    ranking = sorted(rows, key=lambda r: r["separability"], reverse=True)

    print("=== Classifica separabilita' (valori normalizzati, piu' alto = separa meglio) ===")
    header = f"{'variabile':<24}{'separability':>14}{'median_piano':>14}{'median_altro':>16}{'n_piano':>8}{'n_altro':>10}"
    print(header)
    print("-" * len(header))
    for r in ranking:
        print(f"{r['variable']:<24}{r['separability']:>14.4f}{r['median_flat']:>14.4f}"
              f"{r['median_nonflat']:>16.4f}{r['n_flat']:>8}{r['n_nonflat']:>10}")

    csv_path = os.path.join(output_dir, "separability_ranking.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["variable", "separability", "median_flat", "median_nonflat", "n_flat", "n_nonflat"])
        writer.writeheader()
        writer.writerows(ranking)
    print(f"\nClassifica salvata in: {csv_path}")

    # ---- griglia di istogrammi ----
    n = len(candidate_vars)
    if n > 0:
        ncols = 4
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.5 * ncols, 3.2 * nrows))
        axes = np.atleast_1d(axes).ravel()

        for ax, var in zip(axes, candidate_vars):
            vals_flat = gdf.loc[is_flat, var].dropna().values
            vals_nonflat = gdf.loc[is_nonflat, var].dropna().values
            if len(vals_flat) == 0 and len(vals_nonflat) == 0:
                ax.set_visible(False)
                continue
            ax.hist(vals_nonflat, bins=n_bins, alpha=0.6, color="orange", label="Non piano")
            ax.hist(vals_flat, bins=n_bins, alpha=0.6, color="steelblue", label="Piano")
            ax.set_title(var, fontsize=9)
            ax.tick_params(labelsize=7)

        for ax in axes[n:]:
            ax.set_visible(False)
        axes[0].legend(fontsize=8)
        fig.tight_layout()

        grid_path = os.path.join(output_dir, "histograms_grid.png")
        fig.savefig(grid_path, dpi=150)
        plt.close(fig)
        print(f"Griglia istogrammi salvata in: {grid_path}")


if __name__ == "__main__":
    main()
