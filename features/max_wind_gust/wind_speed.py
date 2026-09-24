# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 11:09:53 2026

@author: steff
"""

# compute the maximum wind value for the 5 year period after the fire. Also save the date (we are only interested in the year) for that this speed is measured! 

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

path_to_save = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing wind speed\output"

# wind speed file
wind_speed_base_file = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing wind speed\input"
wind_speed_file = r"C:\Users\steff\Documents\16_Work_LSCE\September\Processing wind speed\input\8739c9a95bac40233af065213d384724.nc"


# Open and merge
ds = xr.open_dataset(wind_speed_file, engine="netcdf4")
print(ds)

files = sorted(glob.glob(wind_speed_base_file + r"\**\*.nc", recursive=True))
print(len(files))

ds_windspeeds = [xr.open_dataset(f, engine="netcdf4") for f in files]

ds = xr.concat(ds_windspeeds, dim="valid_time")
ds = ds.sortby("valid_time")
print(ds)
# extract the location and time
lat = np.array(ds.latitude)
lon = np.array(ds.longitude) 
time= ds.valid_time[:]

print(time)

print(time.min())
print(time.max())


#%% start setup 
results = []

# Get the polygons we consider for the analysis: 
#complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\16_Work_LSCE\September\fire_weather\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# polygons to consider
polygons = patches.polygon.unique()
print(len(polygons))

for polygon_name in polygons: 
    print(polygon_name)
    polygon_name = polygon_name.strip()
    
    polygon_folder = f"C:/Users/steff/Documents/16_Work_LSCE/September/fire_weather/Polygons/{polygon_name}.gpkg" 
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
    
    # get the index of the longitute and latitude values that are closest to this center: 
    index_lat= np.argmin(np.abs(lat-center_lat))
    index_lon= np.argmin(np.abs(lon-center_lon))
    
    
    #for plotting create a geometry point where we take the climate data from 
    point = gpd.points_from_xy([lon[index_lon]], [lat[index_lat]], crs = "EPSG:4326")
    
    #print(lon[index_lon], lat[index_lat])
    
    '''
    # check the location of the climate data in relation to polygon 
    fig, ax = plt.subplots()

    gdf_polygon.plot(ax=ax, color="lightblue", edgecolor="black")
    #gdf_polygon.centroid.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2)
    #point.plot(ax=ax, edgecolor= "red", linewidth = 2)
    gpd.GeoSeries(point).plot(ax =ax, color = 'red', linewidth = 2)
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
    start_date_before = date_fire
    
    '''Update this!!!!'''
    end_date_before = date_fire
    
    latest_date = pd.Timestamp("2025-12-31")
    
    #afterfire
    start_date_after = date_fire
    end_date_after = min(start_date_after + pd.DateOffset(years= 5), latest_date)
    # plot the different indices. 
    ds_period = ds.sel(valid_time=slice(start_date_before, end_date_after))
    
    
    # Extract the windspeed at the fire location 
    
    wind_speed_time_series = ds_period.i10fg[:,index_lat,index_lon]
    wind_speed_max = np.round(float(wind_speed_time_series.max().item()), 2)
    wind_speed_max_date = pd.to_datetime(wind_speed_time_series.idxmax(dim = "valid_time").item())
    
    '''
    print(wind_speed_max, wind_speed_max_date)
    
    fig, axes = plt.subplots(
        figsize=(12, 9))
    
    # Wind speed time series 
    axes.plot(
        wind_speed_time_series.valid_time,
        wind_speed_time_series
    )
    
    
    axes.axvline(date_fire, linestyle="--")
    axes.axvline(wind_speed_max_date, color = "red", linestyle = "--")
    axes.set_ylabel("Wind_speed")
    
    axes.grid()
    
    
    
    plt.tight_layout()
    plt.show()
    print(wind_speed_max)
    '''
    
    results.append({"polygon_id": polygon_name,
                    "fire_date": date_fire,
                    "max_instantaneous_wind_gust": wind_speed_max, 
                    "date_max_wind": wind_speed_max_date})
    
df_max_wind_speed = pd.DataFrame(results)
print(len(df_max_wind_speed))
#%%

new_path = Path(path_to_save)
csv_filename = "max_wind_gust.csv"
df_max_wind_speed.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

