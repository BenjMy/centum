#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 17:17:35 2025

@author: z0272571a
"""
import geopandas as gpd
import rioxarray
from dataclasses import dataclass
from typing import Optional
import xarray as xr
from rasterio.features import rasterize
import rasterio
import numpy as np
import xarray as xr

@dataclass
class IrrigationDistrict:
    """
    Class for handling irrigation districts using georeferenced shapefiles.
    
    Attributes
    ----------
    shapefile_path : str
        The path to the irrigation district shapefile.
    crs : str, optional
        The coordinate reference system (CRS) to convert the shapefile to, if needed.
    """
    shapefile_path: str
    crs: Optional[str] = None  # Optional CRS for reprojecting
    
    def load_shapefile(self) -> gpd.GeoDataFrame:
        """
        Loads the irrigation district shapefile into a GeoDataFrame.
        
        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame representing the irrigation districts.
        """
        # Load shapefile into GeoDataFrame
        gdf = gpd.read_file(self.shapefile_path)
        
        if self.crs:
            # If CRS is provided, reproject the GeoDataFrame to the specified CRS
            gdf = gdf.to_crs(self.crs)
        
        return gdf
    
    
    def convert_to_rioxarray(self, 
                             gdf: gpd.GeoDataFrame, variable: str, resolution: float, bounds: tuple) -> xr.DataArray:
        """
        Converts a GeoDataFrame to a rioxarray DataArray, enabling spatial operations on it.
    
        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            The GeoDataFrame representing the irrigation districts.
        variable : str
            The name of the variable to associate with the irrigation districts.
        resolution : float
            The spatial resolution of the output raster.
        bounds : tuple
            The bounding box of the raster in the format (minx, miny, maxx, maxy).
    
        Returns
        -------
        xr.DataArray
            A rioxarray DataArray with the variable values overlaid on the irrigation districts' geospatial extent.
        """
        # Extract geometries and associated values
        shapes = [(geom, value) for geom, value in zip(gdf.geometry, gdf[variable])]
    
        # Define raster dimensions
        width = int((bounds[2] - bounds[0]) / resolution)
        height = int((bounds[3] - bounds[1]) / resolution)
        transform = rasterio.transform.from_bounds(*bounds, width, height)
    
        # Rasterize the GeoDataFrame
        raster = rasterize(
            shapes,
            out_shape=(height, width),
            transform=transform,
            fill=0,  # Default value for areas outside geometries
            dtype=np.int32
        )
    
        # Convert to xarray.DataArray
        da = xr.DataArray(
            raster,
            dims=("y", "x"),
            coords={
                "y": np.linspace(bounds[3], bounds[1], height),
                "x": np.linspace(bounds[0], bounds[2], width)
            }
        )
    
        if gdf.crs is not None:
            # Assign CRS for spatial context
            da.rio.write_crs(gdf.crs, inplace=True)
    
        return da

    
    def get_irrigation_area(self, gdf: gpd.GeoDataFrame) -> float:
        """
        Computes the total irrigation area (in square kilometers).
        
        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            The GeoDataFrame representing the irrigation districts.
        
        Returns
        -------
        float
            The total area of the irrigation districts in square kilometers.
        """
        # Assuming the GeoDataFrame contains valid geometries, compute the area
        gdf = gdf.to_crs("EPSG:3395")  # Reproject to meters (using EPSG:3395)
        area_km2 = gdf.geometry.area.sum() / 1e6  # Convert from square meters to square kilometers
        
        return area_km2



def get_mask_IN_patch_i(irrigation_map_xr,patchid=0):
    mask_IN = irrigation_map_xr==patchid
    return mask_IN

def get_mask_OUT(irrigation_map_xr,patchid=0):
    mask_OUT = irrigation_map_xr==1
    return mask_OUT
