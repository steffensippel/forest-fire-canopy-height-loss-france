# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 00:48:01 2026

@author: steff

Computes minimum and median distance to road for each 1 ha patch 
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from shapely.geometry import box, mapping
from matplotlib import pyplot as plt

import rasterio.mask
from rasterstats import zonal_stats
import rasterio


# ===================== INPUTS =====================

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"

#adjust!!!
path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\distance_to_road"

path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"

path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"
path_distance_roads = local_folder + "data/proximite_route_30m.tif"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

# save results in: 
results = []
 
for polygon_name in polygons: 
    polygon_name = polygon_name.strip()
    print(polygon_name)
    
    # ===================== LOAD POLYGON =====================
    polygon_file = path_polygons + f"/{polygon_name}.gpkg"
    gdf_polygon = gpd.read_file(polygon_file, encoding="latin1")
    
    polygon_file = path_polygons + f"/{polygon_name}.gpkg"
    gdf_polygon = gpd.read_file(polygon_file, encoding="latin1")
    crs_polygon = gdf_polygon.crs
  
    # get box around polygon. 
    # ===================== LOAD PATCHES =====================
    patches_polygon = patches[patches.polygon == polygon_name].to_crs("EPSG:2154").copy()
    patches_polygon["patches_area"] = patches_polygon.geometry.area
    patches_polygon = patches_polygon.reset_index(drop=True)
    
    # load the distance to road map for this box 
    
    with rasterio.open(path_distance_roads) as src:
        #band = src.read(1)
        #affine = src.transform
        # --- reproject polygon to raster CRS ---
        gdf_proj = gdf_polygon.to_crs(src.crs)
   
        # --- buffered bounding box ---
        buffer = 500
        minx, miny, maxx, maxy = gdf_proj.total_bounds
   
        bbox = box(
            minx - buffer, miny - buffer,
            maxx + buffer, maxy + buffer
        )
   
        # --- clip raster ---
        data, transform = rasterio.mask.mask(
            src,
            [mapping(bbox)],
            crop=True
        )
   
        band = data[0].astype("float32")
   
        if src.nodata is not None:
            band[band == src.nodata] = np.nan

    gdf = patches_polygon.copy().reset_index(drop=True)
    gdf = gdf.to_crs(src.crs)
    
    stats = zonal_stats(
        gdf,
        band,
        affine=transform,
        stats=["min", "median"],
        nodata=src.nodata
    )
    
    df = pd.DataFrame(stats)

    df["patch_id"] = gdf["patch_id"].values
    df["forest_typ"] = gdf["forest_typ"].values
    df["polygon"] = polygon_name

    results.append(df)

df_distance_to_road = pd.concat(results, ignore_index=True)

print(df_distance_to_road.head())
print(len(df_distance_to_road))




#SAVING FILE 
csv_filename = "distance_to_road.csv"
path = path_to_save + f"/{csv_filename}"
df_distance_to_road.to_csv(path, index=False, sep=";", float_format="%.3f", decimal=".")


print(len(df_distance_to_road))
print(len(patches))

print("Number of distance-to-road rows:", len(df_distance_to_road))
print("Number of patches:", len(patches))

print("\nMissing values:")
print(df_distance_to_road.isna().sum())

missing_patch_ids = df_distance_to_road.loc[
    df_distance_to_road["min"].isna() |
    df_distance_to_road["median"].isna(),
    "patch_id"
]

print(missing_patch_ids)

#%%

# SANITY CHECK 
import matplotlib.pyplot as plt
import geopandas as gpd
from rasterio.plot import plotting_extent

patch_iden = "AQ-020_25"
patch = gdf[gdf.patch_id == patch_iden]
row = df[df.patch_id == patch_iden].iloc[0]
minimum = row['min']
median = row['median']

print(minimum, median)

fig, ax = plt.subplots(figsize=(8, 6))

extent = plotting_extent(band, transform)

im = ax.imshow(
    band,
    cmap="viridis",
    extent=extent,
    vmin=np.nanpercentile(band, 2),
    vmax=np.nanpercentile(band, 98)
)

plt.colorbar(im, ax=ax, label="Distance to road")

# plot patch
patch.plot(
    ax=ax,
    facecolor="none",
    edgecolor="red",
    linewidth=2
)

# plot polygon boundary
gdf_polygon.to_crs(src.crs).boundary.plot(
    ax=ax,
    color="black",
    linewidth=1
)

plt.title(f"min = {minimum}, median = {median}")
plt.show()


