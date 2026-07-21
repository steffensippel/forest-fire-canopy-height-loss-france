# -*- coding: utf-8 -*-
"""
Created on Fri May 15 11:24:33 2026

@author: steff

get a dnbr statistics values per polygon patch 
"""
# LOAD AND PROCESS THE DNBR FILES FROM LILIAN: 
import pandas as pd 
import geopandas as gpd
import rasterio
from pathlib import Path 
from matplotlib import pyplot as plt 
from rasterio.features import rasterize, geometry_mask
import numpy as np 

# FUNCTIONS: 
# function to compute all the stats 
def summary_stats(arr):
# Remove NaNs
    arr = arr[~np.isnan(arr)]

    # ---- HARD EXIT if no valid data ----
    if arr.size == 0:
        return {
            "mean": np.nan,
            "std": np.nan,
            "q05": np.nan,
            "q25": np.nan,
            "q50": np.nan,
            "q75": np.nan,
            "q95": np.nan,
            "coefficient_of_variation": np.nan
        }

    return {
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "q05": round(float(np.percentile(arr, 5)), 2),
        "q25": round(float(np.percentile(arr, 25)), 2),
        "q50": round(float(np.percentile(arr, 50)), 2),
        "q75": round(float(np.percentile(arr, 75)), 2),
        "q95": round(float(np.percentile(arr, 95)), 2),
        "coefficient_of_variation": round(np.std(arr)/np.mean(arr),2)
    }

#%%
# ===================== INPUTS =====================

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"
path_polygons = local_folder + "data/Polygons"

path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\dNBR"

# complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# polygons to consider
polygons = patches.polygon.unique()

print(len(polygons))

# Load the polygon shape.
#polygon_id = "V-022"


results = []
for polygon_id in polygons: 
    polygon_id = polygon_id.strip()
    print(polygon_id)
    
    # load polygon shape: 
    polygon_folder = path_polygons + f"/{polygon_id}.gpkg" 
    
    polygon_folder_path = Path(polygon_folder)
    # in case the file does not exist we want to skip! 
    if not polygon_folder_path.exists():
        print(f"File not found, skipping: {polygon_folder}")
        continue
    
    # read polygon 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:2154")
      
    # dnbr file 
    path_name = f"C:/Users/steff/Documents/06-Internshi_Paris/00_Mai/NBR_Lilian/fires_dNBR-20260515T091959Z-3-001/fires_dNBR/{polygon_id}_dnbr.tif"
      
    # Read dnbr 
    with rasterio.open(path_name) as ds:
        dnbr = ds.read(1)
    
        transform_dnbr = ds.transform
        crs_nbr = ds.crs
        width = ds.width
        height = ds.height
    
    # clip this to the shape of the polygon! 
    gdf_polygon = gdf_polygon.to_crs(crs_nbr)  # or height CRS if different
    
    mask_polygon = geometry_mask(
        [geom for geom in gdf_polygon.geometry],
        transform=transform_dnbr,
        invert=True,
        out_shape= dnbr.shape
    )
    
    dnbr_polygon = np.where(mask_polygon, dnbr, np.nan)
    
    # now plot the dnbr 
    plt.figure(figsize=(8, 8))
    plt.imshow(dnbr_polygon)
    plt.colorbar(label="dnbr")
    plt.title(f"dnbr for {polygon_id} ")
    plt.show()
    
    # ========== Load the patches file. ==================== 
    
    # adjust the patches raster to the raster of the dnbr 
    # get the format we fit the patches against
    first_transform = transform_dnbr
    height_shape = dnbr.shape
    
    # adjust patches to crs
    patches = patches.to_crs(crs_nbr)
    
    # now load the patches for that area: 
    patches_polygon = patches[patches.polygon == polygon_id]
    patches_polygon = patches_polygon.reset_index()
    
    # now create to raster file: 1 with the the patches, 2 with the tree species 
    # Band 1: index
    shapes_index = [
        (geom, idx)
        for geom, idx in zip(
            patches_polygon.geometry,
            patches_polygon.index
        )
    ]
    
    # Band 2: TFV_num
    shapes_tfv = [
        (geom, tfv)
        for geom, tfv in zip(
            patches_polygon.geometry,
            patches_polygon.TFV_num
        )
    ]
    
    # create two rasters 
    # raster index 
    raster_index = rasterize(
        shapes_index,
        out_shape=height_shape,
        transform=first_transform,
        fill=-1,
        dtype="int32"
    )
    
    # raster TFV_num 
    raster_tfv = rasterize(
        shapes_tfv,
        out_shape=height_shape,
        transform=first_transform,
        fill=-1,
        dtype="int32"
    )  
    
    plt.figure(figsize=(8, 8))
    plt.imshow(raster_index)
    plt.colorbar(label="tfv")
    plt.title(f"tfv for {polygon_id} ")
    plt.show()
    
    
    # ============= Iterate over the patches and compute stats values of dnbr values within! =================== 
    
    
    # loop over the patches and load the dnbr values within: (DO WE NEED MASKS?)
    
    
    for index in np.unique(raster_index): # go through all the patches
        if index == -1: 
            continue
        mask_index = raster_index == index 
        dnbr_stats = np.where(mask_index, dnbr_polygon, np.nan)
        #dnbr_stats = dnbr_polygon[mask_index]
        row = patches_polygon[patches_polygon.index == index].iloc[0]
        patch_id = row["patch_id"]
        
        #check 
        '''
        # Plot
        fig, ax = plt.subplots(figsize=(8, 6))
    
        im = ax.imshow(dnbr_stats, cmap="viridis", vmin = -100, vmax = 250)
    
        ax.set_title("dnrb_patch")
        
        plt.show()
        '''
        #check 
        # print to verify we are doing the right thing! 
        
        # get the tfv forest type for the pach (only one species per patch)
        tfv_num = np.unique(raster_tfv[mask_index])[0]
        
        # compute the stats values for the ones inside the patches. 
        pre_stats = summary_stats(dnbr_stats)
    
        results.append({
            'polygon': polygon_id,
            "patch_index": index,
            "patch_id": patch_id, 
            "tfv_num" : tfv_num,
            **{f"dnbr_{k}": v for k, v in pre_stats.items()},
            })
        
    
