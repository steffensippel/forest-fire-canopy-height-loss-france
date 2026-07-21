# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 19:52:59 2026

@author: steff
"""

# load the netcdf file of temperature and precipitation in france: 
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt 
import geopandas as gpd
import pandas as pd 
import glob
from pathlib import Path
import netCDF4


path_to_save = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\temperature_precipitation"

#%% START HERE:

# FIRST: climate data 30 days before and after fire 
    
# merge the xarray files. for the daily maximum temperature files 
import glob
import xarray as xr

# GET THE PRECIPITATION NETCDF FILES 
# Root folder containing the yearly subfolders
folder2 = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\weather\cumulative_precipitation"

# Find all NetCDF files in all subfolders
files2 = sorted(glob.glob(folder2 + r"\**\*.nc", recursive=True))

print(files2[0])
print(f"Found {len(files)} files.")

# Open and merge
datasets2 = [xr.open_dataset(f, engine="netcdf4") for f in files2]

ds_prec = xr.concat(datasets2, dim="valid_time")
ds_prec = ds_prec.sortby("valid_time")

# extract the location and time
#lat = np.array(ds_prec.latitude)
#lon = np.array(ds_prec.longitude) 
time_prec= ds_prec.valid_time[:]

# GET THE MAX TEMPERATURE FILES
# Root folder containing the yearly subfolders
folder = r"C:\Users\steff\Documents\06-Internshi_Paris\00_Juni\weather\max_temp"

# Find all NetCDF files in all subfolders
files = sorted(glob.glob(folder + r"\**\*.nc", recursive=True))

print(files[0])
print(f"Found {len(files)} files.")

# Open and merge
datasets = [xr.open_dataset(f, engine="netcdf4") for f in files]

ds_temp = xr.concat(datasets, dim="valid_time")
ds_temp = ds_temp.sortby("valid_time")

# extract the location and time
lat = np.array(ds_temp.latitude)
lon = np.array(ds_temp.longitude) 
time= ds_temp.valid_time[:]


# start setup 
results = []

# Get the polygons we consider for the analysis: 
#complete patch file: 
path_patches_shapes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\processed_patches\all_polygons_cut_overlap_removed_with_id.gpkg"


# now load the patches: 
input_file = path_patches_shapes 
patches = gpd.read_file(input_file)

# polygons to consider
polygons = patches.polygon.unique()

print(len(polygons))



for polygon_name in polygons: 
    print(polygon_name)
    polygon_name = polygon_name.strip()
    
    polygon_folder = f"C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/Polygons/{polygon_name}.gpkg" 
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
    
    #before fire
    start_date_before = date_fire - pd.Timedelta(days = 30)
    end_date_before = date_fire
    
    #afterfire
    start_date_after = date_fire
    end_date_after = date_fire + pd.Timedelta(days = 30)
    
    # store temperature before and after fire 
    ds_before_fire = ds_temp.sel(valid_time=slice(start_date_before, end_date_before))
    ds_after_fire = ds_temp.sel(valid_time=slice(start_date_after, end_date_after))
    
    # store precipitation before and after fire 
    ds_prec_before_fire = ds_prec.sel(valid_time=slice(start_date_before, end_date_before))
    ds_prec_after_fire = ds_prec.sel(valid_time=slice(start_date_after, end_date_after))
    
    '''HERE ADJUST: WHAT OTHER METRICS COULD WE BE INTERESTED IN???'''
    
    # ------------GET MEAN VALUES FOR THE ONE COORDINATE-----------------------
    # get the mean value for the coordinate closest to the center of the polygon 
    temp_before_fire = ds_before_fire.t2m[:,index_lat,index_lon] - 273.15
    temp_after_fire = ds_after_fire.t2m[:, index_lat, index_lon] - 273.15
    mean_temp_before = np.mean(temp_before_fire.values)
    mean_temp_after = np.mean(temp_after_fire.values)
    
    #precipitation
    prec_before_fire = ds_prec_before_fire.tp[:,index_lat,index_lon]*1000
    prec_after_fire = ds_prec_after_fire.tp[:, index_lat, index_lon]*1000
    sum_prec_before = np.sum(prec_before_fire.values)
    sum_prec_after = np.sum(prec_after_fire.values)
   
    #print(prec_before_fire.values)
    
    # get the number of days above 30 degrees for the coordinte clostes to the center of the polygon
    num_days_above_30_before = np.sum(temp_before_fire.values > 30)
    num_days_above_30_after = np.sum(temp_after_fire.values > 30)
    #print(num_days_above_30_before)
    #print(num_days_above_30_after)
    
    
    results.append({
           "polygon_id": polygon_name,
           "fire_date": date_fire,
           "mean_temp_before_fire": np.round(mean_temp_before, 2), 
           "mean_temp_after_fire": np.round(mean_temp_after, 2),
           "num_days_above_30_before": num_days_above_30_before,
           "num_days_above_30_after": num_days_above_30_after, 
           "sum_prec_before_fire": np.round(sum_prec_before,2),
           "sum_prec_after_fire": np.round(sum_prec_after,2),
           
       })
    
    

    
df_prec_temp = pd.DataFrame(results)

print(len(df_prec_temp))

new_path = Path(path_to_save)
csv_filename = "temp_prec_30_days_around_fire.csv"
df_prec_temp.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

#%% 

results3 = []
results4 = []

#polygons to load 

for polygon_name in polygons:
# ----------LOAD POLYGON FILE ----------------
#polygon_name = "Q-048"
    polygon_name = polygon_name.strip()
    polygon_folder = f"C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/Polygons/{polygon_name}.gpkg" 
    gdf_polygon = gpd.read_file(polygon_folder, encoding="cp1252").to_crs("EPSG:4326")
    
    # Then seasonal averages over a 5 year period 
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
    print(lon[index_lon], lat[index_lat])
    
    # load the precipitation and temperature data for the five years following the year of the fire. (including the year of the fire)
    # STEP 1: get the year of fire: 
        
    # get the start of fire date 
    gdf_polygon["fire_date"] = pd.to_datetime(
        gdf_polygon["date_de_premiere_alerte"].astype(int),
        unit="s"
    )
    date_fire = gdf_polygon['fire_date'].iloc[0]
    year_fire = date_fire.year
    print(year_fire)
    
    years = np.arange(max(year_fire-1, 2015), min(year_fire+4, 2023)+1)
    print(years)
    
    
    # ============================= GET THE SEASONAL AVERAGES PER YEAR ===========================
    
    # ============================
    # TEMPERATURE
    # ============================
    
    ds_temp_loc = ds_temp.t2m[:, index_lat, index_lon] - 273.15
    
    ds_temp_subset = ds_temp_loc.where(
        ds_temp_loc.valid_time.dt.year.isin(np.append(years[0]-1, years)),
        drop=True
    )
    
    ds_temp_subset = ds_temp_subset.assign_coords(
        season_year=(
            "valid_time",
            ds_temp_subset.valid_time.dt.year.where(
                ds_temp_subset.valid_time.dt.month != 12,
                ds_temp_subset.valid_time.dt.year + 1
            ).data
        )
    )
    
    temp_seasonal_year = (
        ds_temp_subset
        .groupby(["season_year", "valid_time.season"])
        .mean()
    )
    
    temp_seasonal_year = temp_seasonal_year.sel(season_year=years)
    
    temp_seasonal_df = (
        temp_seasonal_year
        .to_dataframe(name="temperature")
        .reset_index()
    )
    
    
    # ============================
    # PRECIPITATION
    # ============================
    
    ds_prec_loc = ds_prec.tp[:, index_lat, index_lon]   # adjust variable name if needed
    
    ds_prec_subset = ds_prec_loc.where(
        ds_prec_loc.valid_time.dt.year.isin(np.append(years[0]-1, years)),
        drop=True
    )
    
    ds_prec_subset = ds_prec_subset.assign_coords(
        season_year=(
            "valid_time",
            ds_prec_subset.valid_time.dt.year.where(
                ds_prec_subset.valid_time.dt.month != 12,
                ds_prec_subset.valid_time.dt.year + 1
            ).data
        )
    )
    
    prec_seasonal_year = (
        ds_prec_subset
        .groupby(["season_year", "valid_time.season"])
        .sum()
    )

    prec_seasonal_year = prec_seasonal_year.sel(season_year=years)
    
    prec_seasonal_df = (
        prec_seasonal_year
        .to_dataframe(name="precipitation")
        .reset_index()
    )

    
    
    # ============================
    # MERGE
    # ============================
    
    seasonal_df = temp_seasonal_df.merge(
        prec_seasonal_df,
        on=["season_year","season", "number", "latitude", "longitude"],
        how="left"
    )
    
    seasonal_df["polygon"] = polygon_name
    seasonal_df["fire_date"] = date_fire
    
    results3.append(seasonal_df)    
    
  
    
    # ============================== AVERAGE PER SEASON OVER TIME SPAN OF 5 YEARS ====================
 
    # TEMPERATURE 
    # Compute mean over seasons over time span of 5 years 
    temp_seasonal = (
        ds_temp_subset
        .groupby(["valid_time.season"])
        .mean()
    )
    
    # get dataframe 
    temp_season_df = (
        temp_seasonal
        .to_dataframe(name="temperature")
        .reset_index()
    )

    # PRECIPITATION
    prec_seasonal = (ds_prec_subset.groupby(["valid_time.season"]).sum())
    prec_season_df = (
        prec_seasonal
        .to_dataframe(name="precipitation")
        .reset_index()
    )
    
    # ============================
    # MERGE
    # ============================
    
    one_seasonal_df = temp_season_df.merge(
        prec_season_df,
        on=["season", "number", "latitude", "longitude"],
        how="left"
    )
    
    one_seasonal_df["polygon"] = polygon_name
    one_seasonal_df["fire_date"] = date_fire
    
    results4.append(one_seasonal_df) 

        

df_season_per_year = pd.concat(results3, ignore_index=True)
df_season_one_year = pd.concat(results4, ignore_index=True)

print(len(df_season_per_year.polygon.unique()))
print(len(df_season_one_year.polygon.unique()))

new_path = Path(path_to_save)
csv_filename = "temp_prec_5_year_seasons.csv"
df_season_per_year.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f")   

new_path = Path(path_to_save)
csv_filename = "temp_prec_5_year_seasons_average_sum.csv"
df_season_one_year.to_csv(new_path / csv_filename, index=False,sep=";", float_format="%.3f") 
  
    
