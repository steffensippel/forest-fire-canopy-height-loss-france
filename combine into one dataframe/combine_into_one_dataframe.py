# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 08:29:53 2026

@author: steff
"""
# Load the continous data per patch: 
    
# clean the columns for the analysis

# IMPORT PACKAGES 

import pandas as pd 
from matplotlib import pyplot as plt 
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
import math 

# FILENAMES 
file_biodiversity_genus = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\biodiversity_genus\biodiversity_indices_genus.csv"

file_distance_to_edge = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\distance_to_edge\distance_to_edge.csv"

file_distance_to_road = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\distance_to_road\distance_to_road.csv"

file_dNBR = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\dNBR\dNBR.csv"

# === SOIL ===
file_ph = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\soil_properties\ph.csv"

file_reserve_utile = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\soil_properties\reserve_utile.csv"

file_topographic_wetness_index = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\soil_properties\topographic_wetness_index.csv"

#  === TOPOGRAPHY ===
file_altitude = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\topography\altitude.csv"

file_aspect_cos =  r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\topography\aspect_cos.csv"

file_aspect_sin = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\topography\aspect_sin.csv"

file_slope = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\topography\slope.csv"

# CATEGORICAL 
file_management_regimes = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\management_regimes\management_class.csv"

file_ownership_parc_reserve = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\ownership_parc_reserve\ownership_parc_reserve.csv"

# TEMPERATURE AND PRECIPITATION 
file_temp_prec_30_days_around_fire = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\temperature_precipitation\temp_prec_30_days_around_fire.csv"
file_temp_prec_5_year_seasons = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\temperature_precipitation\temp_prec_5_year_seasons.csv"
file_temp_prec_5_year_season_average = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\temperature_precipitation\temp_prec_5_year_seasons_average_sum.csv"

# GENERAL POLYGON INFORMATION (GRECO; CODE SER)
file_general_polygon = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\polygon_level_information\polygon_level_info.csv"

# SIZE AND SHAPE OF POLYGONS 
file_size_shape_polygons = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\polygon_shapes\polygon_shape.csv"

# === to be predicted ===

file_pipeline_output = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\output"


# %%
# ===LOAD TO BE PREDICTED===
from pathlib import Path
import pandas as pd

# Folder containing the CSV files
folder = Path(r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\output")

# Find all CSV files
csv_files = folder.glob("*.csv")

# Read all CSVs into a list of DataFrames
dfs = [pd.read_csv(file, sep=";", encoding="utf-8-sig") for file in csv_files]

# Concatenate them
df = pd.concat(dfs, ignore_index=True)
df = df.rename(columns = {'patch_index': 'patch_id'})
print(df.shape)
print(df.head())
print(df.columns)

# forest cover threshold for the consideration in the analysis: 
forest_cover_threshold = 0.1

df_loss = df[['patch_id', 'polygon', 'num_years_after_fire', 'forest_cover', 'year_diff', 'pixels_loss>5m', 'pixels_loss>3m', 'relative_loss>5m','relative_loss>3m', 'relative_loss_>25%', 'relative_loss_>50%', 'relative_loss_>75%']]
df_loss = df_loss[df_loss.forest_cover > forest_cover_threshold]
df_loss = df_loss.drop(columns = ["forest_cover"])

df_loss_year0 = df_loss[df_loss.num_years_after_fire == 0]
df_loss_year1 = df_loss[df_loss.num_years_after_fire == 1]
df_loss_year2 = df_loss[df_loss.num_years_after_fire == 2]
df_loss_year3 = df_loss[df_loss.num_years_after_fire == 3]
df_loss_year4 = df_loss[df_loss.num_years_after_fire == 4]

polygons = df['polygon'].unique()
print(len(polygons))

print(len(df_loss_year0))

# Predictors: 
# === HEIGHT PRE FIRE ===
# these variables are also year dependent! (do we want that?)

# for now we ignore the height dynamics for later years! 
# === HEIGHT ===
df_height_all_years = df[['patch_id', 'polygon', 'num_years_after_fire', 'height_no_filter_mean', 'height_no_filter_std',
    'height_no_filter_q05', 'height_no_filter_q25', 'height_no_filter_q50',
    'height_no_filter_q75', 'height_no_filter_q95',
    'height_no_filter_coefficient_of_variation', 'height_above_5m_mean',
    'height_above_5m_std', 'height_above_5m_q05', 'height_above_5m_q25',
    'height_above_5m_q50', 'height_above_5m_q75', 'height_above_5m_q95',
    'height_above_5m_coefficient_of_variation']]

df_height_pre_fire = df_height_all_years[df_height_all_years.num_years_after_fire == 0]
df_height_pre_fire = df_height_pre_fire.drop(columns = ['num_years_after_fire'])

# === TREE COVER ====
df_tree_cover = df[['patch_id','polygon','num_years_after_fire', 'forest_cover', 'edge_density', 'tree_cover', 'LPI_forest', 'LPI_nonforest']]
df_tree_cover = df_tree_cover[df_tree_cover.num_years_after_fire == 0]
df_tree_cover = df_tree_cover.drop(columns = ['num_years_after_fire'])
print(len(df_tree_cover))

# === TREE SPECIES ===
df_tree_species = df[['patch_id', 'polygon','num_years_after_fire', 'tfv_num', 'forest_type', 'broad_forest_type']]
df_tree_species = df_tree_species[df_tree_species.num_years_after_fire == 0]
df_tree_species = df_tree_species.drop(columns = ['num_years_after_fire'])
df_tree_species.loc[df_tree_species["forest_type"] == "Just cut","broad_forest_type"] = 'Mixed deciduous'

print(len(df_tree_species))


# === GENERAL POLYGON INFORMATION ON POLYGON LEVEL ===
# === SER, GRECO, LOCATION ===
df_greco_ser_location = pd.read_csv(file_general_polygon, sep = ";", encoding = "utf-8-sig")
df_greco_ser_location = df_greco_ser_location[df_greco_ser_location['Polygon_ID'].isin(polygons)]
print(df_greco_ser_location.columns)
df_greco_ser_location = df_greco_ser_location[['Polygon_ID', 'departement', 'code_insee', 'sylvoecoregion', 'sylvo_letter','greco_name']]
df_greco_ser_location = df_greco_ser_location.rename(columns=  {"Polygon_ID": "polygon"})

import ast
df_greco_ser_location["sylvoecoregion"] = (
    df_greco_ser_location["sylvoecoregion"]
    .apply(lambda x: ast.literal_eval(x)[0] if isinstance(x, str) and x.startswith("[") else x)
)
print(df_greco_ser_location['sylvoecoregion'].unique())

# === TIME INFORMATION ===
df_month_year = df[df['num_years_after_fire'] == 0]
df_month_year = df_month_year[["polygon",  'fire_date', 'year_pre_fire']]
df_month_year = df_month_year.drop_duplicates()
# Convert to datetime
df_month_year["fire_date"] = pd.to_datetime(df_month_year["fire_date"])

# Extract year and month
df_month_year["fire_year"] = df_month_year["fire_date"].dt.year
df_month_year["fire_month"] = df_month_year["fire_date"].dt.month

print(len(df_month_year))

# === POLYGON SHAPE AND SIZE ===
df_polygon_size_shape = pd.read_csv(file_size_shape_polygons, sep = ";", encoding = "utf-8-sig")
print(df_polygon_size_shape.columns)
print(len(df_polygon_size_shape))
df_polygon_size_shape = df_polygon_size_shape.rename(columns = {"edge_density": "edge_density_polygon"})

# === POLYGON LOCATION === 
df_lat_lon = pd.read_csv(file_temp_prec_5_year_seasons, sep = ";", encoding = "utf-8-sig") 
print(df_lat_lon.columns)
df_lat_lon = df_lat_lon[["polygon", "latitude", "longitude"]]
df_lat_lon = df_lat_lon.drop_duplicates(subset="polygon", keep="first")
print(len(df_lat_lon))

# change JUST CUT in the broad forest category of "mixed deciduous"

#%%
# ===== ON 1 HA AREA SCALE =====

# CONTINOUS

# ===LOAD PREDICTORS===
# load files and clean the column names. Filter for only the columns we would like to include in the analysis, then merge everything throught the patch index and plot the correlations
# === BIODIVERSITY === 
df_biodiversity_genus = pd.read_csv(file_biodiversity_genus, sep = ";", encoding = "utf-8-sig")
print(df_biodiversity_genus.columns)
df_biodiversity_genus = df_biodiversity_genus[['patch_id', 'polygon', 'richness_index', 'shannon_index', 'berger_parker_index','tree_coverage']]

# === DISTANCE TO EDGE ===
df_distance_to_edge = pd.read_csv(file_distance_to_edge, sep = ";", encoding = "utf-8-sig")
print(df_distance_to_edge.columns)
df_distance_to_edge = df_distance_to_edge[['patch_id', 'polygon','distance_to_edge', 'distance_to_outer_edge']]

# === DISTANCE TO ROAD ===
df_distance_to_road = pd.read_csv(file_distance_to_road, sep = ";", encoding = "utf-8-sig")
print(df_distance_to_road.columns)
# rename columns: 
df_distance_to_road = df_distance_to_road.rename(columns = {"min": "min_distance_to_road", "median": "median_distance_to_road"})
df_distance_to_road = df_distance_to_road[['patch_id', 'polygon','min_distance_to_road', 'median_distance_to_road']]

# === dNBR ===
df_dNBR = pd.read_csv(file_dNBR, sep = ";", encoding = "utf-8-sig")
print(df_dNBR.columns)
df_dNBR = df_dNBR[['patch_id', 'polygon', 'dnbr_mean','dnbr_std', 'dnbr_q05', 'dnbr_q25', 'dnbr_q50', 'dnbr_q75', 'dnbr_q95','dnbr_coefficient_of_variation']]
print(np.max(df_dNBR.dnbr_coefficient_of_variation))
# === PH ===
df_ph = pd.read_csv(file_ph, sep = ";", encoding = "utf-8-sig")
print(df_ph.columns) 
df_ph = df_ph[['patch_id', 'polygon','ph_value']]
df_ph.loc[df_ph.ph_value < 0, 'ph_value'] = np.nan


# === RESERVE_UTILE ===
df_reserve_utile = pd.read_csv(file_reserve_utile, sep = ";", encoding = "utf-8-sig")
print(df_reserve_utile.columns)
df_reserve_utile = df_reserve_utile.rename(columns = {"min": "min_reserve_utile", "max": "max_reserve_utile", "mean": "mean_reserve_utile"})
df_reserve_utile = df_reserve_utile[["patch_id", "polygon","min_reserve_utile", "max_reserve_utile", "mean_reserve_utile"]]

# === TOPOGRAPHIC WETNESS INDEX  ===
df_tpi = pd.read_csv(file_topographic_wetness_index, sep = ";", encoding = "utf-8-sig")
print(df_tpi.columns) 
df_tpi = df_tpi.rename(columns = {"mean": "mean_topographic_wetness"})
df_tpi = df_tpi[['patch_id', 'polygon','mean_topographic_wetness']]

# === ALTITUDE  ===
df_altitude = pd.read_csv(file_altitude, sep = ";", encoding = "utf-8-sig")
print(df_altitude.columns) 
df_altitude = df_altitude.rename(columns = {"altitude_min": "min_altitude", "altitude_max": "max_altitude", "altitude_mean": "mean_altitude", "altitude_std": "std_altitude", "altitude_median": "median_altitude", "altitude_q25": "q25_altitude", "altitude_q75": "q75_altitude", "altitude_q95": "q95_altitude"})
df_altitude = df_altitude[['patch_id', 'polygon','min_altitude', 'max_altitude', 'mean_altitude', 'std_altitude', 'median_altitude', 'q25_altitude', 'q75_altitude','q95_altitude']]

# === ASPECT_COS ===
df_aspect_cos = pd.read_csv(file_aspect_cos, sep = ";", encoding = "utf-8-sig")
print(df_aspect_cos.columns)
df_aspect_cos = df_aspect_cos[['patch_id', 'polygon','aspect_cos_min', 'aspect_cos_max', 'aspect_cos_mean', 'aspect_cos_count', 'aspect_cos_std', 'aspect_cos_median','aspect_cos_q25', 'aspect_cos_q75', 'aspect_cos_q95']]

# === ASPECT_SIN === 
df_aspect_sin = pd.read_csv(file_aspect_sin, sep = ";", encoding = "utf-8-sig")
print(df_aspect_sin.columns)
df_aspect_sin = df_aspect_sin[['patch_id', 'polygon','aspect_sin_min', 'aspect_sin_max', 'aspect_sin_mean', 'aspect_sin_count', 'aspect_sin_std', 'aspect_sin_median','aspect_sin_q25', 'aspect_sin_q75', 'aspect_sin_q95']]

# === SLOPE === 
df_slope = pd.read_csv(file_slope, sep = ";", encoding = "utf-8-sig")
print(df_slope.columns)
df_slope = df_slope[['patch_id', 'polygon','slope_min', 'slope_max', 'slope_mean', 'slope_count', 'slope_std', 'slope_median','slope_q25', 'slope_q75', 'slope_q95']]

# CATEGORICAL 
# === MANAGEMENT REGIMES ===
df_management_regimes = pd.read_csv(file_management_regimes, sep = ";", encoding = "utf-8-sig")
print(df_management_regimes.columns)
df_management_regimes = df_management_regimes[['patch_id', 'polygon','management_class', 'management_type']]

# === OWNERSHIP / NATURAL PARC ===
df_ownership_parc_reserve = pd.read_csv(file_ownership_parc_reserve, sep = ";", encoding = "utf-8-sig")
print(df_ownership_parc_reserve.columns)
df_ownership_parc_reserve = df_ownership_parc_reserve[['patch_id', 'polygon','relative_public', 'ownership_broad',
       'ownership_specific', 'regional_ownership', 'relative_parc_reserve',
       'parc_ou_reserve_broad', 'parc_reserve_specific',
       'regional_parc_reserve']]
df_ownership_parc_reserve = df_ownership_parc_reserve.drop_duplicates()
print(len(df_ownership_parc_reserve))

# for the remaining duplicates: 1 ha area is intersecting with two categories. For simplicity just pick first one 
df_ownership_parc_reserve = df_ownership_parc_reserve.drop_duplicates(subset="patch_id", keep="first")
print(len(df_ownership_parc_reserve))


# ===== DATA ON POLYGON LEVEL =====
# Precipitation and Temperature 30 days around fire
df_temp_prec = pd.read_csv(file_temp_prec_30_days_around_fire, sep = ";", encoding = "utf-8-sig")
print(df_temp_prec.columns)  
df_temp_prec = df_temp_prec[['polygon_id', 'mean_temp_before_fire',
       'mean_temp_after_fire', 'num_days_above_30_before',
       'num_days_above_30_after', 'sum_prec_before_fire',
       'sum_prec_after_fire']]
df_temp_prec = df_temp_prec.rename(columns = {"polygon_id": "polygon", "mean_temp_before_fire": "temp30_before",
        "mean_temp_after_fire": "temp30_after",
        "num_days_above_30_before": "days30_before",
        "num_days_above_30_after": "days30_after",
        "sum_prec_before_fire": "prec30_before",
        "sum_prec_after_fire": "prec30_after"})

# Encode the different seasons in columns, to still have one value per polygon patch! 
# Precipitation and Temperature seasonal values 
# For now only look at the first year (the year within which the fire happened)

df_temp_prec_seasons = pd.read_csv(file_temp_prec_5_year_seasons, sep = ";", encoding = "utf-8-sig") 
print(df_temp_prec_seasons.columns)
df_temp_prec_seasons = df_temp_prec_seasons[['polygon','season_year', 'season',
       'temperature', 'precipitation']]
df_temp_prec_seasons["year_num"] = df_temp_prec_seasons.groupby("polygon")["season_year"].transform(lambda x: x.rank(method="dense").astype(int) - 1)
df_temp_prec_seasons = df_temp_prec_seasons[df_temp_prec_seasons["year_num"].isin([0,1])]

# pivot on season and year_num
df_temp_prec_seasons["seasonal_year"] = df_temp_prec_seasons["season"] + "_" + df_temp_prec_seasons["year_num"].astype(str)

df_temp_prec_seasons = df_temp_prec_seasons.pivot_table(
    index="polygon",
    columns="seasonal_year",
    values=["precipitation", "temperature"]
).reset_index()

df_temp_prec_seasons.columns = [
    col if isinstance(col, str)
    else f"{col[1]}_{col[0]}"
    for col in df_temp_prec_seasons.columns
]

df_temp_prec_seasons = df_temp_prec_seasons.rename(columns = {"_polygon": "polygon"})

df_temp_prec_seasons = df_temp_prec_seasons[['polygon', 'DJF_0_precipitation', 'MAM_0_precipitation',  'JJA_0_precipitation', 'SON_0_precipitation', 
       'DJF_1_precipitation', 'MAM_1_precipitation','JJA_1_precipitation', 'SON_1_precipitation',
       'DJF_0_temperature', 'MAM_0_temperature', 'JJA_0_temperature', 'SON_0_temperature', 
       'DJF_1_temperature', 'MAM_1_temperature', 'JJA_1_temperature', 'SON_1_temperature']]

print(df_temp_prec_seasons.columns)

# === Precipitation and Temperature seasonal values compressed into one ===
df_temp_prec_season_compressed = pd.read_csv(file_temp_prec_5_year_season_average, sep = ";", encoding = "utf-8-sig")
print(df_temp_prec_season_compressed.columns)
df_temp_prec_season_compressed = df_temp_prec_season_compressed[['polygon','season','temperature',
       'precipitation']]

df_temp_prec_season_compressed = df_temp_prec_season_compressed.pivot_table(
    index="polygon",
    columns="season",
    values=["precipitation", "temperature"]
).reset_index()

# flatten columns properly
df_temp_prec_season_compressed.columns = [
    col if isinstance(col, str) else f"{col[1]}_{col[0]}"
    for col in df_temp_prec_season_compressed.columns
]

df_temp_prec_season_compressed = df_temp_prec_season_compressed.rename(columns = {"_polygon": "polygon"})

df_temp_prec_season_compressed = df_temp_prec_season_compressed[['polygon', 'DJF_precipitation', 'MAM_precipitation','JJA_precipitation',
        'SON_precipitation', 'DJF_temperature', 'MAM_temperature','JJA_temperature',  'SON_temperature']]

print(df_temp_prec_season_compressed.columns)
#%%
from functools import reduce

# ==== CONTINUOUS DATA ====
# Merge all the predicting data continous on 1ha area level  
df_continuous = [
    df_biodiversity_genus,
    df_distance_to_edge,
    df_distance_to_road,
    df_dNBR,
    df_ph,
    df_reserve_utile,
    df_tpi,
    df_altitude,
    df_aspect_cos,
    df_aspect_sin,
    df_slope, 
    df_height_pre_fire, 
    df_tree_cover
]


print(len(df_altitude))
# ==== CATEGORICAL DATA ====
# Merge predicting data, categorical on 1 ha area level 
df_categorical = [df_management_regimes, df_ownership_parc_reserve, df_tree_species]

print(len(df_management_regimes), len(df_ownership_parc_reserve), len(df_tree_species))

# ==== POLYGON LEVEL DATA ====
# Polygon level information 
dfs_polygon_level = [df_greco_ser_location, df_month_year, df_polygon_size_shape, df_temp_prec,  df_temp_prec_season_compressed, df_temp_prec_seasons, df_lat_lon]
df_polygon_info = reduce(
    lambda left, right: pd.merge(left, right, on="polygon", how="left"),
    dfs_polygon_level
)

print(len(df_polygon_info))


dfs = df_continuous + df_categorical 


df_merged = reduce(
    lambda left, right: pd.merge(left, right, on=["patch_id", "polygon"], how="outer"),
    dfs
)

print(len(df_merged))

df_final = df_merged.merge(df_polygon_info, on="polygon", how="left")
print(len(df_final))

#%% PLOT THE DISTRIBUTIONS OF THE DIFFERENT DATA: 
print(df_final.columns)
# group into categories. And: choose what variables to use! 

biodiversity = ['richness_index', 'shannon_index', 'berger_parker_index',
       'tree_coverage']

distance = ['distance_to_edge', 'distance_to_outer_edge',
            'min_distance_to_road', 'median_distance_to_road']

dnbr = ['dnbr_mean', 'dnbr_std', 'dnbr_q05', 'dnbr_q25', 'dnbr_q50', 'dnbr_q75',
'dnbr_q95', 'dnbr_coefficient_of_variation']


soil = ['ph_value',
'min_reserve_utile', 'max_reserve_utile', 'mean_reserve_utile',
'mean_topographic_wetness']


# we can already reduce the topography variables: 
topography_altitude_slope = ['min_altitude', 'max_altitude',
'mean_altitude', 'std_altitude', 'median_altitude', 'q25_altitude', 'q95_altitude', 'slope_min',
'slope_max', 'slope_mean', 'slope_std', 'slope_median',
'slope_q25', 'slope_q95']

topography_aspect = ['aspect_cos_min', 'aspect_cos_max',
'aspect_cos_mean', 'aspect_cos_std',
'aspect_cos_median', 'aspect_cos_q25', 'aspect_cos_q75',
'aspect_cos_q95', 'aspect_sin_min', 'aspect_sin_max', 'aspect_sin_mean', 'aspect_sin_std', 'aspect_sin_median',
'aspect_sin_q25', 'aspect_sin_q75', 'aspect_sin_q95']


height = ['height_no_filter_mean', 'height_no_filter_std', 'height_no_filter_q05',
'height_no_filter_q25', 'height_no_filter_q50', 'height_no_filter_q75',
'height_no_filter_q95', 'height_no_filter_coefficient_of_variation',
'height_above_5m_mean', 'height_above_5m_std', 'height_above_5m_q05',
'height_above_5m_q25', 'height_above_5m_q50', 'height_above_5m_q75',
'height_above_5m_q95', 'height_above_5m_coefficient_of_variation']


tree_cover = ['edge_density', 'tree_cover', 'LPI_forest',
'LPI_nonforest']



# Categorical data 
management_classes = ["management_class", "management_type"]

ownership_parc_reserve_classes = ["ownership_broad", "ownership_specific", "parc_ou_reserve_broad", "parc_reserve_specific"]


tree_species = ["tfv_num", "forest_type", "broad_forest_type"]



temperature_precipitation_classes_one_season = ['DJF_precipitation', 'MAM_precipitation',
       'JJA_precipitation', 'SON_precipitation', 'DJF_temperature',
       'MAM_temperature', 'JJA_temperature', 'SON_temperature'] 

temperature_precipitation_classes_multiple_seasons = [ 'DJF_0_precipitation', 'MAM_0_precipitation',
       'JJA_0_precipitation', 'SON_0_precipitation', 'DJF_1_precipitation',
       'MAM_1_precipitation', 'JJA_1_precipitation', 'SON_1_precipitation',
       'DJF_0_temperature', 'MAM_0_temperature', 'JJA_0_temperature',
       'SON_0_temperature', 'DJF_1_temperature', 'MAM_1_temperature',
       'JJA_1_temperature', 'SON_1_temperature']

temp_prec = ["temp30_before", "temp30_after", "days30_before", "days30_after", "prec30_before", "prec30_after"]


# %% First look at prediction of year 0: 

df_predict_year0 = pd.merge(df_loss_year0, df_final, how = 'left' , on = ["patch_id", "polygon"])
print(len(df_predict_year0))
print(df_predict_year0.columns)

to_predict = ['relative_loss>5m',
'relative_loss>3m', 'relative_loss_>25%', 'relative_loss_>50%',
'relative_loss_>75%' ]

#%%

# STEP 1: Plot the distributions of my data: 

def plot_category_histograms(df, variables, title):
    # Keep only variables that actually exist in the dataframe
    variables = [v for v in variables if v in df.columns]

    melted = df[variables].melt(
        var_name="Variable",
        value_name="Value"
    )

    g = sns.FacetGrid(
        melted,
        col="Variable",
        col_wrap=4,
        sharex=False,
        sharey=False,
        height=3.5
    )

    g.map_dataframe(
        sns.histplot,
        x="Value",
        bins=30
    )

    g.set_titles("{col_name}")
    g.set_axis_labels("", "Count")
    g.figure.suptitle(title, fontsize=16)
    g.figure.tight_layout()
    g.figure.subplots_adjust(top=0.9)

    plt.show()
    
# for the polygon_level data only plot data point once per polygon (otherwise the huge fire polygon will be dominating the visual!!)
def plot_category_histograms_polygon(df, variables, title):
    # Keep only one row per polygon
    df_polygon = df.drop_duplicates(subset="polygon", keep="first")

    # Keep only variables that actually exist
    variables = [v for v in variables if v in df_polygon.columns]

    melted = df_polygon[variables].melt(
        var_name="Variable",
        value_name="Value"
    )

    g = sns.FacetGrid(
        melted,
        col="Variable",
        col_wrap=4,
        sharex=False,
        sharey=False,
        height=3.5
    )

    g.map_dataframe(
        sns.histplot,
        x="Value",
        bins=30
    )

    g.set_titles("{col_name}")
    g.set_axis_labels("", "Count")
    g.figure.suptitle(title, fontsize=16)
    
    g.figure.tight_layout(rect=[0, 0, 1, 0.92])
    g.figure.suptitle(title, fontsize=16)

    plt.show()
    
def plot_category_countplots(df, variables, title):
    # Keep only one row per polygon
    df_polygon = df

    # Keep only variables that exist
    variables = [v for v in variables if v in df_polygon.columns]

    melted = df_polygon[variables].melt(
        var_name="Variable",
        value_name="Category"
    )

    g = sns.FacetGrid(
        melted,
        col="Variable",
        col_wrap=4,
        sharex=False,
        sharey=False,
        height=3.5
    )

    g.map_dataframe(
        sns.countplot,
        x="Category",
        order=None
    )

    # Rotate category labels (different numbers of categories)
    for ax in g.axes.flat:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor", fontsize = 6)

    g.set_titles("{col_name}")
    g.set_axis_labels("", "Count")

    g.figure.tight_layout(rect=[0, 0, 1, 0.92])
    g.figure.suptitle(title, fontsize=16)

    plt.show()
    

def plot_category_countplots_polygon(df, variables, title):
    # Keep only one row per polygon
    df_polygon = df.drop_duplicates(subset="polygon", keep="first")

    # Keep only variables that exist
    variables = [v for v in variables if v in df_polygon.columns]

    melted = df_polygon[variables].melt(
        var_name="Variable",
        value_name="Category"
    )

    g = sns.FacetGrid(
        melted,
        col="Variable",
        col_wrap=4,
        sharex=False,
        sharey=False,
        height=3.5
    )

    g.map_dataframe(
        sns.countplot,
        x="Category",
        order=None
    )

    # Rotate category labels (different numbers of categories)
    for ax in g.axes.flat:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor", fontsize = 6)

    g.set_titles("{col_name}")
    g.set_axis_labels("", "Count")

    g.figure.tight_layout(rect=[0, 0, 1, 0.92])
    g.figure.suptitle(title, fontsize=16)

    plt.show()
    
# plot the heat correlation map
def plot_correlation_heatmap(df, predictors, targets, title):
    """
    Plot a correlation heatmap for selected predictors and one target.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    predictors : list of str
        Predictor column names.
    target : str
        Target column name.
    title : str
        Figure title.
    """

    # Keep only columns that exist
    predictors = [col for col in predictors if col in df.columns]

    targets = [col for col in targets if col in df.columns]

    cols = predictors + targets

    corr = df[cols].corr(numeric_only=True)

    plt.figure(figsize=(max(6, len(cols)), max(5, len(cols))))

    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        vmin=-1,
        vmax=1, 
        cbar = False
    )

    plt.title(title, fontsize = 25)
    plt.tight_layout()
    plt.show()
    
# this only looks at the data where treecover is >0.1
plot_category_histograms(df_predict_year0, to_predict, "Heigth Loss Metric")
plot_category_histograms(df_predict_year0, biodiversity, "Biodiversity")
plot_category_histograms(df_predict_year0, distance, "Distance")
plot_category_histograms(df_predict_year0, dnbr, "dNBR")
plot_category_histograms(df_predict_year0, soil, "Soil")
plot_category_histograms(df_predict_year0, height, "Height")
plot_category_histograms(df_predict_year0, tree_cover, "Tree cover")
plot_category_histograms(df_predict_year0, topography_altitude_slope, "Topography: Slope, Altitude")  
plot_category_histograms(df_predict_year0, topography_aspect, "Topography: Aspect")

# polygon level 
plot_category_histograms_polygon(df_predict_year0, temp_prec, "30 days before after: temperature, precipitation")
plot_category_histograms_polygon(df_predict_year0, temperature_precipitation_classes_one_season, "seasonal average: temperature precipitation")
plot_category_histograms_polygon(df_predict_year0, temperature_precipitation_classes_multiple_seasons, "individual seasons: temperature precipitation")
#plot_category_histograms_polygon(df_predict_year0, polygon_area_shape, "Polygon Shape") 

# categorical data
plot_category_countplots(df_predict_year0, ownership_parc_reserve_classes, 'Ownership / Natural Parc type')
plot_category_countplots(df_predict_year0, management_classes, 'Management class')
plot_category_countplots(df_predict_year0, tree_species, "Tree species")

# categorical data on polygon level 
#plot_category_countplots_polygon(df_predict_year0, location, 'Location')
#plot_category_countplots_polygon(df_predict_year0, date, "Date")

#%%
# First look correlation plots: this we can only do for continuous data: 

# Regroup the categories: 
    
 
# plot the correlation maps for continous patch level data
plot_correlation_heatmap(df_predict_year0, biodiversity,to_predict, "Biodiversity")
plot_correlation_heatmap(df_predict_year0, distance ,to_predict, "Distance")
plot_correlation_heatmap(df_predict_year0, dnbr ,to_predict, "dNBR")
plot_correlation_heatmap(df_predict_year0, soil ,to_predict, "Soil")
plot_correlation_heatmap(df_predict_year0, height ,to_predict, "Height")
plot_correlation_heatmap(df_predict_year0, tree_cover ,to_predict, "Tree Cover")
plot_correlation_heatmap(df_predict_year0, topography_altitude_slope ,to_predict, "Topography: Slope_Altitude")
plot_correlation_heatmap(df_predict_year0, topography_aspect ,to_predict, "Topography: Aspect")

# plot the correlation maps for continous polygon level data
plot_correlation_heatmap(df_predict_year0, polygon_area_shape, to_predict, "Fire Polygon Shape")
plot_correlation_heatmap(df_predict_year0, temp_prec,to_predict, "30 days before after: temperature, precipitation")
plot_correlation_heatmap(df_predict_year0, temperature_precipitation_classes_one_season ,to_predict, "seasonal average: temperature precipitation")
plot_correlation_heatmap(df_predict_year0, temperature_precipitation_classes_multiple_seasons, to_predict, "individual seasons: temperature precipitation")

# %% From this: reduced columns: 
    
# REDUCE THE COLUMNS TO CONSIDER IN THE ANALYSIS 

biodiversity = ['richness_index', 'shannon_index', 'berger_parker_index',
       'tree_coverage']

distance = ['distance_to_edge', 'distance_to_outer_edge',
            'min_distance_to_road']

dnbr = ['dnbr_mean', 'dnbr_std', 'dnbr_coefficient_of_variation']


soil = ['ph_value', 'mean_reserve_utile','mean_topographic_wetness']


# we can already reduce the topography variables: 
topography_altitude_slope = ['mean_altitude', 'std_altitude',  'slope_mean', 'slope_std']

topography_aspect = ['aspect_cos_min',
'aspect_cos_mean', 'aspect_cos_std',
'aspect_cos_q95', 'aspect_sin_min', 'aspect_sin_mean', 'aspect_sin_std', 'aspect_sin_q95']


height = ['height_no_filter_mean', 'height_no_filter_std', 'height_no_filter_q05',
'height_no_filter_q95', 'height_no_filter_coefficient_of_variation']


tree_cover = ['edge_density', 'tree_cover']

# Categorical data 
management_classes = ["management_class", "management_type"]

ownership_parc_reserve_classes = ["ownership_broad", "ownership_specific", "parc_ou_reserve_broad", "parc_reserve_specific"]


tree_species = ["tfv_num", "forest_type", "broad_forest_type"]

location = ["departement", "code_insee", "sylvoecoregion", "sylvo_letter", "greco_name", "latitude", "longitude"]

date = ["fire_year", "fire_month"]


#  Continous data on polygon level 
polygon_area_shape = ["area_ha", "edge_length", "edge_density_polygon", "landscape_shape_index"]

temperature_precipitation_classes_one_season = ['DJF_precipitation', 'MAM_precipitation',
       'JJA_precipitation', 'SON_precipitation', 'DJF_temperature',
       'MAM_temperature', 'JJA_temperature', 'SON_temperature'] 


temp_prec = ["temp30_before", "temp30_after", "days30_before", "days30_after", "prec30_before", "prec30_after"] 


columns_to_keep = ["patch_id", "polygon"] + to_predict + biodiversity + distance + dnbr + soil + topography_altitude_slope + topography_aspect + height + tree_cover + management_classes + ownership_parc_reserve_classes + tree_species + location + date + polygon_area_shape + temperature_precipitation_classes_one_season + temp_prec

# filter for the columns we decide to keep 
df_model = df_predict_year0[columns_to_keep]

# save this as csv file: 
df_model.to_csv(r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\predictor_target_reduced.csv", sep=";", encoding="utf-8-sig")

#%%
reduced_predictors = biodiversity + distance + dnbr + soil + topography_altitude_slope + topography_aspect + height + tree_cover 
plot_correlation_heatmap(df_predict_year0, reduced_predictors,to_predict, "Reduced Predictors")

#%%
# Function 1: continuous data 
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import pandas as pd
import pandas as pd


def compute_metrics(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    r2 = r2_score(y, x)
    mae = mean_absolute_error(y, x)

    return r2, mae

def hexbin_grid(df, predictors, target, title, gridsize=40, cmap="viridis", bins="log"):
    
    ncols = 4
    nrows = math.ceil(len(predictors) / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(4*ncols, 4*nrows))
  
    axes = np.array(axes).reshape(-1)  # flatten even if 1 row

    fig.subplots_adjust(
        left=0.08,
        right=0.6,
        bottom=0.08,
        top=0.92,
        wspace=0.35,
        hspace=0.35,
    )
    

    y = np.asarray(df[target], dtype=float)
    y_mask = np.isfinite(y)

    for i, var in enumerate(predictors):
        ax = axes[i]

        x = np.asarray(df[var], dtype=float)

        mask = np.isfinite(x) & y_mask
        x_clean = x[mask]
        y_clean = y[mask]

        hb = ax.hexbin(
            x_clean, y_clean,
            gridsize=gridsize,
            cmap=cmap,
            bins=bins,
            mincnt=1
        )

        #ax.set_title(var)
        ax.set_xlabel(var)
        ax.set_ylabel(target)
        
        '''
        # ---- METRICS ----
        r2, mae = compute_metrics(x, y)

        ax.text(
            0.05, 0.95,
            f"$R^2$ = {r2:.2f}\nMAE = {mae:.2f}",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
        )
        '''


    # turn off unused axes
    for j in range(len(predictors), len(axes)):
        axes[j].axis("off")

    
    # Add one shared colorbar
    # [left, bottom, width, height] in figure coordinates
    cax = fig.add_axes([0.99, 0.15, 0.001, 0.70])
    
    cbar = fig.colorbar(hb, cax=cax)
    cbar.set_label("log10(Number of observations)")
    
    '''
    # single shared colorbar
    cbar = fig.colorbar(hb, ax=axes.tolist(), shrink=0.8)
    cbar.set_label("log10(count)")
    '''
    fig.suptitle(
        f"{title} vs. {target}",
        fontsize=18,
        fontweight="bold"
    )
    plt.tight_layout()
    return fig, axes

hexbin_grid(df_predict_year0, topography_altitude_slope, 'relative_loss>5m', "Topography: altitude and slope")
hexbin_grid(df_predict_year0, temp_prec, 'relative_loss>5m', "Temperature, precipitation")
hexbin_grid(df_predict_year0, distance, 'relative_loss>5m', "distance")
hexbin_grid(df_predict_year0, biodiversity, 'relative_loss>5m', "Biodiversity")
hexbin_grid(df_predict_year0, dnbr, 'relative_loss>5m', "dNBR")
hexbin_grid(df_predict_year0, topography_aspect, 'relative_loss>5m', "Topography: Aspect")
hexbin_grid(df_predict_year0, height, 'relative_loss>5m', "Pre-fire height")
hexbin_grid(df_predict_year0, tree_cover, 'relative_loss>5m', "Tree cover")
hexbin_grid(df_predict_year0, polygon_area_shape, 'relative_loss>5m', "Fire polygon shape")

#%%
# Plot boxplot overviews for the categorical data 

def boxplot_grid(df, predictors, target, title):
    
    n = 0
    ncols = 4
    nrows = math.ceil(len(predictors) / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(4*ncols, 4*nrows))
    axes = np.array(axes).reshape(-1)

    fig.subplots_adjust(
        left=0.08,
        right=0.97,
        bottom=0.08,
        top=0.92,
        wspace=0.35,
        hspace=0.5,
    )

    y = np.asarray(df[target], dtype=float)

    for i, var in enumerate(predictors):
        ax = axes[i]
        

        # Keep only finite target values
        mask = np.isfinite(y)
        data = df.loc[mask, [var, target]].dropna()

        # Get categories
        categories = sorted(data[var].unique())

        # Collect target values for each category
        values = [
            data.loc[data[var] == cat, target].values
            for cat in categories
        ]
        

        bp = ax.boxplot(
                values,
                tick_labels=categories,
                showfliers=False,      # optional
                patch_artist=True       # optional
            )
        
        for k, vals in enumerate(values):
        
            n = len(vals)
        
            # Get the top whisker position from matplotlib
            upper_whisker_line = bp["whiskers"][2 * k + 1]
            y_pos = upper_whisker_line.get_ydata()[1]
        
            ax.text(
                k + 1,
                y_pos,
                f"{n}",
                ha="center",
                va="bottom",
                fontsize=5
            )
               
        
        ax.set_xlabel(var)
        ax.set_ylabel(target)

        # Rotate labels if there are many categories
        #ax.tick_params(axis='x', rotation=45)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor", fontsize = 6)
        
        
    #for ax in g.axes.flat:
       


    # Remove unused axes
    for j in range(len(predictors), len(axes)):
        axes[j].axis("off")

    fig.suptitle(
        f"{title} vs. {target}",
        fontsize=18,
        fontweight="bold"
    )

    plt.tight_layout()

    return fig, axes


fig, axes = boxplot_grid(
    df_predict_year0,
    tree_species,
    target='relative_loss>5m',
    title="Tree Species"
)

fig, axes = boxplot_grid(
    df_predict_year0,
    management_classes,
    target='relative_loss>5m',
    title="Management Classes"
)


fig, axes = boxplot_grid(
    df_predict_year0,
    ownership_parc_reserve_classes,
    target='relative_loss>5m',
    title="Ownership and Parc reserve classes"
)


fig, axes = boxplot_grid(
    df_predict_year0,
    location,
    target='relative_loss>5m',
    title="Location"
)


fig, axes = boxplot_grid(
    df_predict_year0,
    date,
    target='relative_loss>5m',
    title="Month and Year"
)






#%% Plot map with Sylvoecoregion and with the departement colored in the median height loss values! 
import geopandas as gpd 
import pandas as pd
from matplotlib import pyplot as plt 


# Now plot the polygons according to loss category 
# Load France outline
departement_file = "C:/Users/steff/Documents/06-Internshi_Paris/0_height_loss_area_analysis/departements/departements_L93.shp"
departement = gpd.read_file(departement_file)
target_crs = departement.crs  # keep Lambert-93


# load the SER areas in France: 
ser_file = r"C:\Users\steff\Documents\06-Internshi_Paris\0_height_loss_area_analysis\ser_regions\France_ser(1)\France_ser.shp"
ser = gpd.read_file(ser_file)


# we take data from the dataframe: df_model which we already saved as file: 
path_data_reduced = r"C:\Users\steff\Documents\06-Internshi_Paris\00_files_for_model\final\predictor_target_reduced.csv"
df_data_reduced = pd.read_csv(path_data_reduced, sep = ";", encoding = "utf-8-sig")


print(df_data_reduced.columns)
#%%
loss_metric1 = "relative_loss>3m"
loss_metric2 = "relative_loss>5m"

# ==== BY DEPARTEMENT ====
per_departement1 = df_data_reduced[['departement', loss_metric1]].groupby('departement').median()
per_departement2 = df_data_reduced[['departement', loss_metric2]].groupby('departement').median()
per_insee = df_data_reduced[["code_insee", "relative_loss>5m"]].groupby("code_insee").median()

# get one row per polygon with the size and the departement. (may overlap multiple departements so just pick the first line)
# Get one row per polygon (if a polygon overlaps multiple departments, keep the first occurrence)
df_data_polygon = (
    df_data_reduced[["departement", "area_ha", "polygon"]]
    .drop_duplicates(subset="polygon", keep="first")
)

print(len(df_data_polygon))

# Total polygon area per department
polygon_size = (
    df_data_polygon
    .groupby("departement")["area_ha"]
    .sum()
)

# Number of polygons per department
polygon_frequency = (
    df_data_polygon
    .groupby("departement")["polygon"]
    .count()
)

# get matching column to merge: DEPARTEMENT 
departement["departement"] = departement["INSEE_DEP"]

departement_loss1 = departement.merge(
    per_departement1,
    left_on="departement",
    right_index=True,
    how="left"
)

departement_loss2 = departement.merge(
    per_departement2,
    left_on="departement",
    right_index=True,
    how="left"
)

departement_size = departement.merge(
    polygon_size,
    left_on="departement",
    right_index=True,
    how="left"
)

departement_frequency = departement.merge(
    polygon_frequency,
    left_on="departement",
    right_index=True,
    how="left"
)
print(departement_loss1.columns)

# ==== PLOT BY DEPARTEMENT ====

fig, axes = plt.subplots(1, 4, figsize=(30, 10))

# 1. Median relative loss
departement_loss1.plot(
    column=loss_metric1,
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[0]
)
axes[0].set_axis_off()
axes[0].set_title(f"Median {loss_metric1} by department")

# 1. Median relative loss
departement_loss2.plot(
    column=loss_metric2,
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[1]
)
axes[1].set_axis_off()
axes[1].set_title(f"Median {loss_metric2} by department")


# 2. Total area
departement_size.plot(
    column="area_ha",
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[2]
)
axes[2].set_axis_off()
axes[2].set_title("Total area in ha by department")


# 3. Polygon frequency
departement_frequency.plot(
    column="polygon",
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[3]
)
axes[3].set_axis_off()
axes[3].set_title("Number of fires by department")

plt.suptitle("DEPARTEMENT", fontsize = 20)
plt.tight_layout()
plt.show()

# %%
loss_metric1 = "relative_loss>3m"
loss_metric2 = "relative_loss>5m"
# ==== BY SYLVOECOREGION REGION ====
per_ser1 = df_data_reduced[['sylvoecoregion', loss_metric1]].groupby('sylvoecoregion').median()
per_ser2 = df_data_reduced[['sylvoecoregion', loss_metric2]].groupby('sylvoecoregion').median()

# get one row per polygon with the size and the departement. (may overlap multiple departements so just pick the first line)
# Get one row per polygon (if a polygon overlaps multiple departments, keep the first occurrence)
df_data_polygon = (
    df_data_reduced[["sylvoecoregion", "area_ha", "polygon"]]
    .drop_duplicates(subset="polygon", keep="first")
)

print(len(df_data_polygon))

# Total polygon area per department
polygon_size = (
    df_data_polygon
    .groupby("sylvoecoregion")["area_ha"]
    .sum()
)

# Number of polygons per department
polygon_frequency = (
    df_data_polygon
    .groupby("sylvoecoregion")["polygon"]
    .count()
)

# get matching column to merge: DEPARTEMENT 
ser["sylvoecoregion"] = ser["codeser"]
print(ser.codeser.unique)

ser_loss1 = ser.merge(
    per_ser1,
    left_on="sylvoecoregion",
    right_index=True,
    how="left"
)

ser_loss2 = ser.merge(
    per_ser2,
    left_on="sylvoecoregion",
    right_index=True,
    how="left"
)

ser_size = ser.merge(
    polygon_size,
    left_on="sylvoecoregion",
    right_index=True,
    how="left"
)

ser_frequency = ser.merge(
    polygon_frequency,
    left_on="sylvoecoregion",
    right_index=True,
    how="left"
)
print(ser_loss1.columns)

# ==== PLOT BY SYLVOECOREGION ====

fig, axes = plt.subplots(1, 4, figsize=(30, 10))

# 1. Median relative loss
ser_loss1.plot(
    column=loss_metric1,
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[0]
)
axes[0].set_axis_off()
axes[0].set_title(f"Median {loss_metric1} by sylvoecoregion")

# 1. Median relative loss
ser_loss2.plot(
    column=loss_metric2,
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[1]
)
axes[1].set_axis_off()
axes[1].set_title(f"Median {loss_metric2} by sylvoecoregion")



# 2. Total area
ser_size.plot(
    column="area_ha",
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[2]
)
axes[2].set_axis_off()
axes[2].set_title("Total area in ha by sylvoecoregion")


# 3. Polygon frequency
ser_frequency.plot(
    column="polygon",
    cmap="viridis",
    legend=True,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    },
    ax=axes[3]
)
axes[3].set_axis_off()
axes[3].set_title("Number of fires by sylvoecoregion")

plt.suptitle("Sylvoecoregion", fontsize = 20)
plt.tight_layout()
plt.show()


# %% LOOK AT TREE SPECIES: 
import os 

df_median_species = (
    df_data_reduced
    .groupby("forest_type")["relative_loss>5m"]
    .median()
    .sort_values(ascending=False)
)

#top6_species = df_median_species.head(6).index.tolist()
top6_species = df_median_species.iloc[6:12].index.tolist()

print(top6_species)    

df_top6 = df_data_reduced[df_data_reduced["forest_type"].isin(top6_species)].copy()

polygon_species_stats = (
    df_top6
    .groupby(["polygon", "forest_type"])
    .agg(
        median_loss=("relative_loss>5m", "median"),
        q75_loss=("relative_loss>5m",
                  lambda x: x.quantile(0.75)),
        n_patches=("patch_id", "nunique"),
        total_area=("area_ha", "sum")
    )
    .reset_index()
)

print(polygon_species_stats.head())

# get the remaining polygons
selected_polygons = df_top6["polygon"].unique()
print(len(selected_polygons))

# load the polygon shape files: 
gdfs = []

target_crs = departement.crs

for polygon in selected_polygons:

    input_file = (
        fr"C:\Users\steff\Documents\06-Internshi_Paris"
        fr"\00_pipeline\data\Polygons\{polygon}.gpkg"
    )

    if os.path.exists(input_file):

        gdf = gpd.read_file(
            input_file,
            encoding="latin1"
        ).to_crs(target_crs)

        gdfs.append(gdf)

    else:

        print(f"Missing: {polygon}")

all_polygons = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True),
    crs=target_crs
)

all_polygons = all_polygons.to_crs(target_crs)

print(len(all_polygons))

polygon_species_map = all_polygons.merge(
    polygon_species_stats,
    left_on="Polygon_ID",
    right_on="polygon",
    how="inner"
)

# get the centroid 
polygon_species_map["centroid"] = polygon_species_map.geometry.centroid

polygon_species_map["marker_size"] = (10 * np.sqrt(polygon_species_map["n_patches"]))

points_gdf = gpd.GeoDataFrame(
    polygon_species_map.drop(columns="geometry"),
    geometry=polygon_species_map["centroid"],
    crs=polygon_species_map.crs
)


# Get the species to plot
species_list = points_gdf["forest_type"].unique()

# Create the figure
fig, axes = plt.subplots(
    nrows=2,
    ncols=3,
    figsize=(18, 12)
)

axes = axes.flatten()

# Keep the same color scale across all maps
vmin = points_gdf["median_loss"].min()
vmax = points_gdf["median_loss"].max()

for ax, species in zip(axes, species_list):

    subset = points_gdf[
        points_gdf["forest_type"] == species
    ]

    # Background map
    ser.plot(
        ax=ax,
        color="whitesmoke",
        edgecolor="lightgray",
        linewidth=0.5
    )

    # Centroids
    subset.plot(
        ax=ax,
        column="median_loss",
        cmap="viridis",
        markersize=subset["marker_size"],
        legend=True,
        vmin=vmin,
        vmax=vmax,
        alpha=0.8
    )

    ax.set_title(species)
    ax.set_axis_off()

# Remove the last panel if there are only 5 species
if len(species_list) < len(axes):
    fig.delaxes(axes[-1])

plt.suptitle("6-12 species with highest median height loss", fontsize = 20)
plt.tight_layout()
plt.show()

# %% LOOK AT TREE SPECIES:
# The ones with the biggest q90 
import os 

df_median_species = (
    df_data_reduced
    .groupby("forest_type")["relative_loss>5m"]
    .quantile(0.90)
    .sort_values(ascending=False)
)

#top6_species = df_median_species.head(6).index.tolist()
top6_species =  df_median_species.iloc[6:12].index.tolist()

print(top6_species)    

df_top6 = df_data_reduced[df_data_reduced["forest_type"].isin(top6_species)].copy()

polygon_species_stats = (
    df_top6
    .groupby(["polygon", "forest_type"])
    .agg(
        median_loss=("relative_loss>5m", "median"),
        q90_loss=("relative_loss>5m",
                  lambda x: x.quantile(0.9)),
        n_patches=("patch_id", "nunique"),
        total_area=("area_ha", "sum")
    )
    .reset_index()
)

print(polygon_species_stats.head())

# get the remaining polygons
selected_polygons = df_top6["polygon"].unique()
print(len(selected_polygons))

# load the polygon shape files: 
gdfs = []

target_crs = departement.crs

for polygon in selected_polygons:

    input_file = (
        fr"C:\Users\steff\Documents\06-Internshi_Paris"
        fr"\00_pipeline\data\Polygons\{polygon}.gpkg"
    )

    if os.path.exists(input_file):

        gdf = gpd.read_file(
            input_file,
            encoding="latin1"
        ).to_crs(target_crs)

        gdfs.append(gdf)

    else:

        print(f"Missing: {polygon}")

all_polygons = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True),
    crs=target_crs
)

all_polygons = all_polygons.to_crs(target_crs)

print(len(all_polygons))

polygon_species_map = all_polygons.merge(
    polygon_species_stats,
    left_on="Polygon_ID",
    right_on="polygon",
    how="inner"
)

# get the centroid 
polygon_species_map["centroid"] = polygon_species_map.geometry.centroid

polygon_species_map["marker_size"] = (10 * np.sqrt(polygon_species_map["n_patches"]))

points_gdf = gpd.GeoDataFrame(
    polygon_species_map.drop(columns="geometry"),
    geometry=polygon_species_map["centroid"],
    crs=polygon_species_map.crs
)


# Get the species to plot
species_list = points_gdf["forest_type"].unique()

# Create the figure
fig, axes = plt.subplots(
    nrows=2,
    ncols=3,
    figsize=(18, 12)
)

axes = axes.flatten()

# Keep the same color scale across all maps
vmin = points_gdf["q90_loss"].min()
vmax = points_gdf["q90_loss"].max()

for ax, species in zip(axes, species_list):

    subset = points_gdf[
        points_gdf["forest_type"] == species
    ]

    # Background map
    ser.plot(
        ax=ax,
        color="whitesmoke",
        edgecolor="lightgray",
        linewidth=0.5
    )

    # Centroids
    subset.plot(
        ax=ax,
        column="q90_loss",
        cmap="viridis",
        markersize=subset["marker_size"],
        legend=True,
        vmin=vmin,
        vmax=vmax,
        alpha=0.8
    )

    ax.set_title(species)
    ax.set_axis_off()

# Remove the last panel if there are only 5 species
if len(species_list) < len(axes):
    fig.delaxes(axes[-1])

plt.suptitle("6-12 species with highest q90 height loss", fontsize = 20)
plt.tight_layout()
plt.show()

# %% Plot where the January and February fires occur 

import os 

#top6_species = df_median_species.head(6).index.tolist()
winter = [10, 11, 12, 1, 2, 3]

df_winter = df_data_reduced[df_data_reduced["fire_month"].isin(winter)].copy()

polygon_species_stats = (
    df_winter
    .groupby(["polygon", "fire_month"])
    .agg(
        median_loss=("relative_loss>5m", "median"),
        q90_loss=("relative_loss>5m",
                  lambda x: x.quantile(0.9)),
        n_patches=("patch_id", "nunique"),
        total_area=("area_ha", "sum")
    )
    .reset_index()
)

print(polygon_species_stats.head())

# get the remaining polygons
selected_polygons = df_top6["polygon"].unique()
print(len(selected_polygons))

# load the polygon shape files: 
gdfs = []

target_crs = departement.crs

for polygon in selected_polygons:

    input_file = (
        fr"C:\Users\steff\Documents\06-Internshi_Paris"
        fr"\00_pipeline\data\Polygons\{polygon}.gpkg"
    )

    if os.path.exists(input_file):

        gdf = gpd.read_file(
            input_file,
            encoding="latin1"
        ).to_crs(target_crs)

        gdfs.append(gdf)

    else:

        print(f"Missing: {polygon}")

all_polygons = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True),
    crs=target_crs
)

all_polygons = all_polygons.to_crs(target_crs)

print(len(all_polygons))

polygon_species_map = all_polygons.merge(
    polygon_species_stats,
    left_on="Polygon_ID",
    right_on="polygon",
    how="inner"
)

# get the centroid 
polygon_species_map["centroid"] = polygon_species_map.geometry.centroid

polygon_species_map["marker_size"] = (10 * np.sqrt(polygon_species_map["n_patches"]))

points_gdf = gpd.GeoDataFrame(
    polygon_species_map.drop(columns="geometry"),
    geometry=polygon_species_map["centroid"],
    crs=polygon_species_map.crs
)


# Get the species to plot
species_list = points_gdf["fire_month"].unique()

# Create the figure
fig, axes = plt.subplots(
    nrows=2,
    ncols=3,
    figsize=(18, 12)
)

axes = axes.flatten()

# Keep the same color scale across all maps
vmin = points_gdf["q90_loss"].min()
vmax = points_gdf["q90_loss"].max()

for ax, month in zip(axes, species_list):

    subset = points_gdf[
        points_gdf["fire_month"] == month
    ]

    # Background map
    ser.plot(
        ax=ax,
        color="whitesmoke",
        edgecolor="lightgray",
        linewidth=0.5
    )

    # Centroids
    subset.plot(
        ax=ax,
        column="q90_loss",
        cmap="viridis",
        markersize=subset["marker_size"],
        legend=True,
        vmin=vmin,
        vmax=vmax,
        alpha=0.8
    )

    ax.set_title(month)
    ax.set_axis_off()

# Remove the last panel if there are only 5 species
if len(species_list) < len(axes):
    fig.delaxes(axes[-1])

plt.suptitle("Winter month median height loss per polygon", fontsize = 20)
plt.tight_layout()
plt.show()

# %% Look at the year 2022: 

import os 

#top6_species = df_median_species.head(6).index.tolist()
winter = [2017,2018,2019,2020, 2021, 2022]

df_winter = df_data_reduced[df_data_reduced["fire_year"].isin(winter)].copy()

polygon_species_stats = (
    df_winter
    .groupby(["polygon", "fire_year"])
    .agg(
        median_loss=("relative_loss>5m", "median"),
        q90_loss=("relative_loss>5m",
                  lambda x: x.quantile(0.9)),
        n_patches=("patch_id", "nunique"),
        total_area=("area_ha", "sum")
    )
    .reset_index()
)

print(polygon_species_stats.head())

# get the remaining polygons
selected_polygons = df_top6["polygon"].unique()
print(len(selected_polygons))

# load the polygon shape files: 
gdfs = []

target_crs = departement.crs

for polygon in selected_polygons:

    input_file = (
        fr"C:\Users\steff\Documents\06-Internshi_Paris"
        fr"\00_pipeline\data\Polygons\{polygon}.gpkg"
    )

    if os.path.exists(input_file):

        gdf = gpd.read_file(
            input_file,
            encoding="latin1"
        ).to_crs(target_crs)

        gdfs.append(gdf)

    else:

        print(f"Missing: {polygon}")

all_polygons = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True),
    crs=target_crs
)

all_polygons = all_polygons.to_crs(target_crs)

print(len(all_polygons))

polygon_species_map = all_polygons.merge(
    polygon_species_stats,
    left_on="Polygon_ID",
    right_on="polygon",
    how="inner"
)

# get the centroid 
polygon_species_map["centroid"] = polygon_species_map.geometry.centroid

polygon_species_map["marker_size"] = (10 * np.sqrt(polygon_species_map["n_patches"]))

points_gdf = gpd.GeoDataFrame(
    polygon_species_map.drop(columns="geometry"),
    geometry=polygon_species_map["centroid"],
    crs=polygon_species_map.crs
)


# Get the species to plot
species_list = points_gdf["fire_year"].unique()

# Create the figure
fig, axes = plt.subplots(
    nrows=2,
    ncols=3,
    figsize=(20, 12)
)

axes = axes.flatten()

# Keep the same color scale across all maps
vmin = points_gdf["q90_loss"].min()
vmax = points_gdf["q90_loss"].max()

for ax, month in zip(axes, winter):

    subset = points_gdf[
        points_gdf["fire_year"] == month
    ]

    # Background map
    ser.plot(
        ax=ax,
        color="whitesmoke",
        edgecolor="lightgray",
        linewidth=0.5
    )

    # Centroids
    subset.plot(
        ax=ax,
        column="q90_loss",
        cmap="viridis",
        markersize=subset["marker_size"],
        legend=True,
        vmin=vmin,
        vmax=vmax,
        alpha=0.8
    )

    ax.set_title(month)
    ax.set_axis_off()

# Remove the last panel if there are only 5 species
if len(species_list) < len(axes):
    fig.delaxes(axes[-1])

plt.suptitle("2022 median height loss per polygon", fontsize = 20)
plt.tight_layout()
plt.show()




