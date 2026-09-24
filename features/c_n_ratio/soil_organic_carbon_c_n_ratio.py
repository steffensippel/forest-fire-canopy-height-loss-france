# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 10:36:21 2026

@author: steff
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from shapely.geometry import box, mapping
from matplotlib import pyplot as plt

import rasterio.mask
from rasterstats import zonal_stats
import rasterio

import geopandas as gpd
from rasterio.plot import plotting_extent

from pathlib import Path 

# Load the soil organic carbon for the 1 ha patches within the fire polygons. 


# ===================== INPUTS ====================

soil_carbon_path = r"C:\Users\steff\Documents\16_Work_LSCE\September\Soil Organic Carbon\input\250_GSNmap_mean_soc_0_30.tif"
c_n_path = r"C:\Users\steff\Documents\16_Work_LSCE\September\CN Ratio\input\cn_ess2_L93.tif"

path_to_save = r"C:\Users\steff\Documents\16_Work_LSCE\September\Soil Organic Carbon\output"

path_polygons = r"C:\Users\steff\Documents\16_Work_LSCE\September\data\Polygons"

path_patches_shapes = r"C:\Users\steff\Documents\16_Work_LSCE\September\data\all_polygons_cut_overlap_removed_with_id.gpkg"

# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# RELEVANT POLYGONS 
polygons = patches.polygon.unique()
print(len(polygons))

# %% Example plot of the soil carbon map
results = []

for polygon_name in polygons: 
    
    polygon_file = path_polygons + f"/{polygon_name}.gpkg"
    gdf_polygon = gpd.read_file(polygon_file, encoding="latin1")
    
    with rasterio.open(c_n_path) as src:
        # --- reproject polygon to raster CRS ---
        gdf_proj = gdf_polygon.to_crs(src.crs)
    
        # --- buffered bounding box ---
        buffer = 500
        minx, miny, maxx, maxy = gdf_proj.total_bounds
    
        bbox = box(
            minx- buffer, miny- buffer,
            maxx + buffer, maxy + buffer
        )
    
        # --- clip raster ---
        data, transform = rasterio.mask.mask(
            src,
            [mapping(bbox)],
            crop=True
        )
    
        band = data[0].astype("float32")
    
        if src.nodata is not None:
            band[band == src.nodata] = np.nan
        
    gdf_polygon = gdf_polygon.to_crs(src.crs)
    
    '''
    # plot as one example: 
    fig, ax = plt.subplots(figsize=(8, 6))
    
    extent = plotting_extent(band, transform)
    
    im = ax.imshow(
        band,
        cmap="viridis",
        extent=extent,
        vmin=np.nanpercentile(band, 2),
        vmax=np.nanpercentile(band, 98)
    )
    
    plt.colorbar(im, ax=ax, label= "cn_ratio")
    
    # plot polygon boundary
    gdf_polygon.to_crs(src.crs).boundary.plot(
        ax=ax,
        color="black",
        linewidth=1
    )
    
    plt.title("c_n_ratio")
    plt.show()
    '''
    
    # get statistics of the raster within the polygon shape 
    stats = zonal_stats(
        gdf_polygon,
        band,
        affine=transform,
        stats=["min", "max", "mean", "std", "count"],
        nodata=src.nodata
    )
    
    stat = stats[0]
    print(stat)
    
    print(stat["count"])
    # call back: if zonal stats does not find pixel values within the polygon shape: take one value. 
    '''start'''
    # ---------------------------------------------------------
    # FALLBACK: no raster pixels inside polygon
    # ---------------------------------------------------------

    if stat["count"] is None or stat["count"] == 0:
 
        print(
            f"{polygon_name}: No raster pixel inside polygon. "
            f"Using closest pixel."
        )
 
        # Polygon centroid
        centroid = gdf_polygon.geometry.iloc[0].centroid
 
        # Get coordinates of all valid raster pixels
        rows, cols = np.where(np.isfinite(band))
 
        # Convert pixel indices to map coordinates
        xs, ys = rasterio.transform.xy(
            transform,
            rows,
            cols,
            offset="center"
        )
 
        xs = np.asarray(xs)
        ys = np.asarray(ys)
 
        # Distance from each valid pixel centre to polygon centroid
        distances = np.sqrt(
            (xs - centroid.x) ** 2 +
            (ys - centroid.y) ** 2
        )
 
        # Index of closest pixel
        closest_idx = np.argmin(distances)
 
        closest_row = rows[closest_idx]
        closest_col = cols[closest_idx]
 
        closest_value = float(band[closest_row, closest_col])
 
        closest_distance = float(distances[closest_idx])
 
        print(
            f"Closest pixel value: {closest_value:.2f}"
        )
        print(
            f"Distance to polygon centroid: "
            f"{closest_distance:.2f} map units"
        )
 
        # Use closest pixel value
        stat = {
            "min": closest_value,
            "max": closest_value,
            "mean": closest_value,
            "std": 0.0,
            "count": 1
        }
    
    '''end'''
    # round the stats
    
    
    stat = {
        key: round(float(value), 2)
        if value is not None
        else None
        for key, value in stat.items()
    }
    
    print(stat)
    
    # HERE INCLUDE: IF THE ZONAL STATS COUNT IS ZERO: JUST TAKE THE VALUE OF THE CLOSEST PIXEL!!! 
    
    df = pd.DataFrame([stat])
    df = df.rename(columns={
        "min": "c_n_ratio_min",
        "max": "c_n_ratio_max",
        "mean": "c_n_ratio_mean",
        "std": "c_n_ratio_std",
        "count": "c_n_ratio_count",
    })
    
    df["polygon"] = polygon_name
    
    results.append(df)


df_cn_ratio = pd.concat(results, ignore_index=True)

new_path = Path(path_to_save)
csv_filename = "c_n_ratio.csv"
df_cn_ratio.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f") 




