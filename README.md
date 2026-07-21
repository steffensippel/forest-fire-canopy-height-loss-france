# forest-fire-canopy-height-loss-france
Predicting canopy height loss after forest fires in France (2015–2022) using annual canopy height maps derived from SPOT imagery.
The objective is to identify and quantify importance of variables (ecological, evnironmental, landscape) that explain differences in spatial canopy height loss after forest fires. 

## Data
### Forest Fires 
- BDIFF fire database (> 5 ha) and fire polygons from ??

### Canopy height maps 
-FORMSpot:  https://doi.theia.data-terra.org/FORMSpoT/.  
-Annual canopy height maps (2014–2025) at 1.5 m resolution derived from SPOT-6/7 imagery.

### Additional predictors 
... 

## Workflow 
### 1. Polygon Partioning
To have a comparable area for the analysis, we cut the fire polygons into approximately equal-area subregions (around 1 ha). The polygons are cute within their BD foret tree species classes. For this we perform an iterative Voronoi algorithm, repeatedly refining Voronoi cells generated from smapled points.
The code is in code/preprocessing_polygons 

### 2. Height Loss Metric Computation 
1. Loading and spatial filtering of input data to the fire polygon

The height map is derived using SPOT images. Since the SPOT image for a specific region is acquired at a specific date we ensure that the fire falls in between two SPOT image acquisitions. The pre-fire year is the year of the SPOT image before the fire, the post-fire year is the year that corresponds to the spot image after the fire.

In some cases the height map of the year of fire is not reliable: If the fire date falls between two SPOT image acquisition dates of the same year, we define the pre-fire year as the previous year, the post-fire year as the year after. We apply the same logic, if the acquisition date of the SPOT image is within 31 days after the start of the fire.  

We load the 1.5m resolution annual canopy height maps for the polygon areas. We load the height map for the pre-fire year and the five subsequent years.

2. computing height-loss metrics at the pixel level and aggregating these by tree species and other characteristics 

Tree masking: We filter for pixels with pre fire height bigger than 5 m, as we focus on trees and want to exclude shrubs, moors and bare ground. Based on this filter we compute the pre fire forest cover as pixel kept / all pixels per 1 ha subregion. We only include the subregions in the analysis with a forest cover above 10%. 

Compute interannual height differences: For the masked tree pixels we compute the year to year height difference on a pixel level. Pixels are flagged as having experienced significant height loss if they lost a height within a year above a certain threshold. We differ absolute loss of more than 3m or 5m or relative loss of more than 25%, 50% ore 75%. Then we compute the proportion of tree pixels exceeding the height loss threshold per 1 ha subregion.

The code is in code/height_loss_pipeline

### 3. Process features 
Variables used for the predictive model are processed either on 1 ha subregion level or on the fire polygon level. 
(HOW TO UPLOAD THE TABLE HERE?)
- Polygon Shape / Landscape Structure 
- Distance / Landscape Position 
- Location 
- Ecological Region 
- Date / Fire Timing 
- Climate 
- Fire Severity 
- Topography 
- Soil Characteristics 
- Pre-fire Vegetation Structure 
- Biodiversity / Vegetation complexity 
- Tree cover / spatial vegetation pattern 
- Forest composition 
- Forest Management

### 4. Building a model to predict height loss


