# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 09:03:07 2026

@author: steff
"""

# CREATE UNIQUE IDENTIFIER FOR THE PATCHES: Name of poylgon_ number of row of that polygon! 
import geopandas as gpd 

#path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\UPDATE_processed_patches\all_patches_complete.gpkg"
path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\ overlapping_polygons_cut.gpkg"

# now load the patches: 
input_file = path_patches_shapes
patches = gpd.read_file(input_file)


# Create row number within each polygon
patches["patch_number"] = patches.groupby("polygon").cumcount()

# Create unique identifier
patches["patch_id"] = (
    patches["polygon"].astype(str)
    + "_"
    + patches["patch_number"].astype(str)
)

#output_file = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\UPDATE_processed_patches\all_patches_complete_with_ids.gpkg"
#output_problematic = r"C:\Users\steff\Documents\06-Internshi_Paris\00_April\subdivide polygons\V-001_cut\patches_V-001_with_id.gpkg"

output = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\overlapping_polygons_cut_with_id.gpkg"

patches.to_file(
    output,
    driver="GPKG"
)

