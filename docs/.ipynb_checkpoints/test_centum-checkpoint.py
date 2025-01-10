#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 14:05:06 2024
"""

from centum import plotting as pltC
import xarray as xr
import numpy as np

from centum.delineation import ETAnalysis
import matplotlib.pyplot as plt

from centum.irrigation_district import IrrigationDistrict 
from centum import irrigation_district as irr_geo_tools 

#%%
scenario_nb = 0
ds_analysis_EO = xr.open_dataset(f'../data/synthetic/ds_analysis_EO_{scenario_nb}.netcdf')
ds_analysis_baseline = xr.open_dataset(f'../data/synthetic/ds_analysis_baseline_{scenario_nb}.netcdf')
# grid_xr_with_IRR = xr.open_dataset(f'{rootpath}/prepro/grid_xr_EO_AquaCrop_sc{args.sc_AQUACROP}_weather_{args.weather_scenario}.netcdf')

#%%
# Corrected implementation to ensure consistency and proper handling of geometries
import geopandas as gpd
from shapely.geometry import Polygon

# Define raster dimensions and pixel size
raster_size = 1000
center_size = 100
pixel_size = 1  # Assuming 1x1 units per pixel

# Define the outer bounds of the raster
raster_extent = [
    (0, 0),
    (raster_size * pixel_size, 0),
    (raster_size * pixel_size, raster_size * pixel_size),
    (0, raster_size * pixel_size),
    (0, 0),
]

# Define the center bounds for the 10x10 polygon
center_start = (raster_size - center_size) // 2 * pixel_size
center_end = center_start + center_size * pixel_size
center_extent = [
    (center_start, center_start),
    (center_end, center_start),
    (center_end, center_end),
    (center_start, center_end),
    (center_start, center_start),
]
# Create polygons
outer_polygon = Polygon(raster_extent)
center_polygon = Polygon(center_extent)

# Create a GeoDataFrame with both zones
gdf = gpd.GeoDataFrame(
    {"zone": ["outer", "center"], "geometry": [outer_polygon, center_polygon]},
    # crs="EPSG:4326",  # Default CRS (can be changed)
)
# Save the GeoDataFrame as a shapefile
import matplotlib.pyplot as plt
# Plot the GeoDataFrame with different colors for the zones
fig, ax = plt.subplots(figsize=(8, 8))
gdf.plot(ax=ax, column='zone', legend=True, cmap='viridis', edgecolor='black')
# Add title and labels for clarity
ax.set_title("Polygon Zones: Outer and Center", fontsize=14)
ax.set_xlabel("X Coordinate", fontsize=12)
ax.set_ylabel("Y Coordinate", fontsize=12)
plt.show()


# Save to shapefile
output_shapefile = "../data/synthetic/area_SC0.shp"
gdf.to_file(output_shapefile)

#output_shapefile


#%%
_, index = np.unique(ds_analysis_EO['time'], return_index=True)
ds_analysis_EO = ds_analysis_EO.isel(time=index)
ds_analysis_baseline = ds_analysis_baseline.isel(time=index)

ds_analysis_EO['ACT. ETRA'].plot.imshow(x="x", y="y", 
                                        col="time", 
                                        col_wrap=4,
                                        )
ds_analysis_baseline['ACT. ETRA'].plot.imshow(x="x", y="y", 
                                        col="time", 
                                        col_wrap=4,
                                        )
# ss
#%%
scenario_analysis_usingET = ETAnalysis()
decision_ds, event_type = scenario_analysis_usingET.irrigation_delineation(ds_analysis_EO)

#%% Plot timeline 
ncols = 4
time_steps = event_type.time.size
nrows = int(np.ceil(time_steps / ncols))  # Number of rows needed
fig, axes = plt.subplots(nrows=nrows, ncols=ncols, 
                         figsize=(15, nrows * 3)
                         )
pltC.plot_irrigation_schedule(event_type,time_steps,fig,axes)
# plt.savefig(os.path.join(figpath, 'classify_events.png'))

#%%
GeoAnalysis = IrrigationDistrict("../data/synthetic/area_SC0.shp")
gdf_irr = GeoAnalysis.load_shapefile()
resolution = event_type.rio.resolution()[0]
bounds = gdf.total_bounds  # (minx, miny, maxx, maxy)
gdf_irr['index'] = gdf_irr.index.values
rioxr_irrigation = GeoAnalysis.convert_to_rioxarray(gdf=gdf_irr, 
                                                    variable="index", 
                                                    resolution=resolution, 
                                                    bounds=bounds
                                                    )
rioxr_irrigation = rioxr_irrigation.rio.write_crs("EPSG:4326")
event_type = event_type.rio.write_crs("EPSG:4326")
rioxr_irrigation= rioxr_irrigation.rio.reproject_match(event_type)


rioxr_irrigation.plot.imshow()
event_type.x
rioxr_irrigation.x
    
#%%

mask_IN = irr_geo_tools.get_mask_IN_patch_i(rioxr_irrigation,
                                    patchid=1
                                    )
mask_IN = rioxr_irrigation==1
mask_OUT = irr_geo_tools.get_mask_OUT(rioxr_irrigation,
                                      )

event_type_node_IN = event_type.where(mask_IN, drop=True).mean(['x','y'])
event_type_node_OUT = event_type.where(mask_OUT, drop=True).mean(['x','y'])

#%%
    
# plot_local_regional_time_serie



#%%
# def set_probability_levels():
#     print('to implement')
#     pass
    
