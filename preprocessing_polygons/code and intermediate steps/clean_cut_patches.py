# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 13:46:36 2026

@author: steff
"""


# Get an overview of the complete files of the cut polygons: 
# we merge the cut patches for all polygons and clean the data by fixing the overlapping patches 


import geopandas as gpd
import pandas as pd    
from matplotlib import pyplot as plt 

new_file_with_id = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\overlapping_polygons_cut_with_id.gpkg"
old_file_with_id = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\UPDATE_processed_patches\patches_shapes.gpkg"

new_patches_with_id = gpd.read_file(new_file_with_id).to_crs('EPSG: 2154')
old_patches_with_id = gpd.read_file(old_file_with_id).to_crs('EPSG: 2154')


# ======================== STEP 1: Merge the initial cut polygons and the ones with overlapping BD foret areas =========================================
# STEP 1: get the polygons that are in new_patches_with_id 
polygons_overlap = new_patches_with_id["polygon"].unique().tolist()
print(polygons_overlap)

print(len(old_patches_with_id.polygon.unique()))
# STEP 2: remove these polygons from old one

old_patches_with_id = old_patches_with_id[~old_patches_with_id.polygon.isin(polygons_overlap)]

print(len(old_patches_with_id.polygon.unique()))


merged_patches = gpd.GeoDataFrame(
    pd.concat(
        [old_patches_with_id, new_patches_with_id],
        ignore_index=True
    ),
    crs=old_patches_with_id.crs
)

print("Merged rows:", len(merged_patches))
print("Unique polygons:", len(merged_patches["polygon"].unique()))

# ===== Get the overlapping patches: ====

THRESHOLD = 20  # m²

overlaps_found = []

for polygon_name, group in merged_patches.groupby("polygon"):

    if len(group) < 2:
        continue

    group = group.reset_index(drop=False)  # preserve original index
    sindex = group.sindex
    
    for i, geom1 in group.geometry.items():

        candidates = sindex.intersection(geom1.bounds)

        for j in candidates:

            if j <= i:
                continue

            geom2 = group.geometry.iloc[j]

            if not geom1.intersects(geom2):
                continue

            inter = geom1.intersection(geom2)

            if inter.is_empty:
                continue

            if inter.area > THRESHOLD:

                overlaps_found.append({
                    "polygon": polygon_name,
                    "idx1": group.iloc[i]["index"],
                    "idx2": group.iloc[j]["index"],
                    "patch_id_1": group.iloc[i]['patch_id'],
                    "patch_id_2": group.iloc[j]['patch_id'],
                    "overlap_area": inter.area,
                    "intersection": inter
                })
                
                
overlaps_df = pd.DataFrame(overlaps_found)

# plot: overlaps_df.overlap_area distribution. 
overlaps = overlaps_df.overlap_area.values
plt.boxplot(overlaps)

print(len(overlaps_df))
# now only consider those with an overlap biggern than 1000 m^2 
overlaps_df = overlaps_df[overlaps_df.overlap_area > 100]
print(len(overlaps_df))

# get the ids of the patches that are part of this
overlap_patch_ids = list(overlaps_df.patch_id_1.unique())
overlap_patch_ids += list(overlaps_df.patch_id_2.unique())

print(overlap_patch_ids)
print(len(overlap_patch_ids))

# get all the rows from merged_patches that have a patch id in overlaps_df!
# ==================== get the overlapping in merged_patches ===================

overlap_patches = merged_patches[merged_patches.patch_id.isin(overlap_patch_ids)]
print(len(overlap_patches))

# loop through the row of overlaps_df. get the patch ids in overlap patches. compute areas. for the smaller area do the difference. then safe back in overlap_patches 
for _, row in overlaps_df.iterrows():
    
    patch_id_1 = row.patch_id_1
    patch_id_2 = row.patch_id_2
    
    # get the overlapping geometries! 
    
    geom1 = overlap_patches.loc[overlap_patches.patch_id == patch_id_1, "geometry"].iloc[0]
    geom2 = overlap_patches.loc[overlap_patches.patch_id == patch_id_2, "geometry"].iloc[0]
    
    area1 = geom1.area
    area2 = geom2.area
    
    inter = overlaps_df[
        (overlaps_df.patch_id_1 == patch_id_1) &
        (overlaps_df.patch_id_2 == patch_id_2)
    ]["intersection"].iloc[0]
    
    
    ''' check plotting '''
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    gpd.GeoSeries([geom1]).plot(ax=ax, alpha=0.5)
    ax.set_title("BEFORE patch1")
    ax.axis("off")
    plt.show()
    
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    gpd.GeoSeries([geom2]).plot(ax=ax, alpha=0.5)
    ax.set_title("BEFORE patch2")
    ax.axis("off")
    plt.show()
    
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    gpd.GeoSeries([inter]).plot(ax=ax, alpha=0.5)
    ax.set_title("INTERSECTION")
    ax.axis("off")
    plt.show()
    '''check plotting'''

    # subtract overlap from smaller polygon
    if area1 >= area2:
        new_geom2 = geom2.difference(inter)
        overlap_patches.loc[overlap_patches.patch_id == patch_id_2, "geometry"] = new_geom2
        updated_geom= new_geom2
    else:
        new_geom1 = geom1.difference(inter)
        overlap_patches.loc[overlap_patches.patch_id == patch_id_1, "geometry"] = new_geom1
        updated_geom = new_geom1
    '''check plotting'''
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    gpd.GeoSeries([updated_geom]).plot(
        ax=ax,
        alpha=0.5
    )
    
    ax.set_title("AFTER 1")
    ax.axis("off")
    plt.show()
    
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    gpd.GeoSeries([geom1 if area1 > area2 else geom2]).plot(
        ax=ax,
        alpha=0.5
    )
    
    ax.set_title("AFTER 2")
    ax.axis("off")
    plt.show()
    '''check plotting'''
        
        
    
# in the end merge back to merged_patches! 

print(len(overlap_patches))

    
# ====== LAST STEP: MERGE BACK TO ORIGINAL DATAFRAME

final_patches = merged_patches[
    ~merged_patches.patch_id.isin(overlap_patches.patch_id.unique())
]

final_patches = pd.concat([final_patches, overlap_patches], ignore_index=True)


print(len(final_patches))
print(len(final_patches.patch_id.unique()))

save_path = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\ all_polygons_cut_overlap_removed_with_id.gpkg"
final_patches.to_file(save_path, driver="GPKG")


#%%
test_polygon = "A-243"
test = final_patches[final_patches.polygon == test_polygon]
test.plot(column = "TFV_num", cmap= "tab20", edgecolor = "black",  alpha = 0.5)
plt.show()

areas = final_patches.area.values

plt.hist(areas, bins=30)
plt.show()