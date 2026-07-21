# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 23:10:18 2026

@author: steff
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from rasterio.mask import mask
from rasterio.features import rasterize
from shapely.geometry import mapping
from matplotlib import pyplot as plt
from rasterio.merge import merge

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np


# LOAD THE TREE GENUS MAPS: 

# ==============FILE STRUCTURE========================
path_france_shape = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Mai\Genus_Map\France_ser\France_ser.shp"

local_folder = "C:/Users/steff/Documents/06-Internshi_Paris/00_pipeline/"

#adjust!!!
path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\biodiversity_genus"
path_polygons = local_folder + "data/Polygons"
path_genus_tiles_overview = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Mai\Genus_Map\grid.gpkg"
path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"

df_ser = gpd.read_file(path_france_shape)

# Resolution of the tree genus map: 
    
# DICTIONARY GENUS MAP:
genus_dic = {
    0: "Larix", 
    1: "Picea", 
    2: "Pinus", 
    3: "Fagus", 
    4: "Quercus", 
    5: "Other needleleaf", 
    6: "Other broadleaf", 
    7: "No trees"     }

# ==== DEFINITION OF DIVERSITY INDECES ====
def richness_index(band, no_tree_class=7):
    """
    Returns the number of unique species/classes in the raster.
    Ignores NaN values.
    """
    # flatten and clean
    vals = band.flatten()
    vals = vals[~np.isnan(vals)]

    # remove no-tree class
    vals = vals[vals != no_tree_class]
    
    return len(np.unique(vals[~np.isnan(vals)]))


def genus_types(band, no_tree_class = 7): 
    """
    Returns the species/classes in the raster.
    Ignores NaN values.
    """
    # flatten and clean
    vals = band.flatten()
    vals = vals[~np.isnan(vals)]
    
    return np.unique(vals[~np.isnan(vals)])

    
def shannon_index(band, no_tree_class=7):
    """
    Computes Shannon diversity index from a raster band.
    Ignores NaN and optionally excludes 'No trees' class.
    """

    # flatten and clean
    vals = band.flatten()
    vals = vals[~np.isnan(vals)]
    
    # case the pixels are not assigned anything
    if len(vals) == 0:
        return np.nan
        
    # remove no-tree class
    vals = vals[vals != no_tree_class]

    # case: the pixels are assigned the "no tree class" 
    # if empty area
    if len(vals) == 0:
        return 0.0

    # get unique classes and counts
    classes, counts = np.unique(vals, return_counts=True)

    # convert to probabilities
    p = counts / counts.sum()

    # Shannon index
    shannon = -np.sum(p * np.log(p))

    return round(shannon,2)

def berger_parker_index(band, no_tree_class=7):
    """
    Berger-Parker dominance index:
    proportion of the most abundant class.
    also return what class this is! 
    """

    vals = band.flatten()
    vals = vals[~np.isnan(vals)]
    
    if len(vals) == 0:
        berger_parker_type = np.nan
        return 0, berger_parker_type
    
    vals = vals[vals != no_tree_class]

    if len(vals) == 0:
        berger_parker_type = 7
        return 0, berger_parker_type

    classes, counts = np.unique(vals, return_counts=True)
    
    dominant_idx = np.argmax(counts)
    
    berger_parker = counts.max() / counts.sum() 
    berger_parker_type = classes[dominant_idx] 
    
    return round(berger_parker, 2), berger_parker_type


def area_with_trees(band, no_tree_class = 7): 
    """ 
    computes the area that has a genus assigned. 
    we are excluding "no tree" and nan pixesl
    """
    vals = band.flatten()
    total_pixels = len(vals)
    
    vals = band.flatten()
    vals = vals[~np.isnan(vals)]
    vals = vals[vals != no_tree_class]
    
    n_tree_pixels = len(vals)
    # resolution is 10m 
    
    return n_tree_pixels * 100, total_pixels * 100 
    

    
# STEP 0: Load the overview of the tiles of the genus maps 
genus_map = gpd.read_file(path_genus_tiles_overview).to_crs("EPSG:2154")

# load patches 
# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

polygons = patches.polygon.unique()