df_dnbr = pd.DataFrame(results)  

print(len(df_dnbr))
print(len(patches))

print("Number of dnbr rows:", len(df_dnbr))
print("Number of patches:", len(patches))
print(set(patches.patch_id)- set(df_dnbr.patch_id))

print(df_dnbr["dnbr_mean"].isna().sum())
missing_patch_ids = df_dnbr[df_dnbr["dnbr_mean"].isna()]["patch_id"]
print(missing_patch_ids)

    
#%%
new_path = Path(path_to_save)
csv_filename = "dNBR.csv"
df_dnbr.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

#%% 
# plot distribution of dnbr per tree species 
FOREST_TYPE_LABELS = {
    0.0: 'Just cut',
    1.0: 'Deciduous oak',
    6.0: 'Evergreen oak',
    9.0: 'Beech',
    10.0: 'Chestnut',
    14.0: 'Locust',
    19.0: 'Poplar',
    49.0: 'Other deciduous',
    100.0: 'Mixed deciduous',
    111.0: 'Mixed deciduous in island',
    51.0: 'Maritime pine',
    52.0: 'Scotch pine',
    53.0: 'Austrian pine',
    57.0: 'Aleppo pine',
    58.0: 'Mountain, stone pines',
    80.0: 'Mixed pines',
    81.0: 'Other pines',
    61.0: 'Fir, spruce',
    63.0: 'Larch',
    64.0: 'Douglas',
    90.0: 'Mixed non pine',
    91.0: 'Other non pine',
    200.0: 'Mixed conifers',
    222.0: 'Mixed conifers in island',
    310.0: 'Mainly deciduous',
    320.0: 'Mainly conifers',
    400.0: 'Open just cuts',
    401.0: 'Open deciduous',
    402.0: 'Open conifers',
    403.0: 'Open mixed',
    504.0: 'Moors',
    506.0: 'Shrubland',
}

# Dictionary for the broad forest categories 
BROAD_FOREST_TYPE_LABELS = {-1: 'no_bd_foret', 0.0: 'Other', 1.0: 'Pure deciduous', 6.0: 'Pure deciduous', 9.0: 'Pure deciduous', 10.0: 'Pure deciduous', 14.0: 'Pure deciduous',
19.0: 'Pure deciduous', 49.0: 'Pure deciduous', 100.0: 'Mixed deciduous', 111.0: 'Mixed deciduous', 51.0: 'Pure conifers', 52.0: 'Pure conifers', 53.0: 'Pure conifers', 57.0: 'Pure conifers',
58.0: 'Pure conifers',
81.0: 'Pure conifers', 80.0: 'Mixed conifers',
61.0: 'Pure conifers', 63.0: 'Pure conifers', 64.0: 'Pure conifers',
91.0: 'Pure conifers', 90.0: 'Mixed conifers',
200.0: 'Mixed conifers', 222.0: 'Mixed conifers',
310.0: 'Mixed deciduous', 320.0: 'Mixed conifers', 400.0: 'Other',
401.0: 'Mixed deciduous', 402.0: 'Mixed conifers', 403.0: 'Mixed deciduous', 504.0: 'Other',
506.0: 'Other', 1000: 'Other'}

# use the mean.   
df_dnbr['forest_type'] = df_dnbr['tfv_num'].map(BROAD_FOREST_TYPE_LABELS)

import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))

sns.boxplot(
    data=df_dnbr,
    x="forest_type",
    y="dnbr_q05"
)

plt.xticks(rotation=90)

plt.xlabel("TFV number")
plt.ylabel("dNBR mean")
plt.title("Distribution of mean dNBR per TFV class")

plt.show()    

#%%
polygon_id = "Q-048"
# dnbr file 
path_name = f"C:/Users/steff/Documents/06-Internshi_Paris/00_Mai/NBR_Lilian/fires_dNBR-20260515T091959Z-3-001/fires_dNBR/{polygon_id}_dnbr.tif"
  
# Read dnbr 
with rasterio.open(path_name) as ds:
    dnbr = ds.read(1)

    transform_dnbr = ds.transform
    crs_nbr = ds.crs
    width = ds.width
    height = ds.height
    resolution = ds.res
    print(resolution)

    
#%%
import rasterio
from rasterio.warp import calculate_default_transform

with rasterio.open(path_name) as ds:
    transform, width, height = calculate_default_transform(
        ds.crs,
        "EPSG:2154",
        ds.width,
        ds.height,
        *ds.bounds
    )

    resolution_lambert = (transform.a, abs(transform.e))

    print("Resolution in Lambert-93:", resolution_lambert)
    
    
    
