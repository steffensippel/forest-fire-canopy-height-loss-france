# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 11:54:30 2026

@author: steff
for each patch compute the distance to the edge of the polygon
"""

import pandas as pd 
import geopandas as gpd
import rasterio
from pathlib import Path 
from matplotlib import pyplot as plt 
from rasterio.features import rasterize, geometry_mask
import numpy as np 
from shapely.ops import nearest_points
from shapely.geometry import Polygon, MultiPolygon, MultiLineString
# ===================== INPUTS =====================

'''STRUCTURE OF FILES'''
local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"
path_polygons = local_folder + "data/Polygons"

path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\distance_to_edge"

# complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)
print(patches.columns)

# polygons to consider
polygons = patches.polygon.unique()

print(len(polygons))

#%%

results = []

for polygon in polygons:

    polygon_folder = path_polygons + f"/{polygon}.gpkg"

    gdf_polygon = (
        gpd.read_file(polygon_folder, encoding="cp1252")
        .to_crs("EPSG:2154")
    )

    polygon_geom = gdf_polygon.union_all()
    
    # polygon boundary
    boundary = polygon_geom.boundary
    
    # also consider the outer boundary: 
    # outer boundary only

    if isinstance(polygon_geom, Polygon):
        outer_boundary = polygon_geom.exterior

    elif isinstance(polygon_geom, MultiPolygon):
        
        geoms = [poly for poly in polygon_geom.geoms]
            
        max_area = max(poly.area for poly in geoms)
        threshold = 0.001  # keep polygons with at least 0.1% of the largest polygon's area

        main_geoms = [poly for poly in geoms if poly.area >= max_area * threshold]

        outer_boundary = MultiLineString(
            [poly.exterior for poly in main_geoms]
        )
        '''
        elif isinstance(polygon_geom, MultiPolygon):
            
            outer_boundary = MultiLineString(
                [poly.exterior for poly in polygon_geom.geoms]
            )
        '''
    
    patches_polygon = patches[patches.polygon == polygon]

    for i, index in enumerate(patches_polygon.patch_id.unique()):

        patch = patches_polygon[patches_polygon.patch_id == index].iloc[0]

        # centroid
        centroid = patch.geometry.centroid

        distance_to_edge = centroid.distance(boundary)
        distance_to_outer_edge = centroid.distance(outer_boundary)
      
        results.append({
            'polygon': polygon,
            "patch_id": index,
            "distance_to_edge": distance_to_edge, 
            "distance_to_outer_edge": distance_to_outer_edge
            })
        

        # nearest point on boundary
        centroid_pt, nearest_boundary_pt = nearest_points(
            centroid,
            boundary
        )

        print(
            f"Patch {index}: distance = {distance_to_edge:.2f} m"
        )
        
        if i % 400 == 0:
            # -------------------
            # Plot
            # -------------------
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # full polygon boundary (includes holes)
            gpd.GeoSeries([boundary]).plot(
                ax=ax,
                linewidth=2,
                label="Full boundary", 
                alpha = 0.5,
                
            )
            
            # outer boundary only
            gpd.GeoSeries([outer_boundary]).plot(
                ax=ax,
                linewidth=2,
                label="Outer boundary", 
                color = "black" 
            )
            
            # patch
            gpd.GeoSeries([patch.geometry]).plot(
                ax=ax,
                alpha=0.5,
                label="Patch"
            )
            
            # centroid
            ax.scatter(
                centroid.x,
                centroid.y,
                s=50,
                marker="o",
                label="Centroid"
            )
            
            # nearest point on outer boundary
            centroid_pt, nearest_outer_pt = nearest_points(
                centroid,
                outer_boundary
            )
            
            # line to outer edge
            ax.plot(
                [centroid_pt.x, nearest_outer_pt.x],
                [centroid_pt.y, nearest_outer_pt.y],
                linewidth=2,
                label=f"Outer distance = {distance_to_outer_edge:.1f} m \n distance = {distance_to_edge:1f}"
            )
            
            # nearest point
            ax.scatter(
                nearest_outer_pt.x,
                nearest_outer_pt.y,
                s=50,
                marker="x",
                label="Nearest outer point"
            )
            
            ax.set_title(f"{polygon} — Patch {index}")
            ax.set_aspect("equal")
            ax.legend()
            
            plt.show()
        
df_distance_to_edge = pd.DataFrame(results)

print(len(df_distance_to_edge))
print(df_distance_to_edge.isna().any(axis=1).sum())

#%%
new_path = Path(path_to_save)
csv_filename = "distance_to_edge.csv"
df_distance_to_edge.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   
        

#%% OTHER IDEAS FOR HANDLING STUFF: now we do a form of smooting to remove smaller holes. To get an understanding of the distance to the "outer patch" 


from shapely.geometry import LineString

outer_boundary = polygon_geom.exterior
distance_to_edge = centroid.distance(outer_boundary)

from shapely.geometry import MultiLineString

outer_boundary = MultiLineString(
    [poly.exterior for poly in polygon_geom.geoms]
)

distance_to_edge = centroid.distance(outer_boundary)

# plot these and see what it looks like! 

#%%

polygon = "V-020"

polygon_folder = path_polygons + f"/{polygon}.gpkg"

gdf_polygon = (
    gpd.read_file(polygon_folder, encoding="cp1252")
    .to_crs("EPSG:2154")
)

polygon_geom = gdf_polygon.union_all()
from shapely.geometry import MultiLineString

outer_boundary = MultiLineString(
    [poly.exterior for poly in polygon_geom.geoms]
)


'''start'''

geoms = [poly for poly in polygon_geom.geoms]
    
max_area = max(poly.area for poly in geoms)
threshold = 0.01  # keep polygons with at least 1% of the largest polygon's area

main_geoms = [poly for poly in geoms if poly.area >= max_area * threshold]

outer_boundary = MultiLineString(
    [poly.exterior for poly in main_geoms]
)
'''end'''



distance_to_edge = centroid.distance(outer_boundary)

gpd.GeoSeries([outer_boundary]).plot()
plt.axis("equal")
plt.show()
        
        
# this is nicer! Also save this!! 

# %% step for step debug: 
   
polygon = "V-020"

polygon_folder = path_polygons + f"/{polygon}.gpkg"

gdf_polygon = (
    gpd.read_file(polygon_folder, encoding="cp1252")
    .to_crs("EPSG:2154")
)

polygon_geom = gdf_polygon.union_all()

polygons = list(polygon_geom.geoms)

print(len(polygons))

for i, poly in enumerate(polygons):
    print(i, poly.area)    

# now look if the polygons are inside of each other? 
outer_polygons = []

for i, poly in enumerate(polygons):

    inside = False

    for j, other in enumerate(polygons):

        if i == j:
            continue

        if other.contains(poly):
            inside = True
            break

    if not inside:
        outer_polygons.append(poly)

outer_lines = [
    poly.exterior
    for poly in outer_polygons
]

outer_boundary = MultiLineString(outer_lines) 
   
for i, poly in enumerate(polygons):
    print(
        i,
        "area:", poly.area,
        "bounds:", poly.bounds
    )
    

gpd.GeoSeries([outer_boundary]).plot()
plt.axis("equal")
plt.show()

#%%
# save this idea, then take care later: 
'''try new function'''
from shapely.geometry import Polygon, MultiPolygon, MultiLineString
from shapely.ops import unary_union

def get_outer_boundary(polygon_geom, buffer_dist=200):
    """
    Returns only the true outer boundary of a (Multi)Polygon by:
    1. Buffering outward to merge nearby fragments and close internal gaps
    2. Taking the union (which dissolves everything into one shell)
    3. Buffering back inward to restore approximate original shape
    4. Extracting only the exterior rings (drops all holes/islands)
    
    buffer_dist: tune this to be larger than the gaps between
                 fragments you want to swallow (in CRS units = meters for EPSG:2154)
    """
    # Step 1+2: close all gaps and merge outliers that are within buffer_dist
    closed = polygon_geom.buffer(buffer_dist).buffer(-buffer_dist)
    
    # Step 3: drop all interior holes — keep only exterior rings
    if isinstance(closed, Polygon):
        clean = Polygon(closed.exterior)
    elif isinstance(closed, MultiPolygon):
        clean = MultiPolygon([Polygon(p.exterior) for p in closed.geoms])
    
    # Step 4: extract boundary for distance calculations
    if isinstance(clean, Polygon):
        return clean.exterior, clean
    else:
        return MultiLineString([p.exterior for p in clean.geoms]), clean
'''try new function '''


'''remove small areas first approach:'''
elif isinstance(polygon_geom, MultiPolygon):
    
    geoms = [poly for poly in polygon_geom.geoms]
        
    max_area = max(poly.area for poly in geoms)
    threshold = 0.01  # keep polygons with at least 1% of the largest polygon's area

    main_geoms = [poly for poly in geoms if poly.area >= max_area * threshold]

    outer_boundary = MultiLineString(
        [poly.exterior for poly in main_geoms]
    )

        

