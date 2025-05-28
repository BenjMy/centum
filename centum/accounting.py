import centum.delineation
import centum.irrigation_district
import centum.plotting
import centum.utils
import xarray as xr
import matplotlib.pyplot as plt

import numpy as np
import rioxarray  # you already have it
import pandas as pd

def compute_pixel_area(da):
    """
    Compute the approximate area (m²) of each pixel based on coordinate spacing.
    Assumes coordinates are in meters (e.g., UTM projection).

    Parameters:
    - da: xarray.DataArray with spatial dims 'x' and 'y' and coordinate values in meters.

    Returns:
    - 2D numpy array of pixel areas in m² with shape (y, x)
    """
    # Calculate resolution in x and y directions (assumed uniform spacing)
    dx = np.abs(np.diff(da['x'].values).mean())
    dy = np.abs(np.diff(da['y'].values).mean())
    pixel_area = dx * dy
    return pixel_area


def et_mm_day_to_m3_day(da_etha, pixel_area_m2):
    """
    Convert ETa from mm/day to volume m³/day per pixel.

    Parameters:
    - da_etha: xarray.DataArray with dimensions (time, y, x) in mm/day
    - pixel_area_m2: scalar or 2D array of pixel area in m²

    Returns:
    - xarray.DataArray with volume m³/day per pixel, same dims as da_etha
    """
    # Convert mm to meters
    et_m_per_day = da_etha / 1000
    volume_m3_per_day = et_m_per_day * pixel_area_m2
    return volume_m3_per_day


def aggregate_volume(da_volume, freq='M'):
    """
    Aggregate volume data over time.

    Parameters:
    - da_volume: xarray.DataArray with dimension 'time' and spatial dims
    - freq: resampling frequency string (e.g., 'M' for monthly, '6M' for semester)

    Returns:
    - xarray.DataArray aggregated over time with given frequency
    """
    return da_volume.resample(time=freq).sum()


def compute_water_accounting(ds, variable='ETa', freq='M'):
    """
    Compute water accounting volumes aggregated by time frequency.

    Parameters:
    - ds: xarray.Dataset with 'ETa' variable in mm/day
    - variable: variable name for ETa
    - freq: time resampling frequency ('M' = month, '6M' = semester)

    Returns:
    - xarray.DataArray of volume (m³) aggregated by freq, dims (time, y, x)
    """
    da_etha = ds[variable]

    # Compute pixel area (assume uniform pixel size in meters)
    pixel_area = compute_pixel_area(da_etha)

    # Convert ETa mm/day to m³/day per pixel
    da_volume = et_mm_day_to_m3_day(da_etha, pixel_area)

    # Aggregate volumes over the requested period (e.g., monthly)
    da_volume_agg = aggregate_volume(da_volume, freq=freq)

    return da_volume_agg



def plot_monthly_et(monthly_ds, var='ETa_monthly_sum'):
    """
    Plot spatially averaged monthly ETa.
    """
    # Average spatially (x, y dims) to get time series
    monthly_mean = monthly_ds[var].mean(dim=['x', 'y'], skipna=True)
    
    plt.figure(figsize=(12, 5))
    monthly_mean.plot(marker='o')
    plt.title('Monthly Total ETa (mm/month) - Spatial Average')
    plt.ylabel('ETa (mm/month)')
    plt.xlabel('Time')
    plt.grid(True)
    plt.show()

