# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 16:49:44 2026

@author: steff
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 10:42:04 2026

@author: steff
description: 
"""

# =============================================================================
# STEP 1 – INPUT DATA & IO UTILITIES
# =============================================================================
import os
import sys
from pathlib import Path
import math
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize, geometry_mask
from rasterio.windows import from_bounds, transform as window_transform, Window
from shapely.geometry import box, mapping, Point
import pandas as pd
from scipy import ndimage


'''STRUCTURE OF FILES'''
_qwerty_work = os.environ.get(
    "QWERTY_WORK",
    os.path.join(os.environ.get("WORK", "/lustre/fswork/projects/rech/ego/uim21mi"), "QWERTY"),
)
local_folder = _qwerty_work.rstrip("/") + "/"

#adjust!!!
path_to_save = local_folder + "output" 
path_formspot_maps =  "/lustre/fsn1/projects/rech/ego/uim21mi/FORMSpoT_2014_2025_new_version/"# and then in the calling function this file name is added:  f"{year}_cog.tif"

path_polygons = local_folder + "input/Polygons"
path_spot_date = local_folder + "input/spot_dates"
path_patches_shapes = local_folder + "input/all_polygons_cut_overlap_removed_with_id.gpkg"
path_polygon_index = local_folder + "input/polygon_task_index.txt"
MIN_LANDSCAPE_PIXELS = 20
MIN_FULL_LANDSCAPE_PIXELS = 100
SMOOTH_MIN_SIZE = 11
LPI_STRUCTURE = ndimage.generate_binary_structure(2, 1)

# =============================================================================
# FOREST TYPE LOOKUP TABLE (BD Forêt)
# =============================================================================
FOREST_TYPE_LABELS = {
    -1: 'no_bd_foret',
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

# Dictionary for the broad forest categories 
BROAD_FOREST_TYPE_LABELS = {-1: 'no_bd_foret', 0.0: 'Other', 1.0: 'Pure deciduous', 6.0: 'Pure deciduous', 9.0: 'Pure deciduous', 10.0: 'Pure deciduous', 14.0: 'Pure deciduous',
19.0: 'Pure deciduous', 49.0: 'Pure deciduous', 100.0: 'Mixed deciduous', 111.0: 'Mixed deciduous', 51.0: 'Pure conifers', 52.0: 'Pure conifers', 53.0: 'Pure conifers', 57.0: 'Pure conifers',
58.0: 'Pure conifers',
81.0: 'Pure conifers', 80.0: 'Mixed conifers',
61.0: 'Pure conifers', 63.0: 'Pure conifers', 64.0: 'Pure conifers',
91.0: 'Pure conifers', 90.0: 'Mixed conifers',
200.0: 'Mixed conifers', 222.0: 'Mixed conifers',
310.0: 'Mixed deciduous', 320.0: 'Mixed conifers', 400.0: 'Other',
401.0: 'Mixed deciduous', 402.0: 'Mixed conifers', 403.0: 'Mixed deciduous', 504.0: 'Other',
506.0: 'Other', 1000: 'Other'}


# =============================================================================
# DATA 1 – FIRE POLYGON (AOI)
# =============================================================================
def load_polygon(polygon_name):
    """
    Load a fire polygon from a GeoPackage and derive spatial helpers.
    """

    input_file = path_polygons + f"/{polygon_name}.gpkg"
    #input_file = f"C:/Users/steff/Documents/06-Internshi_Paris/00_April/slope and altitude/Polygons/{polygon_name}.gpkg"

    gdf_polygon = gpd.read_file(input_file, encoding="cp1252").to_crs("EPSG:2154")

    x1, y1, x2, y2 = gdf_polygon.total_bounds
    bbox_geom = box(x1, y1, x2, y2)

    polygon_rectangle = gpd.GeoDataFrame(
        {"geometry": [bbox_geom]},
        crs="EPSG:2154"
    )

    polygon_bounds = (
        math.ceil(x1),
        math.ceil(y1),
        math.ceil(x2),
        math.ceil(y2),
    )
    
    x_center = 0.5 * (x1 + x2)
    y_center = 0.5 * (y1 + y2)
    
    center_point = gpd.GeoDataFrame(
        geometry=[Point(x_center, y_center)],
        crs="EPSG:2154"
    ).to_crs("EPSG:4326")
    
    lon, lat = center_point.geometry.iloc[0].coords[0]
    lon = round(lon,2)
    lat = round(lat,2)

    return gdf_polygon, polygon_rectangle, polygon_bounds, lon, lat 



# =============================================================================
# DATA 3 – FORMSPOT HEIGHT RASTERS
# =============================================================================

# load from the local height file 
# folder 

#folder = 'folder_placeholder_formspot'

# load height map from local file (bbox window read, then polygon mask)
def load_height_formspot_from_local(asset_type, years, gdf_polygon):
    """Load and clip FORMSpoT height rasters to a polygon AOI."""
    height_years = []
    transforms = []
    meta = {}
    gdf_poly = None
    last_crs = None

    for year in years:
        file = path_formspot_maps + f"{year}_cog.tif"
        with rasterio.open(file) as src:
            if src.crs != last_crs:
                gdf_poly = gdf_polygon.to_crs(src.crs)
                last_crs = src.crs

            minx, miny, maxx, maxy = gdf_poly.total_bounds
            window = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
            window = window.intersection(Window(0, 0, src.width, src.height))
            data = src.read(1, window=window).astype("float32")
            transform = window_transform(window, src.transform)

            inside = geometry_mask(
                [mapping(gdf_poly.geometry.iloc[0])],
                out_shape=data.shape,
                transform=transform,
                invert=True,
            )
            band = np.where(inside, data, np.nan)
            if src.nodata is not None:
                band = np.where(data == src.nodata, np.nan, band)

            height_years.append(band)
            transforms.append(transform)
            meta = {
                "crs": src.crs,
                "transform": transform,
                "resolution": src.res,
            }

    height_years = np.stack(height_years, axis=0) / 10.0  # dm → m
    return height_years, transforms, meta


def load_fire_polygon_ids():
    cache = Path(path_polygon_index)
    if cache.exists():
        return [line.strip() for line in cache.read_text(encoding="utf-8").splitlines() if line.strip()]
    try:
        df = gpd.read_file(path_patches_shapes, columns=["polygon"])
    except TypeError:
        df = gpd.read_file(path_patches_shapes)[["polygon"]]
    ids = [p.strip() for p in df.polygon.unique()]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(ids), encoding="utf-8")
    return ids


def load_patches_for_polygon(polygon_id):
    safe_id = polygon_id.replace("'", "''")
    try:
        return gpd.read_file(
            path_patches_shapes,
            where=f"polygon = '{safe_id}'",
        ).to_crs("EPSG:2154")
    except (ValueError, TypeError):
        patches = gpd.read_file(path_patches_shapes).to_crs("EPSG:2154")
        return patches[patches.polygon == polygon_id].copy()


# =============================================================================
# LOAD STATISTIC DATA 
# =============================================================================
def summary_stats(arr):
# Remove NaNs
    arr = arr[~np.isnan(arr)]

    # ---- HARD EXIT if no valid data ----
    if arr.size == 0:
        return {
            "mean": 0,
            "std": 0,
            "q05": 0,
            "q25": 0,
            "q50": 0,
            "q75": 0,
            "q95": 0,
            "coefficient_of_variation": 0
        }

    return {
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr)), 2),
        "q05": round(float(np.percentile(arr, 5)), 2),
        "q25": round(float(np.percentile(arr, 25)), 2),
        "q50": round(float(np.percentile(arr, 50)), 2),
        "q75": round(float(np.percentile(arr, 75)), 2),
        "q95": round(float(np.percentile(arr, 95)), 2),
        "coefficient_of_variation": round(np.std(arr)/np.mean(arr),2)
    }


# ===============LANDSCAPE METRICS FOR TREE COVER ANALYSIS=====================
# Define functions for the landscape metrics: 
    
# smooth to remove very small (less than 10 pixels that are trees or no trees within no trees or trees )
def remove_small_patches(binary, min_size=SMOOTH_MIN_SIZE):
    valid = ~np.isnan(binary)
    valid_n = int(valid.sum())
    if valid_n < min_size:
        return binary.copy()

    h, w = binary.shape
    if valid_n < min_size * min_size or h * w < min_size * min_size:
        return binary.copy()

    vals = np.unique(binary[valid])
    if len(vals) < 2:
        return binary.copy()

    def clean(img):
        if np.unique(img[valid]).size < 2:
            return img.copy()

        masked = np.where(valid, img, 0)
        labeled, _ = ndimage.label(masked)
        sizes = np.bincount(labeled.ravel())
        remove = sizes < min_size
        remove[0] = False

        cleaned = img.copy()
        cleaned[remove[labeled]] = 0
        cleaned[~valid] = np.nan
        return cleaned

    cleaned = clean(binary)
    cleaned_inside = np.where(valid, cleaned, np.nan)
    inverted = 1 - np.nan_to_num(cleaned_inside, nan=0)
    if np.unique(inverted[valid]).size < 2:
        return cleaned
    return 1 - clean(inverted)
    
# compute number of edge pixels between forest and non_forest 
def count_E(arr):
    """E = number of 4-neighbour forest-non-forest edge nodes."""
    a = np.asarray(arr)
    valid = ~np.isnan(a)
    num_pixels = int(valid.sum())
    if num_pixels == 0:
        return 0, 0

    a_bool = (a == 1) & valid

    h_diff = a_bool[:, :-1] ^ a_bool[:, 1:]
    h_valid = valid[:, :-1] & valid[:, 1:]
    horizontal_neighbors = h_diff & h_valid

    v_diff = a_bool[:-1, :] ^ a_bool[1:, :]
    v_valid = valid[:-1, :] & valid[1:, :]
    vertical_neighbors = v_diff & v_valid

    h1 = np.zeros_like(a_bool)
    h2 = np.zeros_like(a_bool)
    h1[:, :-1] = a_bool[:, :-1] & horizontal_neighbors
    h2[:, 1:] = a_bool[:, 1:] & horizontal_neighbors

    v1 = np.zeros_like(a_bool)
    v2 = np.zeros_like(a_bool)
    v1[:-1, :] = a_bool[:-1, :] & vertical_neighbors
    v2[1:, :] = a_bool[1:, :] & vertical_neighbors

    number_edge_nodes = int(np.count_nonzero(h1 | h2 | v1 | v2))
    return number_edge_nodes, num_pixels



# compute largest patch index 
def LPI(arr): 
    # Example:
    # 1 = forest
    # 0 = non-forest
    # NaN = nodata
    
    # valid pixels only
    valid_mask = ~np.isnan(arr)
    
    # case that there is only tree / only no_tree in the patch: 
    vals = np.unique(arr[valid_mask])
    if vals.size < 2:
        if vals.size == 0:
            return 0.0, 0.0
        if vals[0] == 0:
            return 0.0, 1.0
        return 1.0, 0.0

    A = int(valid_mask.sum())
    forest = arr == 1
    labeled_forest, _ = ndimage.label(forest, structure=LPI_STRUCTURE)
    forest_sizes = np.bincount(labeled_forest.ravel())[1:]
    LPI_forest = round(forest_sizes.max() / A, 2)

    nonforest = arr == 0
    labeled_nonforest, _ = ndimage.label(nonforest, structure=LPI_STRUCTURE)
    nonforest_sizes = np.bincount(labeled_nonforest.ravel())[1:]
    LPI_nonforest = round(nonforest_sizes.max() / A, 2)
    return LPI_forest, LPI_nonforest


def safe_ratio(count, total):
    return round(count / total, 2) if total != 0 else 0.0


def count_by_patch(label_raster, mask, max_label):
    labels = label_raster[mask].ravel().astype(np.int64)
    if labels.size == 0:
        return np.zeros(max_label + 1, dtype=np.int64)
    return np.bincount(labels, minlength=max_label + 1)


def polygon_center_lon_lat(gdf_polygon):
    x1, y1, x2, y2 = gdf_polygon.total_bounds
    center = (
        gpd.GeoSeries([Point(0.5 * (x1 + x2), 0.5 * (y1 + y2))], crs=gdf_polygon.crs)
        .to_crs("EPSG:4326")
        .iloc[0]
    )
    return round(center.x, 2), round(center.y, 2)


def build_stats_by_patch(labels, values, patch_ids):
    empty = summary_stats(np.array([]))
    out = {pid: empty.copy() for pid in patch_ids}
    if labels.size == 0:
        return out

    df = pd.DataFrame({"patch": labels.astype(np.int32), "h": values})
    grouped = df.groupby("patch", sort=False)["h"]
    means = grouped.mean().round(2)
    stds = grouped.std().round(2)
    quantiles = grouped.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).unstack(1).round(2)

    for pid in grouped.groups:
        mean = float(means[pid])
        std = float(stds[pid]) if pd.notna(stds[pid]) else 0.0
        out[int(pid)] = {
            "mean": mean,
            "std": std,
            "q05": float(quantiles.loc[pid, 0.05]),
            "q25": float(quantiles.loc[pid, 0.25]),
            "q50": float(quantiles.loc[pid, 0.50]),
            "q75": float(quantiles.loc[pid, 0.75]),
            "q95": float(quantiles.loc[pid, 0.95]),
            "coefficient_of_variation": round(std / mean, 2) if mean else 0,
        }
    return out


def build_patch_windows_from_gdf(patches_gdf, transform, raster_shape):
    """Bounding-box pixel windows from patch geometries (vectorized bounds)."""
    from rasterio.transform import rowcol

    height, width = raster_shape
    bounds = patches_gdf.bounds
    idx = patches_gdf.index.to_numpy()
    rows_a, cols_a = rowcol(transform, bounds.minx.to_numpy(), bounds.maxy.to_numpy())
    rows_b, cols_b = rowcol(transform, bounds.maxx.to_numpy(), bounds.miny.to_numpy())
    r0 = np.clip(np.minimum(rows_a, rows_b), 0, height - 1)
    r1 = np.clip(np.maximum(rows_a, rows_b), 0, height - 1)
    c0 = np.clip(np.minimum(cols_a, cols_b), 0, width - 1)
    c1 = np.clip(np.maximum(cols_a, cols_b), 0, width - 1)
    return {
        int(i): (slice(int(r0[j]), int(r1[j]) + 1), slice(int(c0[j]), int(c1[j]) + 1))
        for j, i in enumerate(idx)
    }


def build_patch_metadata_lut(patches_gdf, max_patch):
    idx = patches_gdf.index.to_numpy(dtype=np.int64)
    lut = {
        "patch_index": np.full(max_patch + 1, "", dtype=object),
        "tfv_num": np.zeros(max_patch + 1, dtype=np.float64),
        "forest_type": np.full(max_patch + 1, "", dtype=object),
        "broad_forest_type": np.full(max_patch + 1, "", dtype=object),
        "area_ha": np.zeros(max_patch + 1, dtype=np.float64),
    }
    lut["patch_index"][idx] = patches_gdf["patch_index"].to_numpy()
    lut["tfv_num"][idx] = patches_gdf["TFV_num"].to_numpy()
    lut["forest_type"][idx] = patches_gdf["TFV_num"].map(FOREST_TYPE_LABELS).to_numpy()
    lut["broad_forest_type"][idx] = patches_gdf["TFV_num"].map(BROAD_FOREST_TYPE_LABELS).to_numpy()
    lut["area_ha"][idx] = (patches_gdf["area2"] / 10000).to_numpy()
    return lut


def tree_cover_by_patch(label_raster, tree_year, base_mask, max_patch):
    tree_valid = base_mask & ~np.isnan(tree_year)
    tree_forest = base_mask & (tree_year == 1)
    den = count_by_patch(label_raster, tree_valid, max_patch)
    num = count_by_patch(label_raster, tree_forest, max_patch)
    cover = np.zeros(max_patch + 1, dtype=np.float64)
    np.divide(num, den, out=cover, where=den > 0)
    return np.round(cover, 2)


def landscape_metrics_for_window(tree_window, area_ha):
    valid = ~np.isnan(tree_window)
    valid_n = int(valid.sum())
    if valid_n < SMOOTH_MIN_SIZE * SMOOTH_MIN_SIZE or np.unique(tree_window[valid]).size < 2:
        smoothed_patch = tree_window
    else:
        smoothed_patch = remove_small_patches(tree_window)

    number_edge_nodes, num_pixels = count_E(smoothed_patch)
    edge_density = round((number_edge_nodes * 1.5) / area_ha, 3) if area_ha else 0.0
    tree_cover = round(np.sum(tree_window == 1) / num_pixels, 2) if num_pixels else 0.0
    lpi_forest, lpi_nonforest = LPI(smoothed_patch)
    return edge_density, tree_cover, lpi_forest, lpi_nonforest

#%%
# =============================================================================
# STEP 2 – SELECT FIRE POLYGON FOR THIS ARRAY TASK
# =============================================================================
task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
polygons = load_fire_polygon_ids()
polygon_id = polygons[task_id].strip()

array_job_id = os.environ.get("SLURM_ARRAY_JOB_ID")
if array_job_id:
    poly_marker = Path(local_folder) / "job_recap" / f".polygon_{array_job_id}_{task_id}.txt"
    poly_marker.parent.mkdir(parents=True, exist_ok=True)
    poly_marker.write_text(polygon_id, encoding="utf-8")

output_path = Path(path_to_save) / f"result_pipeline_{polygon_id}_new.csv"
if output_path.exists():
    print(f"{polygon_id} | already done, skipping")
    sys.exit(0)

# =============================================================================
# STEP 1 – LOAD POLYGON FILE 
# =============================================================================
polygon_path = Path(path_polygons) / f"{polygon_id}.gpkg"
polygon_gdf = gpd.read_file(polygon_path, encoding="cp1252").to_crs("EPSG:2154")
lon, lat = polygon_center_lon_lat(polygon_gdf)

polygon_gdf["fire_date"] = pd.to_datetime(
    polygon_gdf["date_de_premiere_alerte"].astype(int),
    unit="s"
)

poly_geom = polygon_gdf.geometry.iloc[0] # this is used for the intersection with the spot tiles! 
fire_date = polygon_gdf["fire_date"].iloc[0]
fire_year = fire_date.year

# =============================================================================
# STEP 2 – LOAD SPOT TILES FOR FIRE YEAR 
# =============================================================================
spot_path = path_spot_date + f"/spot_{fire_year}.gpkg" 

tiles_gdf = gpd.read_file(spot_path).to_crs("EPSG:2154")
try:
    spot_idx = tiles_gdf.sindex.query(poly_geom, predicate="intersects")
    containing_tile = tiles_gdf.iloc[spot_idx]
except Exception:
    containing_tile = tiles_gdf
containing_tile = containing_tile[containing_tile.geometry.contains(poly_geom)].copy()
containing_tile["date"] = pd.to_datetime(containing_tile["date"])

spot_date = containing_tile["date"].unique()

fire_date_str = fire_date.strftime("%Y-%m-%d")
spot_date_str = [d.strftime("%Y-%m-%d") for d in spot_date]

# =============================================================================
# STEP 3 – TEMPORAL LOGIC (PRE / POST FIRE)
# =============================================================================

min_spot = spot_date.min()
max_spot = spot_date.max() 

# Case 1: all SPOT acquisitions before fire
if max_spot < fire_date:
    year_pre_fire = fire_year
    year_post_fire = fire_year + 1

# Case 2: fire between two spot images
elif len(spot_date) > 1 and min_spot <= fire_date <= max_spot:
    year_pre_fire = fire_year - 1
    year_post_fire = fire_year + 1

# Case 3: all spot images after fire date (one or more tiles)
elif min_spot >= fire_date:
    
    # special case: spot acquisition within month after fire start 
    if (min_spot - fire_date).days <= 31:
        year_pre_fire = fire_year-1 
        year_post_fire = fire_year +1
        
    # Case Spot image after the fire (and after 30 days after the start of the fire )
    else: 
        year_pre_fire = fire_year - 1
        year_post_fire = fire_year

else:
    raise ValueError(
        f"No SPOT tile or no matching temporal case for {polygon_id}: fire={fire_date}, spot={spot_date}"
    )

# =============================================================================
# STEP 4 – LOAD HEIGHT DATA (ONLY REQUIRED YEARS) AND FILTER FOR ONLY PIXELS <= 5m 
# =============================================================================
years_to_load = [year_pre_fire] + list(range(year_post_fire, min(year_post_fire + 4, 2024) + 1))

height_dict = {}
transforms_dict = {}
tree_classes_dict = {}

for year in years_to_load:
    height, transform, _meta = load_height_formspot_from_local("height", [year], polygon_gdf)
    height_dict[year] = height[0]
    transforms_dict[year] = transform[0]

height_dict_no_filter = height_dict.copy()
pre_fire_height = height_dict[year_pre_fire]
forest_mask = pre_fire_height >= 5

for year in years_to_load:
    h = height_dict[year]
    h = np.where(forest_mask, h, np.nan).astype(np.float32, copy=False)
    height_dict[year] = h
    h_nf = height_dict_no_filter[year]
    tree_classes = np.full(h_nf.shape, np.nan, dtype=np.float32)
    tree_classes[(h_nf > 0) & (h_nf < 5)] = 0
    tree_classes[h_nf >= 5] = 1
    tree_classes_dict[year] = tree_classes

# ==============================================================================
# STEP 5 - LOAD THE FILE WITH THE SMALLER PATCHES PER BD FORET AND RASTERIZE 
# =============================================================================

# get the format we fit the patches against
first_year = years_to_load[0]
first_transform = transforms_dict[first_year]
height_shape = height_dict[first_year].shape

    
patches_polygon = load_patches_for_polygon(polygon_id)
patches_polygon["patch_index"] = patches_polygon.patch_id
patches_polygon = patches_polygon.reset_index(drop=True)
patches_polygon["area2"] = patches_polygon.geometry.area


# now create to raster file: 1 with the the patches, 2 with the tree species 
# Band 1: index
shapes_index = [
    (geom, idx)
    for geom, idx in zip(
        patches_polygon.geometry,
        patches_polygon.index
    )
]

# Band 2: TFV_num
shapes_tfv = [
    (geom, tfv)
    for geom, tfv in zip(
        patches_polygon.geometry,
        patches_polygon.TFV_num
    )
]

# create two rasters 
# raster index 
raster_index = rasterize(
    shapes_index,
    out_shape=height_shape,
    transform=first_transform,
    fill=-1,
    dtype="int32"
)

# raster TFV_num 
raster_tfv = rasterize(
    shapes_tfv,
    out_shape=height_shape,
    transform=first_transform,
    fill=-1,
    dtype="int32"
)  

aoi_geom = [mapping(polygon_gdf.geometry.iloc[0])]
aoi_mask = geometry_mask(
    aoi_geom,
    out_shape=height_shape,
    transform=first_transform,
    invert=True,
)

raster_index_masked = np.where(aoi_mask, raster_index, np.nan)
raster_tfv_masked = np.where(aoi_mask, raster_tfv, np.nan)

'''
plt.imshow(raster_tfv_masked)
plt.show()
'''

'''check
# Plot
fig, ax = plt.subplots(figsize=(8, 6))

im = ax.imshow(raster_index_masked, cmap="viridis")

ax.set_title("Forest patches")
plt.colorbar(im, ax=ax, label="Patch ID")

plt.show()
check'''

# =============================================================================
# STEP 6 – HEIGHT LOSS ANALYSIS
# =============================================================================

# Make a 3D array: shape = (num_years, height, width)
height_stack = np.stack([height_dict[year] for year in years_to_load], axis=0)
# Now height_stack[i] corresponds to years_to_load[i]

# compute height differens: current year minus previous year
height_diff_stack = height_stack[1:] - height_stack[:-1]

# get names for the differences 
diff_keys = [f"{years_to_load[i]}-{years_to_load[i-1]}" for i in range(1, len(years_to_load))]
height_diff_dict = dict(zip(diff_keys, height_diff_stack))

# compute masks for different definitions of height loss 
masks_dict = {}

for key, diff in height_diff_dict.items():
    mask_5m = diff < -5
    mask_3m = diff < -3
    
    with np.errstate(divide='ignore', invalid='ignore'):
        relative_loss = -diff / height_dict[int(key.split('-')[1])]  # divide by previous year
        relative_loss = np.nan_to_num(relative_loss, nan=0.0, posinf=0.0, neginf=0.0)
    
    mask_relative_25 = relative_loss > 0.25
    mask_relative_50 = relative_loss > 0.5
    mask_relative_75 = relative_loss > 0.75
    
    masks_dict[key] = {
        'mask_5m': mask_5m,
        'mask_3m': mask_3m,
        'mask_relative_25': mask_relative_25,
        'mask_relative_50': mask_relative_50,
        'mask_relative_75': mask_relative_75
    }

# =============================================================================
# STEP 6b – VECTORIZED PATCH ANALYSIS
# =============================================================================
inside_polygon = ~np.isnan(raster_tfv_masked)
label_raster = np.where(inside_polygon, raster_index.astype(np.int32), -1)
patch_ids = list(patches_polygon.index.unique())
max_patch = int(max(patch_ids)) if patch_ids else 0
base_mask = inside_polygon & (label_raster >= 0)
patch_windows = build_patch_windows_from_gdf(
    patches_polygon, first_transform, height_shape
)
meta_lut = build_patch_metadata_lut(patches_polygon, max_patch)
landscape_cache = {}

n_patches = len(patch_ids)
total_steps = n_patches * len(masks_dict)
progress_step = 0
last_pct = -1
print(f"{polygon_id} | {n_patches} patches | 0%", flush=True)

results = []
for i, (diff_key, masks) in enumerate(masks_dict.items()):
    prev_year = int(diff_key.split("-")[1])
    height_prev = height_dict[prev_year]
    height_no_filter_prev = height_dict_no_filter[prev_year]

    mask_pre = base_mask & ~np.isnan(height_no_filter_prev)
    mask_post = base_mask & ~np.isnan(height_prev)
    mask_above5 = base_mask & (height_prev >= 5)

    pixels_pre = count_by_patch(label_raster, mask_pre, max_patch)
    pixels_post = count_by_patch(label_raster, mask_post, max_patch)
    count_5m = count_by_patch(label_raster, base_mask & masks["mask_5m"], max_patch)
    count_3m = count_by_patch(label_raster, base_mask & masks["mask_3m"], max_patch)
    count_r25 = count_by_patch(label_raster, base_mask & masks["mask_relative_25"], max_patch)
    count_r50 = count_by_patch(label_raster, base_mask & masks["mask_relative_50"], max_patch)
    count_r75 = count_by_patch(label_raster, base_mask & masks["mask_relative_75"], max_patch)

    stats_no_filter = build_stats_by_patch(
        label_raster[mask_pre].ravel(),
        height_no_filter_prev[mask_pre].ravel(),
        patch_ids,
    )
    stats_above5 = build_stats_by_patch(
        label_raster[mask_above5].ravel(),
        height_prev[mask_above5].ravel(),
        patch_ids,
    )

    tree_year = tree_classes_dict[prev_year]
    tree_cover_vec = tree_cover_by_patch(label_raster, tree_year, base_mask, max_patch)
    diff_rows = []
    for index in patch_ids:
        pixels_patch_pre_filter = int(pixels_pre[index])
        pixels_patch_post_filter = int(pixels_post[index])

        cache_key = (prev_year, index)
        if pixels_patch_post_filter < MIN_LANDSCAPE_PIXELS:
            edge_density, tree_cover, lpi_forest, lpi_nonforest = 0.0, 0.0, 0.0, 0.0
        elif pixels_patch_post_filter < MIN_FULL_LANDSCAPE_PIXELS:
            edge_density, lpi_forest, lpi_nonforest = 0.0, 0.0, 0.0
            tree_cover = float(tree_cover_vec[index])
        elif cache_key in landscape_cache:
            edge_density, tree_cover, lpi_forest, lpi_nonforest = landscape_cache[cache_key]
        elif index in patch_windows:
            row_slice, col_slice = patch_windows[index]
            win_mask = label_raster[row_slice, col_slice] == index
            tree_sub = tree_year[row_slice, col_slice]
            tree_window = tree_sub.astype(np.float32, copy=True)
            tree_window[~win_mask] = np.nan
            edge_density, tree_cover, lpi_forest, lpi_nonforest = landscape_metrics_for_window(
                tree_window, meta_lut["area_ha"][index]
            )
            landscape_cache[cache_key] = (
                edge_density, tree_cover, lpi_forest, lpi_nonforest
            )
        else:
            edge_density, tree_cover, lpi_forest, lpi_nonforest = 0.0, 0.0, 0.0, 0.0

        pre_stats = stats_no_filter[index]
        pre_stats_above5m = stats_above5[index]
        c5 = int(count_5m[index])
        c3 = int(count_3m[index])
        cr25 = int(count_r25[index])
        cr50 = int(count_r50[index])
        cr75 = int(count_r75[index])

        diff_rows.append({
            "polygon": polygon_id,
            "year_diff": diff_key,
            "num_years_after_fire": i,
            "new_index": index,
            "patch_index": meta_lut["patch_index"][index],
            "tfv_num": meta_lut["tfv_num"][index],
            "forest_type": meta_lut["forest_type"][index],
            "broad_forest_type": meta_lut["broad_forest_type"][index],
            "new_total_pixels": pixels_patch_post_filter,
            "total_pixels_no_filter": pixels_patch_pre_filter,
            "forest_cover": safe_ratio(pixels_patch_post_filter, pixels_patch_pre_filter),
            "pixels_loss>5m": c5,
            "pixels_loss>3m": c3,
            "relative_loss>5m": safe_ratio(c5, pixels_patch_post_filter),
            "relative_loss>3m": safe_ratio(c3, pixels_patch_post_filter),
            "relative_loss_>25%": safe_ratio(cr25, pixels_patch_post_filter),
            "relative_loss_>50%": safe_ratio(cr50, pixels_patch_post_filter),
            "relative_loss_>75%": safe_ratio(cr75, pixels_patch_post_filter),
            **{f"height_no_filter_{k}": v for k, v in pre_stats.items()},
            **{f"height_above_5m_{k}": v for k, v in pre_stats_above5m.items()},
            "fire_date": fire_date_str,
            "spot_image_date": spot_date_str,
            "year_pre_fire": year_pre_fire,
            "year_post_fire": year_post_fire,
            "lon": lon,
            "lat": lat,
            "edge_density": edge_density,
            "tree_cover": float(tree_cover),
            "LPI_forest": float(lpi_forest),
            "LPI_nonforest": float(lpi_nonforest),
        })
        progress_step += 1
        pct = int(100 * progress_step / total_steps)
        if pct > last_pct:
            print(f"{polygon_id} | {n_patches} patches | {pct}%", flush=True)
            last_pct = pct
    results.extend(diff_rows)

df_area_height_loss = pd.DataFrame(results)  


#SAVING FILE 
new_path = Path(path_to_save)
new_path.mkdir(parents=True, exist_ok=True)
csv_filename = f"result_pipeline_{polygon_id}_new.csv"
output_file = new_path / csv_filename
df_area_height_loss.to_csv(output_file, index=False, sep=";", float_format="%.3f")
print(f"{polygon_id} | {n_patches} patches | saved {output_file}", flush=True)