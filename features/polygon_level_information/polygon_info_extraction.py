# -*- coding: utf-8 -*-
"""
Created on Tue May 19 17:39:58 2026

@author: steff
"""

# extract information on the polygon level: 
'''
area of polygon 
l’origine de l’incendie 
frequency of fire in area 
code insee 
departement 
(these are all things we can extract on polygon level from the polygon info file) 
'''

'''
sylvoecoregion 
greco
(SER files) 
'''

import pandas as pd 
import geopandas as gpd 
import re
from pathlib import Path
import numpy as np 
from matplotlib import pyplot as plt

# ==================FILE STRUCTURE============================
# file structure
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"
path_polygons = local_folder + "data/Polygons"
path_polygon_info = local_folder + "data/Polygon_info.csv"

# file with the shapes of the SER regions: 
filepath = "C:/Users/steff/Documents/06-Internshi_Paris/0_height_loss_area/data/France_ser/France_ser.shp"

# ============================================================


# get the file with the general polygon information 
polygon_info = pd.read_csv(path_polygon_info, encoding="cp1252", sep=";")
polygon_info["annee"] = pd.to_numeric(polygon_info["annee"], errors="coerce")
polygon_info = polygon_info[(polygon_info.annee > 2014) & (polygon_info.annee < 2023)]
polygon_info = polygon_info[polygon_info["Polygon_ID"].notna()]


# create a dataframe filtering for the relevant information 
polygon_info = polygon_info[['Polygon_ID', 'annee', 'departement', 'code_insee', 'nature', 'Polygon_area_ha']]
polygon_info.Polygon_ID = polygon_info.Polygon_ID.str.strip()

# get the greco and the sylvoregion 
print(len(polygon_info))

# get the SER for the polygons

polygons = polygon_info.Polygon_ID.unique()


results = []

# get the sylvoecoregion and the area of the polygons. 

for polygon in polygons: 
    polygon = polygon.strip()
    if (polygon == "T-124"):
        print('ITS HERE!')
    
    polygon_path = Path(path_polygons + f"/{polygon}.gpkg")
    
    if not polygon_path.exists():
        print(f"File not found, skipping: {polygon}")
        continue
    
    # load polygon 
    gdf_polygon = gpd.read_file(polygon_path, encoding="cp1252").to_crs("EPSG: 2154")
    
    area = np.round(gdf_polygon.geometry.area.values[0] / 10000,3) # convert m^2 to ha
    
    if (polygon == "T-124"):
        print('ITS HERE!')
        gdf_polygon.plot()
        plt.show()
    '''
    gdf_polygon.plot()
    plt.show()
    '''
    # load ser map 
    df_ser = gpd.read_file(filepath).to_crs("EPSG: 2154")
    
    '''
    df_ser.plot()
    plt.show()
    '''
    # ---- SPATIAL JOIN: find SERs intersecting the polygon ----
    candidates = gpd.sjoin(
        gdf_polygon,
        df_ser,
        how="inner",
        predicate="intersects"
    )
    
    '''
    candidates.plot()
    plt.show()
    '''
    # Geometry of the matching SERs (handles multiple overlaps)
    ser_geoms = df_ser.loc[candidates.index_right].geometry
    ser_geoms.index = candidates.index
    
    # Number of SERs overlapping the polygon
    num_ser_overlap = len(candidates)
    
    # Compute intersection areas
    candidates["intersection_area"] = (
        candidates.geometry
        .intersection(ser_geoms)
        .area
    )
    
    # ---- SELECT THE SER WITH MAXIMAL INTERSECTING AREA ----
    sylvoecoregion = candidates.loc[
        candidates["intersection_area"].idxmax(),
        "codeser"
    ]
    
    if isinstance(sylvoecoregion, pd.Series):
        sylvoecoregion = sylvoecoregion.tolist()
    
    print(sylvoecoregion)
    
    results.append({
        "Polygon_ID": polygon,
        "sylvoecoregion": sylvoecoregion, 
        "area": area})
    

# save data frame with polygon name and the corresponding sylvoecoregion
polygon_ser = pd.DataFrame(results)


# ===========================
# 2. DEFINE GRECO REGION DICTIONARY
# ===========================
greco_dict = {
    "A": "Grand Ouest cristallin et océanique",
    "B": "Centre Nord semi-océanique",
    "C": "Grand Est semi-continental",
    "D": "Vosges",
    "E": "Jura",
    "F": "Sud-Ouest océanique",
    "G": "Massif Central",
    "H": "Alpes",
    "J": "Méditerranée",
    "I": "Pyrénées",
    "K": "Corse"
}


# extract first letter from sylvioregion 
def extract_first_letter(value):
    text = str(value)
    matches = re.findall(r'[A-Z]\d+', text)
    if matches:
        return matches[0][0]   # first letter of code
    return None

polygon_ser['sylvo_letter'] = polygon_ser['sylvoecoregion'].apply(extract_first_letter)

# Map to GRECO regions
polygon_ser["greco_name"] = polygon_ser["sylvo_letter"].map(greco_dict)

# Merge the datasets 
df_final = pd.merge(polygon_info, polygon_ser, on  = 'Polygon_ID')

# path to save 
save_path = "C:/Users/steff/Documents/06-Internshi_Paris/00_Mai/Polygon_info_data"
# save the merged dataset as csv file! 
df_final.to_csv(save_path + "/polygon_level_info.csv", index=False, encoding="utf-8-sig", sep = ';', decimal = ",")

#%%
# check for completeness: 
print(len(df_final))

polygons1 = polygon_info.Polygon_ID.unique()
polygons2 = df_final.Polygon_ID.unique()
print(polygons1)
print(len(polygons1))
print(polygons2)
print(len(polygons2))
print(list(set(polygons1)- set(polygons2)))