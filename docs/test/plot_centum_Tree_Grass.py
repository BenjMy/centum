#!/usr/bin/env python
# coding: utf-8

# # Tree-Grass ecosystem analysis
# 
# **License:** CC-BY-4.0  
# **Github:** [https://github.com/BenjMy/centum](https://github.com/BenjMy/centum)  
# **Subject:** Tutorial
# **Authors**:
# 
# Benjamin Mary
#   Email: [benjamin.mary@ica.csic.es](mailto:benjamin.mary@ica.csic.es)  
#   ORCID: [0000-0001-7199-2885](https://orcid.org/0000-0001-7199-2885)  
#   Affiliation: ICA-CSIC
#   
# **Date:** 2025/01/10
# 

# :::{note} Hypothesis
# Irrigated agricultural areas can be distinguished from adjacent agricultural parcels or natural areas through a sudden increase in actual evapotranspiration which cannot be explained by other factors (e.g. change in weather or vegetation cover).
# :::
# 
# 

# :::{important}
# 
# For the **delineation** we will use two types of datasets: 
# - Earth Observation induced actual ET (calculated from an energy balance model): those are 3d raster datasets(x,y,time);
# - Only when dealing with real datasets: irrigation district shapefiles
# :::
# 
# In order to make calculation we will use the xarray datarray library. This has the advantage to allow us to read directly netcdf file format a standart for large raster images processing/storing. 
# 
# In the following we use a synthetic dataset that describe a rain event at day 3. 

# In[1]:


import pooch
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import centum
from centum import irrigation_district 
from centum.irrigation_district import IrrigationDistrict 
from centum import irrigation_district as irr_geo_tools 

from centum import utils 
from centum import plotting as pltC


# In[2]:


pooch_Majadas = pooch.create(
    path=pooch.os_cache("Majadas_project"),
    base_url="https://github.com/BenjMy/test_Majadas_centum_dataset/raw/refs/heads/main/",
    registry={
        "20200403_LEVEL2_ECMWF_TPday.tif": None,
        "ETa_Majadas.netcdf": None,
        "ETp_Majadas.netcdf": None,
        "CLC_Majadas_clipped.shp": None,
        "CLC_Majadas_clipped.shx": None,
        "CLC_Majadas_clipped.dbf": None,
    },
)

Majadas_ETa_dataset = pooch_Majadas.fetch('ETa_Majadas.netcdf')
Majadas_ETp_dataset = pooch_Majadas.fetch('ETp_Majadas.netcdf')
Majadas_CLC_shapefile = pooch_Majadas.fetch('CLC_Majadas_clipped.shp')
Majadas_CLC_shapefile = pooch_Majadas.fetch('CLC_Majadas_clipped.dbf')
Majadas_CLC_shx = pooch_Majadas.fetch('CLC_Majadas_clipped.shx')

ETa_ds = xr.load_dataset(Majadas_ETa_dataset)
ETa_ds = ETa_ds.rename({"__xarray_dataarray_variable__": "ETa"})  # Rename the main variable to 'ETa'
ETp_ds = xr.load_dataset(Majadas_ETp_dataset)
ETp_ds = ETp_ds.rename({"__xarray_dataarray_variable__": "ETp"})  # Rename the main variable to 'ETa'
CLC = gpd.read_file(Majadas_CLC_shapefile)  # Load the CLC dataset

# ETa_ds = ETa_ds



# Convert it to a rioxarray object with CRS handling
# ETa_rio = rxr.open_rasterio(Majadas_ETa_dataset, masked=True)



# In[3]:


from pyproj import CRS
crs = CRS.from_wkt('PROJCS["unknown",GEOGCS["WGS 84",DATUM["World Geodetic System 1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Azimuthal_Equidistant"],PARAMETER["latitude_of_center",53],PARAMETER["longitude_of_center",24],PARAMETER["false_easting",5837287.81977],PARAMETER["false_northing",2121415.69617],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]')
ETa_ds.rio.write_crs(crs.to_wkt(), inplace=True)


# In[4]:


# Ensure the CRS matches
CLC.set_crs(crs.to_wkt(), inplace=True)
fig, ax = plt.subplots(1, 1, figsize=(10, 5))
CLC.plot(column='Code_18', ax=ax, legend=True, cmap='viridis')
ax.set_title("Majadas de Tietar Corine Land Cover")
plt.show()

#%%

import leafmap
import rioxarray as rxr 

