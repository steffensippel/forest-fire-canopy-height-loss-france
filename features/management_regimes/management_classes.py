# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 23:01:40 2026

@author: steff
load the 1km resolution management map. Then assign each patch the management type, where the centroid of the patch lies within the pixel 

the second part is for sanity check plotting. Plot a specific patch and check if the management type it lies in corresponds with the one in the saved file 
"""


import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from rasterio.mask import mask
from rasterio.features import rasterize
from shapely.geometry import mapping
from matplotlib import pyplot as plt
from shapely.geometry import box
from pathlib import Path 


dic_management = {1: "Unmanaged forest", 2: "Close-to-nature forestry", 3: "Combined objective forestry", 4: "Intensive forestry", 5: "Very intensive forestry"}
# ===================== INPUTS =====================

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"

path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\management_regimes"

path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"

path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"

# Map the forest management types (map has a 1km resolution) 
# classes : Forest is classified in 5 distinct forest management classes: unmanaged forest, close-to-nature forestry, combined objective forestry, intensive forestry and very intensive forestry
filename = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Mai\Forest_Management\doi-10.34894-hqijn5\Forest_management_map_raster.tif"

# open and plot the file: 
    
polygon_name = "V-001"

# ===================== LOAD POLYGON =====================
polygon_file = path_polygons + f"/{polygon_name}.gpkg"
gdf_polygon = gpd.read_file(polygon_file, encoding="latin1")
 
    
# load cut patches per polygon
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)


with rasterio.open(filename) as src:
    # reproject patch and get spatial centroid
    patches_proj = patches.to_crs(src.crs)
    centroids = patches_proj.geometry.centroid
    
    # get the coordinates of the centroid
    coords = [(p.x, p.y) for p in centroids]
    
    # compute the pixel where the centroid is in
    values = [v[0] for v in src.sample(coords)]

patches["management_class"] = values    
print(patches.columns)   

    


management_class = patches[['parent_id', 'polygon', 'TFV_num', 'forest_typ',
       'patch_id', 'management_class']]

management_class["management_type"] = (
    management_class.management_class
    .map(dic_management)
    .fillna("not_assigned")
)

print(len(management_class))
print(len(patches))
print(len(management_class[management_class.management_type == "not_assigned"]))

new_path = Path(path_to_save)
csv_filename = "management_class.csv"
management_class.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   


#%%
# === PLOTTING SANITY CHECK ===
 
with rasterio.open(filename) as src:

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

from rasterio.plot import plotting_extent

patch = patches[patches.patch_id == "V-001_1348"].to_crs(crs)

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
    color="red",
    linewidth=2
)

patch.plot(ax=ax, color = "black")

plt.colorbar(
    im,
    ax=ax,
    label="Forest management class"
)

plt.show()

    
    
# %% PATCH LEVEL: 
    
# load patches 
# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

patches_polygon = (
    patches[patches.polygon == polygon_name]
    .to_crs(crs)
    .copy()
)
    
#patches_polygon['patch_index'] = patches_polygon.index
patches_polygon['patches_area'] = patches_polygon.area
patches_polygon = patches_polygon.reset_index()

print(patches_polygon.columns)

# ===================== RASTERIZE PATCH IDS =====================

patch_raster = rasterize(
    [
        (geom, pid)
        for geom, pid in zip(
            patches_polygon.geometry,
            patches_polygon.index
        )
    ],
    out_shape=band.shape,
    transform=transform,
    fill=-1,
    dtype="int32",
    all_touched = True
)


# %% PATCH LEVEL ZUWEISUNG: 
import numpy as np
import pandas as pd
from rasterio.mask import mask
from shapely.geometry import mapping

# container for results
results = []

classes = [1, 2, 3, 4, 5]

for idx, row in patches_polygon.iterrows():
    
    geom = row.geometry

    # mask raster with patch geometry
    out_image, _ = mask(
        src,
        [mapping(geom)],
        crop=True,
        all_touched=True
    )

    vals = out_image[0].astype("float32").ravel()

    # remove nodata / nan
    vals = vals[~np.isnan(vals)]

    # optional: also remove 0 if it's background
    vals = vals[vals > 0]

    if len(vals) == 0:
        proportions = [np.nan] * len(classes)
    else:
        proportions = [(vals == c).sum() / len(vals) for c in classes]

    results.append([idx] + proportions)

# create dataframe
df_weights = pd.DataFrame(
    results,
    columns=["patch_index"] + [f"class_{c}" for c in classes]
)

# merge back to patches
patches_polygon = patches_polygon.merge(df_weights, on="patch_index")

#%%

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

# colormap
cmap = plt.get_cmap("tab20", len(dic_management))

# --- build legend ---
legend_patches = [
    mpatches.Patch(
        color=cmap(i - 1),  # shift because tab20 starts at 0
        label=dic_management[i]
    )
    for i in dic_management.keys()
]



fig, ax = plt.subplots(figsize=(12, 8), constrained_layout=True)

ax.imshow(band, cmap=cmap, vmin=1, vmax=5)

gdf_polygon.plot(ax=ax, facecolor="none", edgecolor="black")

ax.legend(
    handles=legend_patches,
    title="Forest management",
    loc="center left",
    bbox_to_anchor=(1.02, 0.5)
)

plt.show()

