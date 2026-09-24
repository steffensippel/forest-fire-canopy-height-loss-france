# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 22:21:46 2026

@author: steff

Multiplot Figure: giving an overview of the fire polygons we look at in the analysis 
"""

# %% Packages Import 
import geopandas as gpd
from shapely.geometry import box
import matplotlib.pyplot as plt
import pandas as pd
import os 
from pyproj import Transformer
import numpy as np
from matplotlib.lines import Line2D
# Import Packages 

import math
#import xarray as xr
import rasterio
import pystac_client
import teledetection as tld


from rasterio.mask import mask
from shapely.geometry import mapping

from rasterio.plot import plotting_extent
from matplotlib.colors import Normalize
from matplotlib_scalebar.scalebar import ScaleBar

from matplotlib.gridspec import GridSpec


# %% Input files: 
path_polygon_infos = r"C:\Users\steff\Documents\16_Work_LSCE\September\Plots for Paper\input\predictor_target_reduced.csv"
path_countries_outline = r"C:\Users\steff\Documents\16_Work_LSCE\September\Plots for Paper\input\ne_10m_admin_0_countries\ne_10m_admin_0_countries.shp"
def path_polygon(polygon):
    return  rf"C:\Users\steff\Documents\16_Work_LSCE\September\data\Polygons\{polygon}.gpkg"
#%%
# ==== GET THE FIRE SIZE AND FIRE FREQUENCY PER YEAR AND FOREST REGION: 
# Load the information on the polygons
path_information_polygons = path_polygon_infos 
df_polygon_information = pd.read_csv(path_information_polygons, sep = ";")

# Build dictionary for different regions  
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

dic_broad_eco_region = {
    "06": "Mediterranean forest",
    "83": "Mediterranean forest",
    "13": "Mediterranean forest",
    "84": "Mediterranean forest",
    "30": "Mediterranean forest",
    "07": "Mediterranean forest",
    "34": "Mediterranean forest",
    "11": "Mediterranean forest",
    "66": "Mediterranean forest",
    "33": "Atlantic pine forest",
    "40": "Atlantic pine forest",
    "47": "Atlantic pine forest",
}

df_polygon_information["eco_region"] = (
    df_polygon_information["departement"]
    .map(dic_broad_eco_region)
    .fillna("Temperate forest")
)


# for the polygons, where "Other" is the most abundant broad forest category we neglect it. 
def mode_without_other(x):
    x = x[x != "Other"]
    
    if len(x) == 0:
        return "Other"
    
    return x.mode().iloc[0]

df_polygons = (
    df_polygon_information
    .groupby("polygon")
    .agg(
        fire_year=("fire_year", "first"),
        fire_month=("fire_month", "first"),
        eco_region = ("eco_region", "first"),
        area_ha=("area_ha", "first"),
        broad_forest_type=("broad_forest_type", mode_without_other),
    )
    .reset_index()
)

df_polygons = df_polygons.rename(columns = ({"polygon": "Polygon_ID"}))

# get the area in kha per eco region as well as the number of yearly fires 
df_polygons["area_kha"] = df_polygons["area_ha"] / 1000
fire_area = (
    df_polygons
    .groupby(["fire_year", "eco_region"])["area_kha"]
    .sum()
    .unstack(fill_value=0)
)

fire_number = (
    df_polygons
    .groupby("fire_year")
    .size()
)


# area distribution 
areas = df_polygons.loc[
    df_polygons["area_ha"] > 0, 
    "area_ha"
]

# Logarithmically spaced bins
bins = np.logspace(
    np.log10(areas.min()),
    np.log10(areas.max()),
    30
)


#%%
# ==== PREPARE A MAP OF FRANCE WITH THE POLYGONS IN IT ==== 
# ==== Load France outline and its neighboring countries ====
path_countries_outline = path_countries_outline
world = gpd.read_file(path_countries_outline, sep = ";")
     
# clip in epsg 2154 roughly 
world_rough = world.cx[-6:10, 41:52]

# reproject only this to Lambert-93
world_l93 = world_rough.to_crs(epsg=2154)

# Lambert-93 bounding box (in meters)
xmin, ymin, xmax, ymax =  -30000, 6000000, 1270000, 7190000

bbox_l93 = box(xmin, ymin, xmax, ymax)
world_clip = world_l93.clip(bbox_l93)


# ==== Prepare the fire polygons to map ====
# load the polygons to plot
polygons= df_polygons["Polygon_ID"].dropna().unique()

# get the crs for lambert93 
target_crs = "2154"

# load all the polygons into the file
gdfs = []
for polygon in polygons:
    input_file = path_polygon(polygon)
    if os.path.exists(input_file):
        gdfs.append(gpd.read_file(input_file, encoding = "latin1"))
    else:
        print(f"Missing: {polygon}")
        
# Reproject all polygons to Lambert 93 
gdfs = [gdf.to_crs(target_crs) for gdf in gdfs]


# 1 Combine all GeoDataFrames into one
all_polygons = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
all_polygons['year_int'] = pd.to_numeric(
    all_polygons['annee'], 
    errors='coerce'
)
# Area in hectares
all_polygons["area_ha"] = all_polygons.geometry.area / 10000

all_polygons = all_polygons[['UID', 'Polygon_ID','annee', 'year_int', 'numero', 'departement', 'code_insee','date_de_premiere_alerte', 'geometry', 'Year', 'Fire_ID', 'area_ha']]
print(all_polygons.columns)
print(len(all_polygons))

# convert the polygons shapes to just their centroid 
all_polygons["centroid"] = all_polygons.geometry.centroid

# scaling of the dot size representing a polygon area
all_polygons["marker_size"] = 4*(all_polygons["area_ha"]) ** 0.5

points_gdf = gpd.GeoDataFrame(
    all_polygons.drop(columns="geometry"),
    geometry=all_polygons["centroid"],
    crs=all_polygons.crs
)

points_gdf = points_gdf.merge(df_polygons, on  ="Polygon_ID", how = "left")

# Define colors for each broad forest type
forest_colors = {
    "Pure deciduous": "#f0c571",
    "Mixed deciduous": "#59a89c",
    "Pure conifers": "#a559aa",
    "Mixed conifers": "#e07a5f", 
    "Shrublands": "#4c78a8" 
}

 


#%%
# ==== Load the Formspot height map yearly evolution for specific polygons (pre / post fire)  ====

# DATA 1: Fire polygon area  
def load_polygon(polygon): 
    """
    Load a polygon from a GeoPackage and compute its bounding rectangle and boundaries.
    """
    input_file = path_polygon(polygon)
    #input_file = polygon_folder / f"{polygon}.gpkg"
    gdf_polygon = gpd.read_file(input_file).to_crs("EPSG:2154")
    
    x1, y1, x2, y2 = gdf_polygon.total_bounds
    bbox_geom = box(x1, y1, x2, y2)
    
    polygon_rectangle = gpd.GeoDataFrame({"geometry": [bbox_geom]}, crs="EPSG:2154")
    polygon_boundaries = (math.ceil(x1), math.ceil(y1), math.ceil(x2), math.ceil(y2))
    
    return gdf_polygon, polygon_rectangle, polygon_boundaries

# DATA 5: Forest Height data: 1.5 m resolution height data  
def load_height_formspot_only_polygon(asset_type, years, gdf_polygon):
    """
    Load and clip FORMSpoT height rasters to polygon AOI.
    Returns stacked array (years, rows, cols) and transforms.
    Heights returned in meters.
    Areas outside polygon are set to np.nan for clean plotting.
    """
    api = pystac_client.Client.open(
        "https://api.stac.teledetection.fr",
        modifier=tld.sign_inplace,
    )

    height_years = []
    transforms = []

    for year in years:
        asset = (
            api.get_collection("FORMSpoT")
            .get_item(f"FORMSpoT-{year}")
            .get_assets()[f"height_{year}"]
        )

        with rasterio.open(asset.href) as src:
            # reproject polygon to raster CRS
            gdf_poly = gdf_polygon.to_crs(src.crs)
            geom = [mapping(gdf_poly.geometry.iloc[0])]
            
            # get bounding box (minx, miny, maxx, maxy)
            minx, miny, maxx, maxy = gdf_poly.total_bounds
            
            '''
            # create rectangular geometry
            bbox_geom = box(minx, miny, maxx, maxy)
            geom = [mapping(bbox_geom)]
            '''
            # mask the raster with the polygon; crop=True keeps only polygon area
            data, transform = mask(src, geom, crop=True, filled=True)  # filled=True ensures outside is nodata
            band = data[0].astype("float32")

            # replace raster nodata values with np.nan
            nodata = src.nodata
            if nodata is not None:
                band[band == nodata] = np.nan

            height_years.append(band)
            transforms.append(transform)

        print(f"Loaded & clipped height for {year}")

    # stack all years
    height_years = np.stack(height_years, axis=0)
    height_years /= 10.0  # decimeters → meters
    
    # Percentiles of ONLY valid pixels inside polygon
    vmin, vmax = np.nanpercentile(
        height_years,
        [1, 99]
    )

    return height_years, transforms, vmin, vmax

# ==Load the V-022 polygon==
polygon = "V-022"

# load the polygon 
gdf_polygon, polygon_rectangle, polygon_boundareis = load_polygon(polygon)
gdf_polygon.plot()

# load the years to plot 
years = [2022, 2023]


# load height maps
heights_formspot_only_polygon_V_022, transform_V_022, vmin_only_polygon_V_022, vmax_only_polygon_V_022 = load_height_formspot_only_polygon('height',
    years, gdf_polygon
)


# ==Load the Q-077 polygon== 

polygon = "Q-077"

# load the polygon 
gdf_polygon_Q_77, polygon_rectangle_Q_77, polygon_boundareis_Q_77 = load_polygon(polygon)
gdf_polygon_Q_77.plot()

# load the years to plot 

years = [2016, 2017, 2018]

# load height maps 
heights_formspot_only_polygon_Q_77, transform_Q_77, vmin_only_polygon_Q_77, vmax_only_polygon_Q_77 = load_height_formspot_only_polygon('height',
    years, gdf_polygon_Q_77
)


# Colormap & normalization
cmap ="magma"
vmin = 0
vmax = max(
    vmax_only_polygon_V_022,
    vmax_only_polygon_Q_77
)

norm = Normalize(vmin=vmin, vmax=vmax)

#%% COMPLETE PLOT LAYOUT 

fontsize_big = 15
fontsize_medium = 13
fontsize_small = 8
# =========================================================
# MAIN FIGURE
# =========================================================

fig = plt.figure(
    figsize=(12, 4.5 + 10.98 + 3.2),     # A4 width, ~3/4 A4 height
    facecolor="white"
)

gs = GridSpec(
    3, 2,
    figure=fig,
    height_ratios=[4.5,10.98, 3.2],
    width_ratios=[1, 1],
)


# =========================================================
# 1. TOP LEFT — BURNED AREA
# =========================================================

# VERSION 1: VERTICAL: 

ax = fig.add_subplot(gs[0, 0])

fire_area.plot(
    kind="bar",
    ax=ax,
    stacked=True,
    color=["#9DBF9E", "#F2C98A", "#d9d9d9"]
)

# Number of fires
for i, year in enumerate(fire_area.index):

    if year in fire_number.index:

        total_area = fire_area.loc[year].sum()
        n_fires = fire_number.loc[year]

        ax.text(
            i,
            total_area + 1,
            f"{n_fires} fires",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

ax.set_ylabel(
    "Burned area (kha)",
    fontsize=fontsize_big
)

ax.set_xlabel("")

ax.legend(
    title="Region",
    fontsize=fontsize_big,
    title_fontsize=fontsize_big,
    frameon=False
)

ax.tick_params(
    axis="x",
    labelrotation=45,
    labelsize=fontsize_big
)

ax.tick_params(
    axis="y",
    labelsize=fontsize_big
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =========================================================
# 2. TOP RIGHT — POLYGON AREA DISTRIBUTION
# =========================================================

ax = fig.add_subplot(gs[0, 1])


ax.hist(
    areas,
    bins=bins,
    edgecolor="black",
    alpha=0.7
)

ax.set_xscale("log")

ax.set_xlabel("Polygon area (ha)", fontsize = 15)
ax.set_ylabel("Number of polygons", fontsize = 15)


ax.tick_params(axis="x", labelsize=15)
ax.tick_params(axis="y", labelsize=15)

#ax.set_title("Distribution of fire areas")

# remove upper and right outline: 
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)   

# =========================================================
# 3. CENTRAL — MAP
# =========================================================

ax_map = fig.add_subplot(gs[1, :])

map_box = box(xmin, ymin, xmax, ymax)

land = world_clip.geometry.union_all()

water = map_box.difference(land)

gpd.GeoSeries(
    [water],
    crs=world_clip.crs
).plot(
    ax=ax_map,
    color="white",
    edgecolor="none"
)

world_clip.plot(
    ax=ax_map,
    color="white",
    edgecolor="grey",
    linewidth=0.6,
    alpha=0.9
)

world_clip[
    world_clip["SOVEREIGNT"] == "France"
].plot(
    ax=ax_map,
    color="white",
    edgecolor="grey",
    linewidth=1.4
)


ax_map.set_xlim(xmin, xmax)
ax_map.set_ylim(ymin, ymax)


# ---------------------------------------------------------
# Forest types
# ---------------------------------------------------------

for forest_type, color in forest_colors.items():

    subset = points_gdf[
        points_gdf["broad_forest_type"] == forest_type
    ]

    ax_map.scatter(
        subset.geometry.x,
        subset.geometry.y,
        color=color,
        s=subset["marker_size"],
        linewidth=0.3,
        alpha=0.7,
        label=forest_type
    )


# ---------------------------------------------------------
# Forest legend
# ---------------------------------------------------------

legend_handles = [
    Line2D(
        [0], [0],
        marker="o",
        color="none",
        markerfacecolor=color,
        markeredgecolor=color,
        markersize=8,
        alpha=0.7,
        label=forest_type
    )
    for forest_type, color in forest_colors.items()
]

forest_legend = ax_map.legend(
    handles=legend_handles,
    title="Broad forest type",
    loc="upper left",
    frameon=True,
    fontsize=fontsize_big,
    title_fontsize=fontsize_big
)

ax_map.add_artist(forest_legend)


# ---------------------------------------------------------
# Fire size legend
# ---------------------------------------------------------

size_legend_values = [100, 1000, 10000]

size_handles = [
    plt.scatter(
        [],
        [],
        s=4 * area ** 0.5,
        color="white",
        edgecolor="black",
        linewidth=0.6,
        label=f"{area:,} ha"
    )
    for area in size_legend_values
]

size_legend = ax_map.legend(
    handles=size_handles,
    title="Fire size",
    title_fontsize=fontsize_big,
    fontsize=fontsize_big,
    loc="lower left",
    frameon=True,
    framealpha=1,       # transparency: 0 = invisible, 1 = opaque
    scatterpoints=1
)

ax_map.add_artist(size_legend)


# ---------------------------------------------------------
# Coordinates
# ---------------------------------------------------------

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2154",
    always_xy=True
)

lon_ticks = np.arange(-6, 11, 2)
lat_ticks = np.arange(42, 53, 2)

lon_x = []

for lon in lon_ticks:

    x, y = transformer.transform(
        lon,
        46
    )

    lon_x.append(x)


lat_y = []

for lat in lat_ticks:

    x, y = transformer.transform(
        2,
        lat
    )

    lat_y.append(y)


ax_map.set_xticks(lon_x)
ax_map.set_yticks(lat_y)

ax_map.set_xticklabels(
    [
        f"{abs(lon)}°{'W' if lon < 0 else 'E' if lon > 0 else ''}"
        for lon in lon_ticks
    ],
    fontsize=fontsize_medium
)

ax_map.set_yticklabels(
    [f"{lat}°N" for lat in lat_ticks],
    fontsize=fontsize_medium
)

ax_map.tick_params(
    axis="x",
    bottom=True,
    labelbottom=True,
    top=False,
    labeltop=False,
    length=3
)

ax_map.tick_params(
    axis="y",
    left=True,
    labelleft=True,
    right=False,
    labelright=False,
    length=3
)

ax_map.set_aspect(
    "equal",
    adjustable="box"
)


# =========================================================
# 4. BOTTOM — CANOPY HEIGHT MULTIPANEL
# =========================================================

# Create a nested GridSpec inside the bottom row
gs_canopy = gs[2, :].subgridspec(
    1,
    6,
    width_ratios=[1, 1, 0.08, 1, 1, 1],
    wspace=0
)

canopy_axes = [
    fig.add_subplot(gs_canopy[0, 0]),
    fig.add_subplot(gs_canopy[0, 1]),
    fig.add_subplot(gs_canopy[0, 3]),
    fig.add_subplot(gs_canopy[0, 4]),
    fig.add_subplot(gs_canopy[0, 5])
]


# ---------------------------------------------------------
# Common normalization
# ---------------------------------------------------------

cmap = "magma"

vmin = 0
vmax = 25

norm = Normalize(
    vmin=vmin,
    vmax=vmax
)


# ---------------------------------------------------------
# Background
# ---------------------------------------------------------

background_color = "#444444"

for ax in canopy_axes:
    ax.set_facecolor(background_color)


# ---------------------------------------------------------
# V-022
# ---------------------------------------------------------

for i, year in enumerate([2022, 2023]):

    ax = canopy_axes[i]

    extent = plotting_extent(
        heights_formspot_only_polygon_V_022[i],
        transform_V_022[i]
    )

    im = ax.imshow(
        heights_formspot_only_polygon_V_022[i],
        cmap=cmap,
        norm=norm,
        extent=extent
    )

    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(
        0.05,
        0.95,
        str(year),
        transform=ax.transAxes,
        fontsize=fontsize_big,
        fontweight="bold",
        verticalalignment="top",
        color="white"
    )

    scalebar = ScaleBar(
        1,
        units="m",
        dimension="si-length",
        location="lower right",
        length_fraction=0.25,
        box_alpha=0,
        color="white",
        scale_loc="bottom",
        label="",
        font_properties={"size": fontsize_medium}
    )

    ax.add_artist(scalebar)


# ---------------------------------------------------------
# Q-077
# ---------------------------------------------------------

for i, year in enumerate([2016, 2017, 2018]):

    ax = canopy_axes[i + 2]

    extent = plotting_extent(
        heights_formspot_only_polygon_Q_77[i],
        transform_Q_77[i]
    )

    im = ax.imshow(
        heights_formspot_only_polygon_Q_77[i],
        cmap=cmap,
        norm=norm,
        extent=extent
    )

    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(
        0.6,
        0.95,
        str(year),
        transform=ax.transAxes,
        fontsize=fontsize_big,
        fontweight="bold",
        verticalalignment="top",
        color="white"
    )

    scalebar = ScaleBar(
        1,
        units="m",
        dimension="si-length",
        location="lower left",
        length_fraction=0.25,
        box_alpha=0,
        color="white",
        scale_loc="bottom",
        label="",
        font_properties={"size": fontsize_medium}
    )

    ax.add_artist(scalebar)


# =========================================================
# CANOPY COLORBAR
# =========================================================

cbar_ax = fig.add_axes([
    0.35,    # left
    0.08,   # bottom
    0.30,    # width
    0.01    # height
])

cbar = fig.colorbar(
    im,
    cax=cbar_ax,
    orientation="horizontal"
)

cbar.set_ticks([vmin, vmax])

cbar.set_ticklabels([
    f"{vmin:g}m",
    f"{vmax:g}m"
])

cbar.ax.tick_params(
    labelsize=fontsize_big
)

cbar.set_label(
    "Canopy Height (m)",
    fontsize=fontsize_big,
    labelpad=3
)


# =========================================================
# DISPLAY
# =========================================================

plt.show()