# Get the bounding box of the GeoDataFrame
# bbox = CLC.total_bounds  # Returns [minx, miny, maxx, maxy]
gdf_WGS84 = CLC.to_crs('EPSG:4326')
# bbox = gdf_WGS84.buffer(5e-4).total_bounds
bbox = gdf_WGS84.total_bounds

# Create the map with specific zoom and base map
# m = leafmap.Map(center=[(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2], zoom=15)

# Use the map_tiles_to_geotiff method to overlay the GeoTIFF onto the map
leafmap.map_tiles_to_geotiff('satellite.tif', bbox=list(bbox),
                             zoom=15, source='Esri.WorldImagery')

# Read the GeoTIFF file using rioxarray (replace with the path to your file)
satellite_image = rxr.open_rasterio('satellite.tif', masked=False)


#%%

clc_codes = utils.get_CLC_code_def()
categorical_enums = {'Code_18': clc_codes}


GeoAnalysis = IrrigationDistrict(Majadas_CLC_shapefile)
gdf_CLC = GeoAnalysis.load_shapefile()

# Plot the satellite image
fig, axs = plt.subplots(1,2,figsize=(10, 10))

# Plot the satellite image using imshow (from rioxarray)
satellite_image.plot.imshow(ax=axs[0], add_colorbar=False,
                            )

# Optionally, plot the boundaries of the GeoDataFrame
gdf_CLC.plot(column='Code_18', ax=axs[1], 
             legend=True, 
             cmap="viridis"
             )

# Set axis labels and title
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Satellite Image with GeoDataFrame Boundary')


axs[0].set_aspect('equal')
axs[1].set_aspect('equal')

# Show the plot
plt.show()



#%%


import contextily as ctx


CLC_Majadas_clipped_grid = GeoAnalysis.convert_to_xarray(gdf=gdf_CLC, 
                                            # variable="index", 
                                            resolution=(10,10), 
                                            engine='geocube',
                                            categorical_enums= categorical_enums,
                                            crs=None
                                            )


categorical_enums_list = [int(cc) for cc in categorical_enums['Code_18'].keys()] 
idcat = np.where(np.array(categorical_enums_list)==212)[0]
mask= CLC_Majadas_clipped_grid['Code_18']==idcat

fig, axs = plt.subplots(1,2,sharex=True,sharey=True)
gdf_CLC.plot(column='Code_18', ax=axs[0], legend=True, cmap="viridis")
CLC_Majadas_clipped_grid['Code_18'].where(mask).plot.imshow(ax=axs[1],
                                                            add_colorbar=False,
                                                            alpha=0.2
                                                            )
# ctx.add_basemap(axs[1], source=ctx.providers.Stamen.Terrain
#                 )

axs[0].set_aspect('equal')
axs[1].set_aspect('equal')


# In[9]:

CLC_Majadas_clipped_grid = CLC_Majadas_clipped_grid.rio.write_crs(crs.to_wkt())
ETa_ds = ETa_ds.rio.write_crs(crs.to_wkt())
CLC_Majadas_clipped_grid = CLC_Majadas_clipped_grid.rio.reproject_match(ETa_ds)

# ETa_ds_reprojected = ETa_ds.rio.reproject("EPSG:4326")


idcat = np.where(np.array(categorical_enums_list)==212)[0]
mask= CLC_Majadas_clipped_grid['Code_18']==idcat

fig, axs = plt.subplots(1,2,sharex=True,sharey=True)
gdf_CLC.plot(column='Code_18', ax=axs[0], legend=True, cmap="viridis")
CLC_Majadas_clipped_grid['Code_18'].where(mask).plot.imshow(ax=axs[1],
                                                            add_colorbar=False
                                                            )
axs[0].set_aspect('equal')
axs[1].set_aspect('equal')

fig, axs = plt.subplots(1,2,sharex=True,sharey=True)
gdf_CLC.plot(column='Code_18', ax=axs[0], legend=True, cmap="viridis")
CLC_Majadas_clipped_grid['Code_18'].plot.imshow(ax=axs[1],
                                                add_colorbar=True
                                                )
axs[0].set_aspect('equal')
axs[1].set_aspect('equal')

#%%

results = []
for land_cover in categorical_enums_list:
    print(land_cover)   
    idcat = np.where(np.array(categorical_enums_list)==land_cover)[0]
    mask= CLC_Majadas_clipped_grid['Code_18']==idcat    
    if np.sum(mask)>0:
        spatial_mean = ETa_ds['ETa'].isel(band=0).where(mask).mean(dim=["x", "y"], 
                                                skipna=True)
        results.append({"Code_18": land_cover, 
                    "ETa_mean": spatial_mean.values}
                   )
