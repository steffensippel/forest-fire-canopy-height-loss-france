

# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 00:48:01 2026

@author: steff

Computes statistics of topographic feature per patch
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

import geopandas as gpd
from rasterio.plot import plotting_extent

from pathlib import Path 



# ===================== INPUTS =====================
# we look at: "altitude", "aspect_cos", "aspect_sin", "slope" 
characteristic = "slope"

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"

#adjust!!!
path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\topography"

path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"

path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"
path_slope = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\slope_altitude_aspect\slope_100.tif"

# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

#polygons = ["Q-048", "V-001"]

#%%
def processing(trait, polygons): 
    # save results in: 
    path_trait = fr"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\slope_altitude_aspect\{trait}_100.tif"
    results = []
     
    for i, polygon_name in enumerate(polygons): 
        
        polygon_name = polygon_name.strip()
        print(polygon_name)
        
        if i % 50 == 0:
            print(i, polygon_name)
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
        
        with rasterio.open(path_trait) as src:
            #print(f"{trait}:", src.meta)
            #print(f"{trait}:", src.tags())
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
            stats=["min", "max", "mean", "std", "count", "median", "percentile_25", "percentile_75", "percentile_95"],
            nodata=src.nodata
        )
        
        df = pd.DataFrame(stats)
        df = df.rename(columns={
            "min": f"{trait}_min",
            "max": f"{trait}_max",
            "mean": f"{trait}_mean",
            "std": f"{trait}_std",
            "count": f"{trait}_count",
            "median": f"{trait}_median",
            "percentile_25": f"{trait}_q25",
            "percentile_75": f"{trait}_q75",
            "percentile_95": f"{trait}_q95"
        })

        
        df["patch_id"] = gdf["patch_id"].values
        df["forest_typ"] = gdf["forest_typ"].values
        df["polygon"] = polygon_name
    
        results.append(df)
        
        '''Included sanity check for each polygon'''
        
        # get a random patch index. 
        patch_indices = patches_polygon.patch_id.unique()
        random_patch_id = np.random.choice(patches_polygon.patch_id.unique())
        #print(random_patch_id)
        
        patch = gdf[gdf.patch_id == random_patch_id]
        row = df[df.patch_id == random_patch_id].iloc[0]
        minimum = row[f'{trait}_min']
        median = row[f'{trait}_median']
        
        #print(minimum, median)
        '''
        fig, ax = plt.subplots(figsize=(8, 6))
        
        extent = plotting_extent(band, transform)
        
        im = ax.imshow(
            band,
            cmap="viridis",
            extent=extent,
            vmin=np.nanpercentile(band, 2),
            vmax=np.nanpercentile(band, 98)
        )
        
        plt.colorbar(im, ax=ax, label= f"{trait}")
        
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
        
        plt.title(f"{trait}, min = {minimum}, median = {median}")
        plt.show()
        '''
        
        '''end included sanity check'''
        
    df = pd.concat(results, ignore_index=True)
    
    
    
    return df 

#%%

df_slope = processing("slope", polygons)
df_altitude = processing("altitude", polygons)
df_aspect_cos = processing("aspect_cos", polygons)
df_aspect_sin = processing("aspect_sin", polygons)

# correct for units: 


print(len(df_slope))
print(len(df_altitude))
print(len(df_aspect_cos))
print(len(df_aspect_sin))

for name, df in [
    ("slope", df_slope),
    ("altitude", df_altitude),
    ("aspect_cos", df_aspect_cos),
    ("aspect_sin", df_aspect_sin)
]:
    print(name)
    print("Total rows:", len(df))
    print("Rows with NaN:", df.isna().any(axis=1).sum())
    print("Total NaN values:", df.isna().sum().sum())
    print()

nan_rows_slope = df_slope[df_slope.isna().any(axis=1)]

print(nan_rows_slope)


# get units and do sanity check if that makes sense! 

# we can save them as individual files: 

# merge on patch_id    
# merge them:
'''
df_topography = (
    df_slope
    .merge(df_altitude, on="patch_id", how="inner")
    .merge(df_aspect_cos, on="patch_id", how="inner")
    .merge(df_aspect_sin, on="patch_id", how="inner")
)
'''
#%%
# Save files 

new_path = Path(path_to_save)
csv_filename = "slope.csv"
df_slope.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")

csv_filename = "altitude.csv"
df_altitude.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")

csv_filename = "aspect_cos.csv"
df_aspect_cos.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")

csv_filename = "aspect_sin.csv"
df_aspect_sin.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")