results = []
for polygon_name in polygons: 
    polygon_name = polygon_name.strip()
    
    print(polygon_name)
        
    # STEP 1: Find the tile that intersects with polygon
    # ===================== LOAD POLYGON =====================
    polygon_file = path_polygons + f"/{polygon_name}.gpkg"
    gdf_polygon = gpd.read_file(polygon_file, encoding="latin1").to_crs("EPSG:2154")
    poly_geom = gdf_polygon.geometry.union_all()
    
    # find intersecting tile and get the label!
    france_tiles = genus_map[genus_map.intersects(poly_geom)]
    
    '''
    # Visualize
    ax = genus_map.plot(color="lightgrey", edgecolor="none")
    france_tiles.plot(ax=ax, color="red")
    df_ser.boundary.plot(ax=ax, color="black", linewidth = 0.5, alpha = 0.7)
    plt.show()
    '''
    
    # get the names of the intersecting tiles: 
    # Get all intersecting tile paths
    tile_paths = []
    
    for cid in france_tiles["cid"]:
    
        parts = cid.split("_")
    
        ulx = int(parts[1])
        uly = int(parts[3])
    
        tile_path = (
            rf"C:\Users\steff\Documents\06-Internshi_Paris\00_Mai\Genus_Map"
            rf"\
                "
        )
    
        tile_paths.append(tile_path)
    
    print(f"{len(tile_paths)} intersecting tiles found")
    print(tile_paths)
    
    if len(tile_paths) == 1:
        path_tile_genus_map = tile_paths[0]
        # load the with the polygon intersecting area 
        with rasterio.open(path_tile_genus_map) as src:
    
            # match CRS
            #gdf_polygon = gdf_polygon.to_crs(src.crs)
            # 1. match CRS FIRST
            gdf_polygon_proj = gdf_polygon.to_crs(src.crs)
    
            # clip raster
            data, transform = mask(
                src,
                [mapping(geom) for geom in gdf_polygon_proj.geometry],
                crop=True
            )
    
            band = data[0].astype("float32")
    
            # convert nodata to nan
            if src.nodata is not None:
                band[band == src.nodata] = np.nan
    
            crs = src.crs
        
    else: 
        src_files = [rasterio.open(fp) for fp in tile_paths]
        
        mosaic, mosaic_transform = merge(src_files)
        crs = src_files[0].crs
        nodata = src_files[0].nodata
        
        from rasterio.io import MemoryFile
    
        meta = src_files[0].meta.copy()
        
        meta.update({
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": mosaic_transform
        })
        
        gdf_polygon_proj = gdf_polygon.to_crs(crs)
        
        with MemoryFile() as memfile:
            with memfile.open(**meta) as dataset:
        
                dataset.write(mosaic)
        
                data, transform = mask(
                    dataset,
                    [mapping(geom) for geom in gdf_polygon_proj.geometry],
                    crop=True
                )
            
        band = data[0].astype("float32")
    
        if nodata is not None:
            band[band == nodata] = np.nan
            
        for src in src_files:
            src.close()
        
        
    
    '''PLOT'''
    # discrete colormap with 8 classes
    cmap = plt.get_cmap("tab10", 8)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    im = ax.imshow(
        band,
        cmap=cmap,
        vmin=-0.5,
        vmax=7.5
    )
    
    # colorbar
    cbar = plt.colorbar(im, ax=ax)
    
    cbar.set_ticks(range(8))
    cbar.set_ticklabels([genus_dic[i] for i in range(8)])
    
    cbar.set_label("Dominant genus")
    
    plt.show()
    
    # ===================== PREPARE PATCHES- Rasterize to the genus map =====================
    
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

    
    plt.imshow(patch_raster)
    plt.show()
    
    # Do biodiversity analysis on the level of the patches: 
    for patch_index in np.unique(patch_raster):
        
        # mask for current patch
        mask_patch = patch_raster == patch_index
        patch_id = patches_polygon[patches_polygon.index == patch_index].patch_id
        
        if patch_index == -1:
            print(patch_id)
            continue
    
        # direct extraction of values inside patch
        values = band[mask_patch]
        
        # get the diversity indeces: 
        richness = richness_index(values)
        shannon = shannon_index(values)
        berger_parker, berger_parker_type = berger_parker_index(values)
        area_with, total_area = area_with_trees(values)
        genus_type = genus_types(values)
        
        '''plot start 
        # --- plotting ---
        patch_values = np.where(mask_patch, band, np.nan)
    
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    
        # Patch mask
        axes[0].imshow(mask_patch, origin="upper")
        axes[0].set_title(f"Patch {patch_index}")
        axes[0].axis("off")
    
        # Values inside patch
        im = axes[1].imshow(patch_values, origin="upper")
        axes[1].set_title(
            f"Richness={richness:.2f}\n"
            f"Shannon={shannon:.2f}\n"
            f"Berger-Parker={berger_parker:.2f}\n"
            f"area_with = {area_with} \n"
            f"are_total = {total_area}"
        )
        axes[1].axis("off")
    
        plt.colorbar(im, ax=axes[1], shrink=0.8, label="Band value")
        plt.tight_layout()
        plt.show()
        plot end '''
    
        row = patches_polygon.iloc[patch_index]
        	
        results.append({
                "polygon": polygon_name,
                "index2": row.name,
                "patch_index": patch_index,
                "patch_id": row.patch_id,
                "tfv_num": row.TFV_num,
                "richness_index": richness,
                "shannon_index": shannon, 
                "berger_parker_index": berger_parker,
                "dominant_genus": genus_dic.get(berger_parker_type), 
                "area_with_trees": area_with, 
                "total_area_from_pixels": total_area, 
                "tree_coverage": round(area_with/ total_area, 2), 
                "area": row.patches_area, 
                "genus_types": genus_type
            })
            
        
# ===================== OUTPUT =====================


df_diversity_indices = pd.DataFrame(results)
print(df_diversity_indices.columns)
df_diversity_indices = df_diversity_indices[['polygon', 'patch_id', 'tfv_num','richness_index', 'shannon_index', 'berger_parker_index',
'dominant_genus', 'area_with_trees', 'total_area_from_pixels',
'tree_coverage', 'genus_types' ]]

print(len(patches))
print(len(patches_polygon))
print(len(df_diversity_indices))

print(set(patches.patch_id) - set(df_diversity_indices.patch_id))

#%%
#SAVING FILE 
csv_filename = "biodiversity_indices_genus.csv"
path = path_to_save + f"/{csv_filename}"
df_diversity_indices.to_csv(path, index=False, sep=";", float_format="%.3f", decimal=".")

    
    
    
    
    
    
    
    