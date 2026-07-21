# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:57:55 2026

@author: steff

get shape indices of the polygon shapes 
"""
import geopandas as gpd
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd 
from pathlib import Path 

# Define how to compute the indices: 

# load all the polygon shapes.
'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"


path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\polygon_shapes"

# get the relevant polygons: 

path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"
path_slope = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\slope_altitude_aspect\slope_100.tif"

# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

# polygon files 
path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"


results = []

for polygon_name in polygons:

    polygon_file = path_polygons + f"/{polygon_name}.gpkg"

    gdf_polygon = gpd.read_file(
        polygon_file,
        encoding="latin1"
    )

    gdf_polygon = gdf_polygon.to_crs("EPSG:2154")

    # compute indices
    area_m2 = gdf_polygon.geometry.area.sum()
    area_ha = area_m2 / 10000

    edge_length = gdf_polygon.geometry.length.sum()

    edge_density = edge_length / area_ha

    # like in the FragStats package 
    landscape_shape_index = edge_length / (
        np.sqrt(area_m2)
    )

    # plot example
    fig, ax = plt.subplots(figsize=(8,6))
    gdf_polygon.plot(ax=ax)

    ax.set_title(
        f"{polygon_name}\n"
        f"edge length: {edge_length:.1f} m\n"
        f"edge density: {edge_density:.2f} m/ha\n"
        f"LSI: {landscape_shape_index:.2f}"
    )

    plt.show()

    # store results
    results.append({
        "polygon": polygon_name,
        "area_ha": area_ha,
        "area_m2": area_m2,
        "edge_length": edge_length,
        "edge_density": edge_density,
        "landscape_shape_index": landscape_shape_index
    })

results_df = pd.DataFrame(results)

print(len(results_df))
#%%
new_path = Path(path_to_save)
csv_filename = "polygon_shape.csv"
results_df.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   


# now 
