# -*- coding: utf-8 -*-
"""
Created on Wed May 20 16:16:09 2026

@author: steff
for each patch get the ownership and natural parc / reserve classification
"""

#%%

import pandas as pd
import geopandas as gpd
import numpy as np

# ===================== INPUTS =====================

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"

#adjust!!!
path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\ownership_parc_reserve"


path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"
path_patches_shapes =  r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"
#path_ownership = r"C:\Users\steff\Documents\06-Internshi_Paris\00_pipeline\data\Ownership and natural park\foret_publique.shp"
path_ownership = local_folder + "data/Ownership and natural park/foret_publique.shp"
path_natural_parc = local_folder + "data/Ownership and natural park/parc_ou_reserve.shp"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

polygons = patches.polygon.unique()
print(len(polygons))

all_results = []

for polygon_name in polygons:
    print(polygon_name)
    # ===================== LOAD POLYGON =====================
    polygon_file = path_polygons + f"/{polygon_name}.gpkg"
    gdf_polygon = gpd.read_file(polygon_file, encoding = "latin1").to_crs("EPSG:2154")
    crs = gdf_polygon.crs

    # ===================== PATCHES =====================
    patches_polygon = (
        patches[patches.polygon == polygon_name]
        .to_crs(crs)
        .copy()
    )

    patches_polygon["patch_index"] = patches_polygon.index
    patches_polygon["patches_area"] = patches_polygon.area

    # ===================== OWNERSHIP =====================
    df_forest_ownership = gpd.clip(
        gpd.read_file(path_ownership, encoding="utf-8").to_crs(crs),
        gdf_polygon
    )
    
    df_parc_ou_reserve = gpd.clip(
        gpd.read_file(path_natural_parc, encoding="utf-8").to_crs(crs),
        gdf_polygon
    )

    ownership_per_patch = gpd.overlay(
        patches_polygon,
        df_forest_ownership,
        how="intersection"
    )
    
    parc_ou_reserve_per_patch = gpd.overlay(
        patches_polygon,
        df_parc_ou_reserve,
        how="intersection"
    )
    
    if len(ownership_per_patch) == 0:
        # no overlap at all → all private
        tmp = patches_polygon[["patch_index"]].copy()
        tmp["relative_public"] = 0
        tmp["ownership_broad"] = "private"
        tmp["ownership_specific"] = "private"
        tmp["regional_ownership"] = "private"
        #all_results.append(tmp)
        summary_ownership = tmp
    else: 
        # ---- CLASSIFY THE OWNERSHIP TYPE ------
        ownership_per_patch["intersection_area"] = ownership_per_patch.area

        ownership_per_patch["relative_public"] = (
            round(ownership_per_patch["intersection_area"]
            / ownership_per_patch["patches_area"],4)
        )

        # keep best row per patch (NO ORDER CHANGE method)
        ownership_per_patch = ownership_per_patch[
            ownership_per_patch["relative_public"].eq(
                ownership_per_patch.groupby("patch_index")["relative_public"].transform("max")
            )
        ]

        # classification
        ownership_per_patch["ownership_broad"] = np.where(
            ownership_per_patch["relative_public"] >= 0.5,
            "public",
            "private"
        )

        ownership_per_patch["ownership_specific"] = np.where(
            ownership_per_patch["ownership_broad"] == "public",
            ownership_per_patch["NATURE"],
            "private"
        )

        ownership_per_patch["regional_ownership"] = np.where(
            ownership_per_patch["ownership_broad"] == "public",
            ownership_per_patch["TOPONYME"],
            "private"
        )
        
        # final selection
        ownership_summary = ownership_per_patch[
            [
                "patch_index",
                "relative_public",
                "ownership_broad",
                "ownership_specific",
                "regional_ownership",
            ]
        ].copy()
    
    
    if len(parc_ou_reserve_per_patch) == 0:
        # no overlap at all → all private
        tmp2 = patches_polygon[["patch_index"]].copy()
        tmp2["relative_parc_reserve"] = 0
        tmp2["parc_reserve_broad"] = "no_parc_reserve"
        tmp2["parc_reserve_specific"] = "no_parc_reserve"
        tmp2["regional_parc_reserve"] = "no_parc_reserve"
        tmp2["polygon"] = polygon_name
        #all_results.append(tmp2)
        summary_parc_ou_reserve = tmp2 
        
    else: 
    
        # ---- CLASSIFY THE PARC RESERVE TYPE -----
        parc_ou_reserve_per_patch["intersection_area"] = parc_ou_reserve_per_patch.area
    
        parc_ou_reserve_per_patch["relative_parc_reserve"] = (
            round(parc_ou_reserve_per_patch["intersection_area"]
            / parc_ou_reserve_per_patch["patches_area"], 2)
        )
    
        # keep best row per patch (NO ORDER CHANGE method)
        parc_ou_reserve_per_patch = parc_ou_reserve_per_patch[
            parc_ou_reserve_per_patch["relative_parc_reserve"].eq(
                parc_ou_reserve_per_patch.groupby("patch_index")["relative_parc_reserve"].transform("max")
            )
        ]
    
        # classification
        parc_ou_reserve_per_patch["parc_ou_reserve_broad"] = np.where(
            parc_ou_reserve_per_patch["relative_parc_reserve"] >= 0.5,
            "parc_reserve",
            "no_parc_reserve"
        )
    
        parc_ou_reserve_per_patch["parc_reserve_specific"] = np.where(
            parc_ou_reserve_per_patch["parc_ou_reserve_broad"] == "parc_reserve",
            parc_ou_reserve_per_patch["NATURE"],
            "no_parc_reserve"
        )
    
        parc_ou_reserve_per_patch["regional_parc_reserve"] = np.where(
            parc_ou_reserve_per_patch["parc_ou_reserve_broad"] == "parc_reserve",
            parc_ou_reserve_per_patch["TOPONYME"],
            "no_parc_reserve"
        )
        
        parc_ou_reserve_summary = parc_ou_reserve_per_patch[
            [
                "patch_index",
                "relative_parc_reserve",
                "parc_ou_reserve_broad",
                "parc_reserve_specific",
                "regional_parc_reserve",
            ]
        ].copy()
    
        
    # now merge the two processed     
    summary = ownership_summary.merge(
        parc_ou_reserve_summary,
        on="patch_index",
        how="outer"   
    )
    
    # now get the rows that do not have intersections with either 
    summary = patches_polygon[["patch_index", "patch_id"]].merge(
        summary,
        on="patch_index",
        how="left"
    )
    
    summary["polygon"] = polygon_name
    
    
    # Ownership defaults
    summary["relative_public"] = summary["relative_public"].fillna(0)
    summary["ownership_broad"] = summary["ownership_broad"].fillna("private")
    summary["ownership_specific"] = summary["ownership_specific"].fillna("private")
    summary["regional_ownership"] = summary["regional_ownership"].fillna("private")
    
    # Reserve defaults
    summary["relative_parc_reserve"] = summary["relative_parc_reserve"].fillna(0)
    summary["parc_ou_reserve_broad"] = summary["parc_ou_reserve_broad"].fillna("no_parc_reserve")
    summary["parc_reserve_specific"] = summary["parc_reserve_specific"].fillna("no_parc_reserve")
    summary["regional_parc_reserve"] = summary["regional_parc_reserve"].fillna("no_parc_reserve")
        

    all_results.append(summary)

# ===================== FINAL DATAFRAME =====================
ownership_parc_reserve_df = pd.concat(all_results, ignore_index=True)

# try removing duplicate lines!!! 
ownership_parc_reserve_final_df = ownership_parc_reserve_df.drop_duplicates()

print(len(ownership_parc_reserve_final_df))
print(len(patches))
print(set(patches.patch_id)- set(ownership_parc_reserve_final_df.patch_id))


#%%
#SAVING FILE 
csv_filename = "ownership_parc_reserve.csv"
path = path_to_save + f"/{csv_filename}"
ownership_parc_reserve_df.to_csv(path, index=False, sep=";", float_format="%.3f", decimal=".", encoding='utf-8-sig')

