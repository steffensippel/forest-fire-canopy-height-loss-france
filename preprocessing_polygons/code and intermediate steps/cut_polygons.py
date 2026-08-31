# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 12:52:12 2026

@author: steff
"""
# we want to split the bd foret parcels in equal sized 1 ha patches 
# IMPORT PACKAGES

import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import pandas as pd
import math
from pathlib import Path

bd_foret_file = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/BD_foret/BD_Foret_France_simp1m.gpkg"
bd_foret_overlapping_file = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\clean_bd_foret_overlapping.gpkg"

#%% Get the individual BD Foret shapes inside the polygon: 

# =============================================================================
# DATA 1  – BD FORÊT (LOADED ONCE)
# =============================================================================

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

def load_bd_foret(polygon_bounds):
    """
    Load BD Forêt data intersecting the polygon bounding box.
    """
    #input_file = BASE_DIR / "data" / "BD-forest" / "BD_Foret_France_simp1m.gpkg"
    input_file = bd_foret_overlapping_file 
    bd_forest = gpd.read_file(
        input_file,
        bbox=polygon_bounds
    ).to_crs("EPSG:2154")

    bd_forest["TFV_num_label"] = bd_forest["TFV_num"].map(FOREST_TYPE_LABELS)

    return bd_forest
   
#%%
# Step 1: get points that are equally distributed within the area. (just use random points)

#===========SAMPLING POINTS====================

# sample random points within polygon shape. Number of points: number of 1ha areas that fit within!   
def sample_points_uniform(geom, n_points):
    minx, miny, maxx, maxy = geom.bounds
    points = []
    
    while len(points) < n_points:
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        p = Point(x, y)
        
        if geom.contains(p):
            points.append(p)
    
    return points

def sample_points_evenly_on_boundary(boundary, n_points):
    length = boundary.length
    distances = np.linspace(0, length, n_points, endpoint=False)
    return [boundary.interpolate(d) for d in distances]

#%%
'''
# =========================WHAT POLYGONS TO CUT====================================
filename = "C:/Users/steff/Documents/06-Internshi_Paris/Polygon Data/Polygon_info.csv"
polygon_file = pd.read_csv(filename, sep = ";", encoding = "latin1")

polygon_file["annee"] = pd.to_numeric(
    polygon_file["annee"],
    errors="coerce"
)

# only look at fires in 2015 to 2022
polygon_file = polygon_file[(polygon_file.annee>2014) & (polygon_file.annee < 2023)]
polygons = polygon_file[polygon_file["Polygon_ID"].notna()].Polygon_ID.values
print(len(polygons))

# process them in four steps 
print(len(polygons)/4) 
polygons1 = polygons[0:82]
polygons2 = polygons[82:164]
polygons3 = polygons[164:246]
polygons4 = polygons[246:328]
polygons_problems = ['V-001']

print(len(polygons1) + len(polygons2) + len(polygons3) + len(polygons4))
'''
#%%
# ==================ITERATIVE ALGORITHM OF CUTTING THE POLYGON PATCHES===============
'''RUN FOR THE PROBLEMATIC POLYGONS'''
polygons_problems = ['V-047', 'Q-281', 'V-001', 'Q-242', 'Q-061', 'Q-105', 'V-052', 'V-036', 'Q-060_C', 'Q-261', 'T-117', 'A-092', 'T-120', 'V-044']

areas = []
all_voronoi = []

# 1) POLYGON LEVEL 
# load the polygon shape
for k, polygon_name in enumerate(polygons_problems):
    polygon_name = polygon_name.strip()
    print(polygon_name, k)
    polygon_folder = f"C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/Polygons/{polygon_name}.gpkg" 
    
    polygon_folder_path = Path(polygon_folder)
    # in case the file does not exist we want to skip! 
    if not polygon_folder_path.exists():
        print(f"File not found, skipping: {polygon_name}")
        continue
    
    #read polygon 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:2154")
    
    # get bounding box of the polygon
    polygon_bounds = gdf_polygon.total_bounds 
    minx, miny, maxx, maxy = gdf_polygon.total_bounds
    
    # get the area of the polygon 
    area = gdf_polygon.geometry.area /10000
    
    # load the bd foret for the entire rectangle 
    bd_foret = load_bd_foret((minx, miny, maxx, maxy))
    
    # clip the bd_foret to the shape of the polygon 
    bd_foret = gpd.clip(bd_foret, gdf_polygon)
    
    '''THE RESHAPING WILL CREATE VERY THIN AND SMALL FRAGMENTS... REMOVE THEM ALREADY BEFORE!!!- it still crashes here!'''
    '''BUT THIS IS NOT THE ACTUAL PROBLEM!!!'''
    
    # load the multipolygons as single polygons
    bd_foret = bd_foret.explode(index_parts=True).reset_index(drop=True)
    
    # after exploding remove the very small fragments that might have occurred during the cleaning of the bd foret set! 
    bd_foret = bd_foret[bd_foret.area > 10]
    
    # one problem has problems with duplicates

    bd_foret["wkt"] = bd_foret.geometry.to_wkt()

    bd_foret = (
        bd_foret
        .drop_duplicates(subset="wkt")
        .drop(columns="wkt")
    )

    
    # 2: BD FORET TREE SPECIES WITHIN POLYGON LEVEL
    # ==========SAMPLE POINTS WITHIN THE BD FORET PARCEL===========================
    for j in range(len(bd_foret)): 
        # 1. get the geometry of the bd foret parcel
        geom = bd_foret.iloc[j].geometry
        forest_type = bd_foret.iloc[j].TFV_num_label
        TFV_num = bd_foret.iloc[j].TFV_num
        area_geom = geom.area / 10000

    
        # 2. Sample inside points
      
        target_area = 10000  # 1 ha in m²
        
        # number of points : how many 1ha areas fit in the shape 
        n_points = math.ceil(geom.area/ target_area)
        #print(n_points)
        
        # make sure at least 1 
        if n_points == 0: 
            n_points = 1

        points_inside = sample_points_uniform(geom, n_points)
        
        # In the following we ensure that the voronoi areas within the polygon are bounded and no infinite area 
        # 3. Buffer
        buffered = geom.buffer(1000)
        
        # 4. Boundary
        boundary = buffered.boundary
        
        # 5. Sample evenly on boundary 
        
        points_outside = sample_points_evenly_on_boundary(boundary, 20)
        
        # 6. Combine points
        points = points_inside + points_outside
        
        # 7. Convert ONCE to GeoDataFrame
        gdf_points = gpd.GeoDataFrame(geometry=points, crs=bd_foret.crs)
        
        # 8. Plot everything cleanly
        '''
        ax = gpd.GeoSeries([geom]).plot()
        plt.show()
        gpd.GeoSeries([buffered]).plot()
        plt.show()
        gdf_points.plot()
        plt.show()
        '''
        # ===========MAKE READY TO CREATE THE VORONOI DIAGRAM=========================
        # Punkte als numpy array darstellen: 
        coords = np.array([[p.x, p.y] for p in points])
        vor = Voronoi(coords)
        
        # ============================================================
        # Iterative Voronoi refinement to obtain more equal partitions
        # ============================================================
        if n_points >1: 
            '''ADD: IF SMALLER THAN CERTAIN AREA DO NOT COMPUTE THE REFINEMENT: JUST CONTINUTE, HERE BE CAREFUL WE STILL WANT TO ADD THEM TO OUR DATAFRAME'''
            for i in range(30): 
                # --------------------------------------------------------
                # Step 1: Convert point geometries to NumPy coordinates
                # (required for scipy.spatial.Voronoi)
                # --------------------------------------------------------
                coords = np.array([[p.x, p.y] for p in points])
                vor = Voronoi(coords)
                
                # --------------------------------------------------------
                # Step 2: Construct finite Voronoi regions as polygons
                # --------------------------------------------------------
                regions = []
                
                for region_index in vor.point_region:
                    region = vor.regions[region_index]
                    
                    # Skip infinite or empty regions
                    if -1 in region or len(region) == 0:
                        continue
                    
                    polygon = Polygon([vor.vertices[i] for i in region])
                    regions.append(polygon)
                
                # --------------------------------------------------------
                # Step 3: Clip Voronoi regions to the original geometry
                # (ensures all polygons lie within the target area)
                # --------------------------------------------------------
                clipped_regions = [poly.intersection(geom) for poly in regions]
                
                vor_gdf = gpd.GeoDataFrame(
                    geometry=clipped_regions, 
                    crs=gdf_polygon.crs
                )
                
            
                # --------------------------------------------------------
                # Step 4: Plot Voronoi tessellation with current points
                # --------------------------------------------------------
                '''
                fig, ax = plt.subplots(figsize=(6, 6))
            
                vor_gdf.plot(ax=ax, edgecolor="black", facecolor="none")
                gdf_points.plot(ax=ax, color="red", markersize=10)
            
                plt.show()
                '''
                # --------------------------------------------------------
                # Step 5: Update points using centroids of regions
                # (Lloyd's algorithm for more uniform partitioning)
                # --------------------------------------------------------
                
                points = [
                    poly.centroid 
                    for poly in clipped_regions 
                    if not poly.is_empty
                ]
                
                # Add fixed outer boundary points (to stabilize edges) (avoid infinite vonoroi areas)
                points.extend(points_outside)
                
                # --------------------------------------------------------
                # Step 6: Convert updated points to GeoDataFrame
                # --------------------------------------------------------
                gdf_points = gpd.GeoDataFrame(
                    geometry=points, 
                    crs=gdf_polygon.crs
                )
                
                #--------------------------------------------------------
                # Step 7: Plot updated point configuration
                # -------------------------------------------------------
                '''
                fig, ax = plt.subplots(figsize=(6, 6))
                gdf_points.plot(ax=ax, color="red", markersize=10)
                
                plt.show()
                '''
                '''new try below'''
        else: 
            regions = []
            
            
            for region_index in vor.point_region:
                region = vor.regions[region_index]
                
                # Skip infinite or empty regions
                if -1 in region or len(region) == 0:
                    continue
                
                polygon = Polygon([vor.vertices[i] for i in region])
                regions.append(polygon)
            
            # --------------------------------------------------------
            # Step 3: Clip Voronoi regions to the original geometry
            # (ensures all polygons lie within the target area)
            # --------------------------------------------------------
            clipped_regions = [poly.intersection(geom) for poly in regions]
            
            vor_gdf = gpd.GeoDataFrame(
                geometry=clipped_regions, 
                crs=gdf_polygon.crs
            )
        '''new try'''
        
        # AFTER iteration add the polygons to the data structure
        # ----------- ADD TO DATAFRAME STRUCTURE -----------------------------
        vor_gdf["parent_id"] = bd_foret.index[j] 
        vor_gdf["polygon"] = polygon_name
        vor_gdf['TFV_num'] = TFV_num
        vor_gdf['forest_typ'] = forest_type
        #vor_gdf["area"] = vor_gdf.geometry.area
        all_voronoi.append(vor_gdf)
        
        # For the final visualization remove the outside points!  
        gdf_points_inside = gpd.GeoDataFrame(
            geometry=[p for p in points if p not in points_outside],
            crs=gdf_polygon.crs
        )

        '''
        fig, ax = plt.subplots(figsize=(6, 6))
        
        vor_gdf.plot(ax=ax, edgecolor="black", facecolor="none")
        gdf_points_inside.plot(ax=ax, color="red", markersize=10)
        #plt.title(f"{j}, {tuple(int(x) for x in bd_foret.index[j])}")
        
        plt.show()
        '''



        
print('end')
# ----------- SAVE IN DATAFRAME STRUCTURE ----------------------
gdf_all = gpd.GeoDataFrame(
    pd.concat(all_voronoi, ignore_index=True),
    crs=bd_foret.crs
)

'''
polygons_first_step = gdf_all.polygon.unique()
print(len(polygons_first_step))

polygons_excluded = list(set(polygons1) - set(polygons_first_step))
print(polygons_excluded)
'''

for polygon in polygons_problems: 
    #TRY COMPARISON
    fig, ax = plt.subplots(figsize=(8, 6))
    polygon = gdf_all[gdf_all.polygon == polygon]
    polygon.plot(ax=ax, edgecolor="black", column="forest_typ", cmap="tab20", alpha = 0.5)
    plt.show()

# COMPARISON FOR DISTRIBUTION OF AREAS 
areas = gdf_all.area.values 
plt.boxplot(areas)
plt.show()


plt.hist(areas, bins=30)

plt.xlabel("Area (m²)")
plt.ylabel("Frequency")

plt.xticks()   # force x ticks
plt.yticks()   # force y ticks

plt.show()

# %% Recut the bigger patches (all patches bigger than 15 000 m^2)

all_patches = gdf_all
all_voronoi = []

# load the bigger patches: 
all_patches_big = all_patches[all_patches.area > 15000]

'''
fig, ax = plt.subplots(figsize=(8, 6))

all_patches_big.plot(ax=ax, edgecolor="black", column="forest_typ", cmap="tab20")
plt.show()
'''

#areas_big = all_patches_big.area.values 


# PERFORM THE ALGORITHM AGAIN ON THE REMAINING PATCHES THAT ARE STILL BIGGER THAN 15000 m^2 
# ==========SAMPLE POINTS WITHIN THE BD FORET PARCEL===========================
for j in range(len(all_patches_big)): 

    # 1. get the geometry of the bd foret parcel 
    geom = all_patches_big.iloc[j].geometry
    forest_type = all_patches_big.iloc[j].forest_typ
    TFV_num = all_patches_big.iloc[j].TFV_num
    polygon_name = all_patches_big.iloc[j].polygon
    area_geom = geom.area / 10000
    print(polygon_name, j)
    
    # 2. Sample inside points
    #points_inside = sample_points_uniform_grid2(geom)
    
    target_area = 10000  # 1 ha in m²
    #n_points = int(geom.area / target_area)
    if geom.area < 25000: 
        n_points = 2
    elif geom.area < 35000: 
        n_points = 3 
    else: 
        n_points = 4
   
    points_inside = sample_points_uniform(geom, n_points)
    
    # 3. Buffer
    buffered = geom.buffer(1000)
    
    # 4. Boundary
    boundary = buffered.boundary
    
    # 5. Sample evenly on boundary 
    def sample_points_evenly_on_boundary(boundary, n_points):
        length = boundary.length
        distances = np.linspace(0, length, n_points, endpoint=False)
        return [boundary.interpolate(d) for d in distances]
    
    points_outside = sample_points_evenly_on_boundary(boundary, 20)
    
    # 6. Combine points
    points = points_inside + points_outside
    
    # 7. Convert ONCE to GeoDataFrame
    gdf_points = gpd.GeoDataFrame(geometry=points, crs=bd_foret.crs)
    
    # 8. Plot everything cleanly
    '''
    ax = gpd.GeoSeries([geom]).plot()
    plt.show()
    gpd.GeoSeries([buffered]).plot()
    plt.show()
    gdf_points.plot()
    plt.show()
    '''   
    # ===========MAKE READY TO CREATE THE VORONOI DIAGRAM=========================
    # Punkte als numpy array darstellen: 
    coords = np.array([[p.x, p.y] for p in points])
    vor = Voronoi(coords)
    
    # ============================================================
    # Iterative Voronoi refinement to obtain more equal partitions
    # ============================================================
    
    for i in range(20): 
        # --------------------------------------------------------
        # Step 1: Convert point geometries to NumPy coordinates
        # (required for scipy.spatial.Voronoi)
        # --------------------------------------------------------
        coords = np.array([[p.x, p.y] for p in points])
        vor = Voronoi(coords)
        
        # --------------------------------------------------------
        # Step 2: Construct finite Voronoi regions as polygons
        # --------------------------------------------------------
        regions = []
        
        for region_index in vor.point_region:
            region = vor.regions[region_index]
            
            # Skip infinite or empty regions
            if -1 in region or len(region) == 0:
                continue
            
            polygon = Polygon([vor.vertices[i] for i in region])
            regions.append(polygon)
        
        # --------------------------------------------------------
        # Step 3: Clip Voronoi regions to the original geometry
        # (ensures all polygons lie within the target area)
        # --------------------------------------------------------
        clipped_regions = [poly.intersection(geom) for poly in regions]
        
        vor_gdf = gpd.GeoDataFrame(
            geometry=clipped_regions, 
            crs=gdf_polygon.crs
        )
        
    
        # --------------------------------------------------------
        # Step 4: Plot Voronoi tessellation with current points
        # --------------------------------------------------------
        

        
        # --------------------------------------------------------
        # Step 5: Update points using centroids of regions
        # (Lloyd's algorithm for more uniform partitioning)
        # --------------------------------------------------------
        
        points = [
            poly.centroid 
            for poly in clipped_regions 
            if not poly.is_empty
        ]
        
        # Add fixed outer boundary points (to stabilize edges)
        points.extend(points_outside)
        
        # --------------------------------------------------------
        # Step 6: Convert updated points to GeoDataFrame
        # --------------------------------------------------------
        gdf_points = gpd.GeoDataFrame(
            geometry=points, 
            crs=gdf_polygon.crs
        )
        
        #--------------------------------------------------------
        # Step 7: Plot updated point configuration
        # --------------------------------------------------------
        '''
        fig, ax = plt.subplots(figsize=(6, 6))
        gdf_points.plot(ax=ax, color="red", markersize=10)
        
        plt.show()
        '''
    '''
    fig, ax = plt.subplots(figsize=(6, 6))

    vor_gdf.plot(ax=ax, edgecolor="black", facecolor="none")
    gdf_points.plot(ax=ax, color="red", markersize=10)

    plt.show()
    '''
    # AFTER iteration add the polygons to the data structure
    # ----------- ADD TO DATAFRAME STRUCTURE -----------------------------
    vor_gdf["parent_id"] = all_patches_big.index[j] 
    vor_gdf["polygon"] = polygon_name
    vor_gdf['TFV_num'] = TFV_num
    vor_gdf['forest_typ'] = forest_type
    all_voronoi.append(vor_gdf)
    
    
    # For the final visualization remove the outside points!  
    gdf_points_inside = gpd.GeoDataFrame(
        geometry=[p for p in points if p not in points_outside],
        crs=gdf_polygon.crs
    )
    '''
    fig, ax = plt.subplots(figsize=(6, 6))
    
    vor_gdf.plot(ax=ax, edgecolor="black", facecolor="none")
    gdf_points_inside.plot(ax=ax, color="red", markersize=10)
    #plt.title(f"{j}, {tuple(int(x) for x in bd_foret.index[j])}")
    
    plt.show()
    '''
    
# ----------- SAVE IN DATAFRAME STRUCTURE ----------------------
gdf_all_big = gpd.GeoDataFrame(
    pd.concat(all_voronoi, ignore_index=True),
    crs=bd_foret.crs
)

# in gdf_all_big there are only the bigger ones! 

# ==============Replace the big patches with the cut ones! add to a geodatafram structure==========================
all_patches_big_recut = pd.concat([all_patches[all_patches.area<15000], gdf_all_big], ignore_index=True)

polygons_second_step = all_patches_big_recut.polygon.unique()
print(len(polygons_second_step))
# COMPARISON FOR DISTRIBUTION OF AREAS 

areas = all_patches_big_recut.area.values 
plt.boxplot(areas)
plt.show()


plt.hist(areas, bins=30)

plt.xlabel("Area (m²)")
plt.ylabel("Frequency")

plt.xticks()   # force x ticks
plt.yticks()   # force y ticks

plt.show()

#%%
# =============MERGE THE SMALL ONES TO THE CLOSEST ONE OF THE SAME SPECIES THAT I NOT TOO FAR AWAY ==============================
# load all the areas smaller than 3000 m^2 
small_patches = all_patches_big_recut[(all_patches_big_recut.area <= 3000)]

#small_patches.plot(column = 'forest_typ')
#plt.show()

all_patches_big_recut_without_small = all_patches_big_recut[(all_patches_big_recut.area > 3000)]
# now join sjoin_nearest, but only if the forest_type column matches! 

results = []

# process each polygon 
for polygon in small_patches.polygon.unique():
    print(polygon)
    # large candidate patches within polygon 
    main_shape = all_patches_big_recut_without_small[all_patches_big_recut_without_small.polygon == polygon]
    # small patches within polygon that we want to merge 
    small_shape = small_patches[small_patches.polygon == polygon]
    
    # only merge if it is the same forst type 
    for ftype in main_shape.forest_typ.unique():
        small = small_shape[small_shape.forest_typ == ftype]
        large = main_shape[main_shape.forest_typ == ftype] 
        # skip if either group is empty 
        if len(small) == 0 or len(large) == 0:
            continue
        
        # find the nearest large patch for each small patch 
        joined = gpd.sjoin_nearest(small, large, how="left", distance_col="distance") # right keeps the small geometries 
        # store original index of small patch 
        joined["small_idx"] = joined.index
        results.append(joined)

# save all nearest-neighbor relationships  
nearest_neighbor = gpd.GeoDataFrame(pd.concat(results, ignore_index=True))

# only merge the ones that are close to a bigger one of the same species 
nearest_neighbor = nearest_neighbor[nearest_neighbor['distance'] < 100]

# now merge with the set excluding the small ones
final = nearest_neighbor.merge(
    all_patches_big_recut_without_small[['geometry']],
    left_on='index_right',
    right_index=True,
    suffixes=('_small', '_large')
)

# and get the union of the small geometry and its closest neighbor of the same forest type 
final['geometry_union'] = final.apply(
    lambda row: row['geometry_small'].union(row['geometry_large']),
    axis=1
)

# set this as  the new geometry 
final = final.set_geometry('geometry_union')

# if multiple small ones belong to the same big one: 
final['target_id'] = final['index_right']
final = final.dissolve(by='target_id')

# merge back to orginal dataframe 
small_used_idx = final["small_idx"]
large_used_idx = final["index_right"]

# remove the rows, where we now want the merged (union of small and big!)
remaining = all_patches_big_recut.drop(index=small_used_idx, errors="ignore")
remaining = remaining.drop(index=large_used_idx, errors="ignore")

# clean the merged and only keep the columns we want
print(all_patches_big_recut.columns)
final = final.rename(columns={
    "forest_typ_left": "forest_typ", 
    "TFV_num_left": "TFV_num", 
    "polygon_left": "polygon", 
    "parent_id_left": "parent_id", 
    "geometry_union": "geometry"
})

# only keep relevant rows 
final = final[["parent_id", "polygon", "TFV_num", "forest_typ", "geometry"]]  
final = final.set_geometry('geometry')
print(final)

final['area'] = final.geometry.area

# now concatenate the removed ones with the merged ones 
final_dataset = gpd.GeoDataFrame(
    pd.concat([remaining, final], ignore_index=True),
    crs=all_patches_big_recut.crs
)

polygons_third_step = final_dataset.polygon.unique()
print(len(polygons_third_step))
# now exclude the small ones again 
final_dataset = final_dataset[final_dataset.area > 3000]

polygon_fourth_step = final_dataset.polygon.unique()
print(len(polygon_fourth_step))
polygons_excluded = list(set(polygons_third_step) - set(polygon_fourth_step))
print(polygons_excluded)
# COMPARISON FOR DISTRIBUTION OF AREAS 

areas = final_dataset.area.values 
plt.boxplot(areas)
plt.show()


plt.hist(areas, bins=30)

plt.xlabel("Area (m²)")
plt.ylabel("Frequency")

plt.xticks()   # force x ticks
plt.yticks()   # force y ticks

plt.show()

for polygon in polygons_problems: 
    #TRY COMPARISON
    fig, ax = plt.subplots(figsize=(8, 6))
    polygon_plot = final_dataset[final_dataset.polygon == polygon]
    polygon_plot.plot(ax=ax, edgecolor="black", column="forest_typ", cmap="tab20", alpha = 0.5)
    plt.show()


#%%
#SAVING FILE 
# save as csv file 

save_path = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\clean BD foret\ overlapping_polygons_cut.gpkg"
final_dataset.to_file(save_path, driver="GPKG")   

#%%

'''
polygon = final_dataset[final_dataset.polygon == "Q-276"]
polygon.plot(column = "forest_typ")
plt.show()

#%%

polygon = all_patches_big_recut[all_patches_big_recut.polygon == "T-100"]
polygon.plot(column = "forest_typ")
plt.show()


#%%
path1 = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/subdivide polygons/UPDATE_processed_patches/patches1.gpkg" 
path2 = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/subdivide polygons/UPDATE_processed_patches/patches2.gpkg"
path3 = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/subdivide polygons/UPDATE_processed_patches/patches3.gpkg"
path4 = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/subdivide polygons/UPDATE_processed_patches/patches4.gpkg"

patches1 = gpd.read_file(path1)
patches2 = gpd.read_file(path2)
patches3 = gpd.read_file(path3)
patches4 = gpd.read_file(path4)

print(len(patches1.polygon.unique()))
print(len(patches2.polygon.unique()))
print(len(patches3.polygon.unique()))
print(len(patches4.polygon.unique()))
all_patches = pd.concat([patches1, patches2, patches3, patches4], ignore_index=True)

save_path = "C:/Users/steff/Documents/06-Internshi_Paris/00_April/subdivide polygons/UPDATE_processed_patches"
final_dataset.to_file(save_path + "/all_patches_complete.gpkg", driver="GPKG")  

print(len(all_patches.polygon.unique()))
print(80+82+79+80)

'''


