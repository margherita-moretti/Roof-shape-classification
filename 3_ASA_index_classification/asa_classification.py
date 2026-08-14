# -*- coding: utf-8 -*-
"""
Classificazione flat/sloped da soglia sull'indice ASA.

Legge il GeoPackage prodotto da roof_morphology.py (stage 1), che ha gia'
l'indice ASA medio per edificio (asp_asa / asp_asa_filtrata), e aggiunge
un campo "classe": flat se ASA < soglia, sloped altrimenti.

Autore: Margherita Moretti
"""

import os
import numpy as np
import geopandas as gpd

# --------------------------------------------------
# INPUT 
# --------------------------------------------------
input_gpkg = r"...\1_roof_morphology\roof_morphology_output\morphology.gpkg"
output_gpkg = r"...\3_ASA_index_classification\classified_buildings.gpkg"


ASA_FIELD = "asp_asa_filtrata"
ASA_THRESHOLD = 0.6   # calibrato nello stage 2 (variable_separability)


def classify_asa(asa):
    """'flat' se ASA < soglia, 'sloped' se ASA >= soglia, None se l'ASA
    non e' stato calcolato per quell'edificio (es. troppo pochi pixel
    validi) - un NaN non classificato non deve finire in
    una delle due classi."""
    if asa is None or (isinstance(asa, float) and np.isnan(asa)):
        return None
    return "flat" if asa < ASA_THRESHOLD else "sloped"


def main():
    os.makedirs(os.path.dirname(output_gpkg) or ".", exist_ok=True)

    gdf = gpd.read_file(input_gpkg)

    if ASA_FIELD not in gdf.columns:
        raise ValueError(f"Campo '{ASA_FIELD}' non trovato. Colonne disponibili: {list(gdf.columns)}")

    gdf["classe"] = gdf[ASA_FIELD].apply(classify_asa)

    n_piano = (gdf["classe"] == "flat").sum()
    n_sloped = (gdf["classe"] == "sloped").sum()
    n_non_class = gdf["classe"].isna().sum()

    print(f"Campo usato: {ASA_FIELD}  |  soglia: {ASA_THRESHOLD}")
    print(f"Flat:            {n_piano}")
    print(f"Sloped:           {n_sloped}")
    print(f"Non classificati: {n_non_class}  (ASA mancante per pochi pixel validi)")

    gdf.to_file(output_gpkg, driver="GPKG")
    print(f"\nSalvato: {output_gpkg}")


if __name__ == "__main__":
    main()
