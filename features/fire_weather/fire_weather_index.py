# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 13:37:13 2026

@author: steff
"""

# TO DOS: 
# Get the patch file 
# Get the polygons files 
# Process the fire weather indices 

# Load the data: 
    
# load the netcdf file of temperature and precipitation in france: 
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt 
import geopandas as gpd
import pandas as pd 
import glob
from pathlib import Path
import netCDF4
import cfgrib
from shapely.geometry import Point

path_to_save = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing the Fire Weather Indices"

# Root folder containing the yearly subfolders
folder = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing the Fire Weather Indices\copernicus_data"

# Find all grib files in all subfolders
files = sorted(glob.glob(folder + r"\**\*.grib", recursive=True))

print(files[0])
print(f"Found {len(files)} files.")

# Open and merge
ds = [xr.open_dataset(f, engine="cfgrib") for f in files]
print(ds)

#%%
ds_fire_weather = xr.concat(ds, dim="time")
ds_fire_weather = ds_fire_weather.sortby("time")

# extract the location and time
lat = np.array(ds_fire_weather.latitude)
lon = np.array(ds_fire_weather.longitude) 
time= ds_fire_weather.valid_time[:]

print(time)
print(ds_fire_weather)

#%% start setup 
results = []

# Get the polygons we consider for the analysis: 
#complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing the Fire Weather Indices\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# polygons to consider
polygons = patches.polygon.unique()


for polygon_name in polygons: 
    print(polygon_name)
    polygon_name = polygon_name.strip()
    
    polygon_folder = f"C:/Users/steff/Documents/16_Work_LSCE/September/Processing the Fire Weather Indices/Polygons/{polygon_name}.gpkg" 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:4326")
    
    # ------------LOCATION OF POLYGON------------------
    # get bounding box of the polygon
    polygon_bounds = gdf_polygon.total_bounds 
    lon_min, lat_min, lon_max, lat_max = [round(v, 2) for v in polygon_bounds]
    
    # get the location of the centre of the polygon: 
    gdf_polygon["centroid"] = gdf_polygon.geometry.centroid
    polygon_center = gdf_polygon.centroid.get_coordinates()
    center_lon, center_lat = np.round(polygon_center['x'].values[0],2), np.round(polygon_center['y'].values[0], 2)
    #print(center_lon, center_lat)
    
    # different indexing system: 
    distance = ((ds_fire_weather.latitude - center_lat)**2 + (ds_fire_weather.longitude - center_lon)**2)
    nearest_index = distance.argmin(dim="values")
    
    # get the index of the longitute and latitude values that are closest to this center: 
    index_lat= np.argmin(np.abs(lat-center_lat))
    index_lon= np.argmin(np.abs(lon-center_lon))
    
    print("Nearest grid point:")
    print("Latitude:", ds_fire_weather.latitude.isel(values=nearest_index).values)
    print("Longitude:", ds_fire_weather.longitude.isel(values=nearest_index).values)
    
    #for plotting create a geometry point where we take the climate data from 
    point = gpd.points_from_xy([lon[index_lon]], [lat[index_lat]], crs = "EPSG:4326")
    
    nearest_lat = ds_fire_weather.latitude.isel(values=nearest_index).item()
    nearest_lon = ds_fire_weather.longitude.isel(values=nearest_index).item()
    point2 = gpd.GeoSeries([Point(nearest_lon, nearest_lat)], crs="EPSG:4326")
    
    print(index_lat, index_lon)
    print(point)
    #print(lon[index_lon], lat[index_lat])
    
    '''
    # check the location of the climate data in relation to polygon 
    fig, ax = plt.subplots()

    gdf_polygon.plot(ax=ax, color="lightblue", edgecolor="black")
    #gdf_polygon.centroid.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2)
    #point.plot(ax=ax, edgecolor= "red", linewidth = 2)
    gpd.GeoSeries(point2).plot(ax =ax, color = 'red', linewidth = 2)
    plt.show()
    '''
    
    # --------------DATE OF FIRE------------------------
    # get the start of fire date 
    gdf_polygon["fire_date"] = pd.to_datetime(
        gdf_polygon["date_de_premiere_alerte"].astype(int),
        unit="s"
    )
    
    date_fire = gdf_polygon['fire_date'].iloc[0]
    
    # Decide on time interval to look at.
    #before fire
    start_date_before = date_fire - pd.Timedelta(days = 200)
    end_date_before = date_fire
    
    #afterfire
    start_date_after = date_fire
    end_date_after = date_fire + pd.Timedelta(days = 200)
    
    # plot the different indices. 
    
    ds_period = ds_fire_weather.sel(valid_time=slice(start_date_before, end_date_after))
    
    ds_fire_day = ds_fire_weather.sel(time = date_fire, method = "nearest")
    
    # Extract the three indices at the fire location
    build_up_index = ds_period.fbupinx.isel(values=nearest_index)
    fire_weather_index = ds_period.fwinx.isel(values=nearest_index)
    initial_fire_spread_index = ds_period.infsinx.isel(values=nearest_index)
    
    build_up_index_day = ds_fire_day.fbupinx.isel(values=nearest_index).item()
    fire_weather_index_day = ds_fire_day.fwinx.isel(values=nearest_index).item()
    initial_fire_spread_index_day = ds_fire_day.infsinx.isel(values=nearest_index).item()
    
    '''
    fig, axes = plt.subplots(
        3, 1,
        figsize=(12, 9),
        sharex=True
    )
    
    # Build-up index
    axes[0].plot(
        build_up_index.time,
        build_up_index
    )
    axes[0].axvline(date_fire, linestyle="--")
    axes[0].set_ylabel("Build-up Index")
    axes[0].grid()
    
    # Fire Weather Index
    axes[1].plot(
        fire_weather_index.time,
        fire_weather_index
    )
    axes[1].axvline(date_fire, linestyle="--")
    axes[1].set_ylabel("Fire Weather Index")
    axes[1].grid()
    
    # Initial Fire Spread Index
    axes[2].plot(
        initial_fire_spread_index.time,
        initial_fire_spread_index
    )
    axes[2].axvline(date_fire, linestyle="--")
    axes[2].set_ylabel("Initial Fire Spread")
    axes[2].set_xlabel("Date")
    axes[2].grid()
    
    plt.tight_layout()
    plt.show()
    '''
    
    results.append({"polygon_id": polygon_name,
                    "fire_date": date_fire,
                    "build_up_index": build_up_index_day, 
                    "fire_weather_index":  fire_weather_index_day, 
                    "initial_fire_spread": initial_fire_spread_index_day })
    
df_fire_indices = pd.DataFrame(results)


#%% PROCESS THE DROUGHT INDEX: 
    
folder_drought_index = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing the Fire Weather Indices\copernicus_data\drought_code\868f5a02518821c75e6f6d3eadf8331b.grib"
ds_drought_index = xr.open_dataset(folder_drought_index, engine="cfgrib")
print(ds_drought_index)

# extract the location and time
lat = np.array(ds_drought_index.latitude)
lon = np.array(ds_drought_index.longitude) 
time= ds_drought_index.valid_time[:]


results = []

# Get the polygons we consider for the analysis: 
#complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing the Fire Weather Indices\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# polygons to consider
polygons = patches.polygon.unique()

for polygon_name in polygons: 
    print(polygon_name)
    polygon_name = polygon_name.strip()
    
    polygon_folder = f"C:/Users/steff/Documents/16_Work_LSCE/September/Processing the Fire Weather Indices/Polygons/{polygon_name}.gpkg" 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:4326")
    
    # ------------LOCATION OF POLYGON------------------
    # get bounding box of the polygon
    polygon_bounds = gdf_polygon.total_bounds 
    lon_min, lat_min, lon_max, lat_max = [round(v, 2) for v in polygon_bounds]
    
    # get the location of the centre of the polygon: 
    gdf_polygon["centroid"] = gdf_polygon.geometry.centroid
    polygon_center = gdf_polygon.centroid.get_coordinates()
    center_lon, center_lat = np.round(polygon_center['x'].values[0],2), np.round(polygon_center['y'].values[0], 2)
    #print(center_lon, center_lat)
    
    # different indexing system: 
    distance = ((ds_drought_index.latitude - center_lat)**2 + (ds_drought_index.longitude - center_lon)**2)
    nearest_index = distance.argmin(dim="values")
    
    # get the index of the longitute and latitude values that are closest to this center: 
    index_lat= np.argmin(np.abs(lat-center_lat))
    index_lon= np.argmin(np.abs(lon-center_lon))
    
    print("Nearest grid point:")
    print("Latitude:", ds_fire_weather.latitude.isel(values=nearest_index).values)
    print("Longitude:", ds_fire_weather.longitude.isel(values=nearest_index).values)
    
    #for plotting create a geometry point where we take the climate data from 
    point = gpd.points_from_xy([lon[index_lon]], [lat[index_lat]], crs = "EPSG:4326")
    
    nearest_lat = ds_drought_index.latitude.isel(values=nearest_index).item()
    nearest_lon = ds_drought_index.longitude.isel(values=nearest_index).item()
    point2 = gpd.GeoSeries([Point(nearest_lon, nearest_lat)], crs="EPSG:4326")
    
    print(index_lat, index_lon)
    print(point)
    #print(lon[index_lon], lat[index_lat])
    
    '''
    # check the location of the climate data in relation to polygon 
    fig, ax = plt.subplots()

    gdf_polygon.plot(ax=ax, color="lightblue", edgecolor="black")
    #gdf_polygon.centroid.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2)
    #point.plot(ax=ax, edgecolor= "red", linewidth = 2)
    gpd.GeoSeries(point2).plot(ax =ax, color = 'red', linewidth = 2)
    plt.show()
    '''
    
    # --------------DATE OF FIRE------------------------
    # get the start of fire date 
    gdf_polygon["fire_date"] = pd.to_datetime(
        gdf_polygon["date_de_premiere_alerte"].astype(int),
        unit="s"
    )
    
    date_fire = gdf_polygon['fire_date'].iloc[0]
    
    # Decide on time interval to look at.
    #before fire
    start_date_before = date_fire - pd.Timedelta(days = 200)
    end_date_before = date_fire
    
    #afterfire
    start_date_after = date_fire
    end_date_after = date_fire + pd.Timedelta(days = 200)
    
    # plot the different indices. 
    
    ds_period = ds_drought_index.sel(valid_time=slice(start_date_before, end_date_after))
    
    ds_drought_fire_day = ds_drought_index.sel(time = date_fire, method = "nearest")

    # Extract the three indices at the fire location
    drought_code = ds_period.drtcode.isel(values=nearest_index)
    drought_code_day = ds_drought_fire_day.drtcode.isel(values=nearest_index).item()
    print(drought_code_day)
    
    
    fig, axes = plt.subplots(
        figsize=(12, 9)
    )
    
    # Build-up index
    axes.plot(
        drought_code.time,
        drought_code
    )
    axes.axvline(date_fire, linestyle="--")
    axes.set_ylabel("Drought Code")
    axes.grid()
    
    
    results.append({"polygon_id": polygon_name,
                    "fire_date": date_fire,
                    "drought_code": drought_code_day})

df_drought_code  = pd.DataFrame(results)


#%%

print(len(df_fire_indices))
print(len(df_drought_code))
df_drought_code = df_drought_code[["polygon_id", "drought_code"]]

df_final = df_fire_indices.merge(
    df_drought_code,
    on="polygon_id",
    how="left"
)

new_path = Path(path_to_save)
csv_filename = "fire_climate_indices.csv"
df_final.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")  