import pandas as pd
land_cover_means = pd.DataFrame(results)
land_cover_means.set_index('Code_18', inplace=True)

# In[ ]:

# Agricultural areas
Agricultural_areas = land_cover_means.loc[land_cover_means.index.astype(str).str.startswith('2')]
Forest_areas = land_cover_means.loc[land_cover_means.index.astype(str).str.startswith('3')]

Agricultural_areas_mean = np.nanmean(np.vstack(Agricultural_areas['ETa_mean'].to_numpy()),axis=0)
Forest_areas_mean = np.nanmean(np.vstack(Forest_areas['ETa_mean'].to_numpy()),axis=0)


# In[ ]:

import matplotlib.pyplot as plt

fig, axs = plt.subplots(1, 2, sharex=True, sharey=True)

# Plot for Agricultural areas (red color)
for i in Agricultural_areas.index:
    idcat = np.where(np.array(categorical_enums_list)==i)[0]
    mask = CLC_Majadas_clipped_grid['Code_18'] == idcat
    CLC_Majadas_clipped_grid['Code_18'].where(mask).plot.imshow(
        ax=axs[1],
        add_colorbar=False,
        cmap=plt.cm.Reds,  # Use a red colormap for agricultural areas
        vmin=0, vmax=1  # Adjust color intensity if necessary
    )

# Plot for Forest areas (blue color)
for i in Forest_areas.index:
    idcat = np.where(np.array(categorical_enums_list)==i)[0]
    mask = CLC_Majadas_clipped_grid['Code_18'] == idcat
    CLC_Majadas_clipped_grid['Code_18'].where(mask).plot.imshow(
        ax=axs[0],
        add_colorbar=False,
        cmap=plt.cm.Blues,  # Use a blue colormap for forest areas
        vmin=0, vmax=1  # Adjust color intensity if necessary
    )

# Adjust the aspect ratio of the subplots
axs[0].set_aspect('equal')
axs[1].set_aspect('equal')

plt.show()


fig, ax = plt.subplots()

for i in range(len(Agricultural_areas.index)):
    ax.scatter(
                x=ETa_ds.time,
                y=Agricultural_areas_mean,
                color='r',
                 alpha=0.2
                )

for i in range(len(Agricultural_areas.index)):
    ax.scatter(
                x=ETa_ds.time,
                y=Forest_areas_mean,
                color='g',
                 alpha=0.2
                )

#%%
from centum.delineation import ETAnalysis
scenario_analysis_usingET = ETAnalysis()

ET_analysis_ds = ETa_ds.isel(band=0)
ET_analysis_ds['ETp'] = ETp_ds['ETp'].isel(band=0)

decision_ds, event_type = scenario_analysis_usingET.irrigation_delineation(ET_analysis_ds)

#%%
mask_IN = irr_geo_tools.get_mask_IN_patch_i(CLC_Majadas_clipped_grid['Code_18'],
                                            patchid=1
                                            )
y_mean = decision_ds['ratio_ETap_local'].where(mask_IN, drop=True).mean(dim=['y', 'x'], 
                                                                        skipna=True
                                                                        )

fig, ax = plt.subplots()
ax.scatter(
            x=decision_ds.time.values,
            y=y_mean,
            color='r',
             alpha=0.2
            )

# for i in range(len(Agricultural_areas.index)):
#     ax.scatter(
#                 x=ETa_ds.time,
#                 y=Forest_areas_mean,
#                 color='g',
#                  alpha=0.2
#                 )
    
    
# ncols = 4
# time_steps = event_type.time.size
# nrows = int(np.ceil(time_steps / ncols))  # Number of rows needed
# fig, axes = plt.subplots(nrows=nrows, ncols=ncols, 
#                          figsize=(15, nrows * 3)
#                          )
# pltC.plot_irrigation_schedule(event_type,time_steps,fig,axes)

#%%

# mask_IN = CLC_Majadas_clipped_grid==1
# mask_OUT = irr_geo_tools.get_mask_OUT(rioxr_irrigation,
#                                       )

event_type_node_IN = event_type.where(mask_IN, drop=True).mean(['x','y'])
# event_type_node_OUT = event_type.where(mask_OUT, drop=True).mean(['x','y'])

event_type_node_IN.plot()

# np.sum(event_type)
