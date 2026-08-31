# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 09:11:58 2026

@author: steff
"""
import geopandas as gpd 
from pathlib import Path 
import pandas as pd


# The following polygons experience overlapping bd foret categories. To clean we assign in the intersection the one that has the bigger overlap with the fire polygon


problem_polygons = ['V-047', 'Q-281', 'V-001', 'Q-242', 'Q-061', 'Q-105', 'V-052', 'V-036', 'Q-060_C', 'Q-261', 'T-117', 'A-092', 'T-120', 'V-044']

# Instead perform on all the polygons and then check! 

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

# DO IT MYSELF: 
    
    
# STEP 1: LOAD THE BD FORET FOR THE POLYGON: 
# PLOT THE BD FORET 


def load_bd_foret(polygon_bounds):
    """
    Load BD Forêt data intersecting the polygon bounding box.
    """
    #input_file = BASE_DIR / "data" / "BD-forest" / "BD_Foret_France_simp1m.gpkg"
    input_file = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/BD_foret/BD_Foret_France_simp1m.gpkg"
    bd_forest = gpd.read_file(
        input_file,
        bbox=polygon_bounds
    ).to_crs("EPSG:2154")

    bd_forest["TFV_num_label"] = bd_forest["TFV_num"].map(FOREST_TYPE_LABELS)

    return bd_forest


results = []
'''NEW APPROACH'''

for polygon_name in problem_polygons: 
    
    print(polygon_name)
    
    polygon_folder = f"C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/Polygons/{polygon_name}.gpkg" 
    polygon_folder_path = Path(polygon_folder)
    
    #read polygon 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:2154")
    
    # get bounding box of the polygon
    polygon_bounds = gdf_polygon.total_bounds 
    minx, miny, maxx, maxy = gdf_polygon.total_bounds
    
    # load the bd foret for the entire rectangle 
    bd_foret = load_bd_foret((minx, miny, maxx, maxy))
    
    bd = bd_foret.copy()
    bd['area'] = bd.geometry.area 
    
    sindex = bd.sindex
    
    bd.plot(column = "TFV_num", cmap = "tab20", alpha = 0.5)
    polygon_bd_before = gpd.clip(bd, gdf_polygon)
    polygon_bd_before.plot(column = "TFV_num", cmap = "tab20", alpha = 0.5)
    
    # find the overlapping pairs: 
        
    overlaps = []
    
    for i,  geom1 in bd.geometry.items(): 
        possible_matches_index = list(sindex.intersection(geom1.bounds))
        
        for j in possible_matches_index: 
            if j<= i:
                continue
            
            geom2 = bd.geometry.iloc[j]
            
            if not geom1.intersects(geom2): 
                continue
            
            inter = geom1.intersection(geom2)
            
            if inter.is_empty or inter.area < 20: 
                continue 
            
            overlaps.append((i,j,inter))
            
    # now assign the overlap to the larger area only: 
    geom_update = bd.geometry.copy()
    
    for i, j, inter in overlaps: 
        area_i = geom_update[i].area 
        area_j = geom_update[j].area 
        
        if area_i >= area_j:
            # remove overlap from j 
            geom_update[j] = geom_update[j].difference(inter)
        else: 
            geom_update[i] = geom_update[i].difference(inter)
    
    bd_clean = bd.copy()
    bd_clean["geometry"] = geom_update
    
    bd_clean = bd_clean[~bd_clean.geometry.is_empty]
    bd_clean = bd_clean.set_geometry("geometry")
    
    # plot to check what happens 
    bd_clean.plot(column = "TFV_num", cmap = "tab20", alpha = 0.5)
    
    polygon_bd = gpd.clip(bd_clean, gdf_polygon)
    polygon_bd.plot(column = "TFV_num", cmap = "tab20", alpha = 0.5)
        
    
    results.append(bd_clean)

#%%
final_gdf = gpd.GeoDataFrame(
    pd.concat(results, ignore_index=True),
    crs=results[0].crs
)

final_gdf.to_file(
    r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\clean_bd_foret_overlapping.gpkg",
    layer="clean_bd_foret",
    driver="GPKG"
)


