# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 09:12:05 2026

@author: steff
"""

# extract the soil properties for the polygons: for now we obtain one mean value per polygon -> adjust this to the patch size. Take care depending on the resolution! 


# import packages 
import rasterio 
from matplotlib import pyplot as plt
import geopandas as gpd

from shapely.geometry import box, mapping, Point

from rasterio.windows import from_bounds
from rasterio.mask import mask
import numpy as np 
from rasterio.plot import plotting_extent
import pandas as pd
from pathlib import Path
from rasterstats import zonal_stats

# ===== STRUCTURE OF FILES ========
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"
path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\soil_properties"

path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"

path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"

# SOIL PROPERTY FILES: 
# ph file 
filename_ph = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/soil properties/ph_2008/ph_2008.tif"
 
# reserve utile file 
# this is for annual 
filename_ru = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/soil properties/ru_6190_an_v1/ru_6190_an_v1.tif"

# this is for the summer time: 
#filename_ru = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/soil properties/ru_6190_et_v1/ru_6190_et_v1.tif"

# topographic wetness
filename_twi = r"C:\Users\steff\Documents\06-Internshi_Paris\00_April\soil properties\topographic_wetness\TWI_100.tif"

# ===== LOAD PATCHES AND POLYGONS TO PROCESS ======
# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

# %% PH PIPELINE:
    
# load cut patches per polygon
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)
#patches = patches[patches.polygon == polygon_name]


with rasterio.open(filename_ph) as src:
    # reproject patch and get spatial centroid
    patches_proj = patches.to_crs(src.crs)
    centroids = patches_proj.geometry.centroid
    
    # get the coordinates of the centroid
    coords = [(p.x, p.y) for p in centroids]
    
    # compute the pixel where the centroid is in
    values = [v[0] for v in src.sample(coords)]

patches["ph_value"] = values    
print(patches.columns)   

    


ph_values = patches[['parent_id', 'polygon', 'TFV_num', 'forest_typ',
       'patch_id', 'ph_value']]

print(len(ph_values))

nan_rows = ph_values[ph_values.isna().any(axis=1)]
print(nan_rows)


# %% SANITY CHECK FOR THE PH: 
# === PLOTTING SANITY CHECK ===
patch_id = "V-016_360" 
polygon_name = "V-016"

# ===================== LOAD POLYGON =====================
polygon_file = path_polygons + f"/{polygon_name}.gpkg"
gdf_polygon = gpd.read_file(polygon_file, encoding="latin1")

with rasterio.open(filename_ph) as src:
    # match CRS
    #gdf_polygon = gdf_polygon.to_crs(src.crs)
    # 1. match CRS FIRST
    gdf_polygon_proj = gdf_polygon.to_crs(src.crs)


    
    minx, miny, maxx, maxy = gdf_polygon_proj.total_bounds
    bbox_geom = box(minx, miny, maxx, maxy).buffer(1000)

    # clip raster
    data, transform = mask(
        src,
        [mapping(bbox_geom)],   
        crop=True, 
        all_touched = True
    )
    
    band = data[0].astype("float32")

    # convert nodata to nan
    if src.nodata is not None:
        band[band == src.nodata] = np.nan

    crs = src.crs


patch = patches[patches.patch_id == patch_id].to_crs(crs)

extent = plotting_extent(band, transform)

fig, ax = plt.subplots(figsize=(8,6))

im = ax.imshow(
    band,
    extent=extent,
    origin="upper", 
    alpha = 0.5
)

gdf_polygon_proj.boundary.plot(
    ax=ax,
    color="black",
    linewidth=0.5, 
    alpha = 0.5
)

patch.plot(ax=ax, color = "red", linewidth = 5)

plt.colorbar(
    im,
    ax=ax,
    label="ph value"
)

plt.title(ph_values[ph_values.patch_id == patch_id].ph_value)

plt.show()
#%%
new_path = Path(path_to_save)
csv_filename = "ph.csv"
ph_values.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

# %% Reserve Utile pipeline: 
  
# ===== LOAD PATCHES AND POLYGONS TO PROCESS ======
# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

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
    
    with rasterio.open(filename_ru) as src:
       
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
        stats=["min", "max", "mean"],
        nodata=src.nodata
    )
    
    df = pd.DataFrame(stats)

    
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
    mean = row["mean"]
    minimum = row["min"]
    
    
    #print(minimum, median)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    extent = plotting_extent(band, transform)
    
    im = ax.imshow(
        band,
        cmap="viridis",
        extent=extent,
        vmin=np.nanpercentile(band, 2),
        vmax=np.nanpercentile(band, 98)
    )
    
    plt.colorbar(im, ax=ax, label= "reserve utile")
    
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
    
    plt.title(f" mean = {mean}, minimum = {minimum}")
    plt.show()
    
    
    '''end included sanity check'''
    
df_reserve_utile = pd.concat(results, ignore_index=True)

print(len(df_reserve_utile))


nan_rows = df_reserve_utile[df_reserve_utile.isna().any(axis=1)]
print(nan_rows)



#%% save reserver utile
new_path = Path(path_to_save)
csv_filename = "reserve_utile.csv"
df_reserve_utile.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

#%% topographic wetness index pipeling: 
    
  
# ===== LOAD PATCHES AND POLYGONS TO PROCESS ======
# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

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
    
    with rasterio.open(filename_twi) as src:
       
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
        stats=["mean"],
        nodata=src.nodata
    )
    
    df = pd.DataFrame(stats)

    
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
    mean = np.round(row["mean"],2)
    
    
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
    
    plt.colorbar(im, ax=ax, label= "TWI")
    
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
    
    plt.title(f"Topographic Wetness Index red patch \n mean = {mean}")
    plt.show()
    '''
    
    '''end included sanity check'''
    
df_topographic_wetness = pd.concat(results, ignore_index=True)

print(len(df_topographic_wetness))

nan_rows = df_topographic_wetness[df_topographic_wetness.isna().any(axis=1)]
print(nan_rows)



#%% save reserver utile
new_path = Path(path_to_save)
csv_filename = "topographic_wetness_index.csv"
df_topographic_wetness.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")  
    
    

