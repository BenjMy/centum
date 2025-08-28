import centum.delineation
import centum.irrigation_district
import centum.plotting
import centum.utils
import xarray as xr
import matplotlib.pyplot as plt

import numpy as np
import rioxarray  # you already have it
import pandas as pd


from dataclasses import dataclass, field
import xarray as xr
import logging
from dataclasses import dataclass, field
import xarray as xr
import logging
from typing import Tuple

@dataclass
class Accounting:
    ds_baseline: xr.Dataset
    ds_EO: xr.Dataset
    variable: tuple[str, str] = ("ETa", "ETa")
    reference_period: tuple = None  # (start, end), as datetime-like strings or pd.Timestamp
    logger: logging.Logger = field(default=None, repr=False)
    freq='M'
    
    def __post_init__(self):
        if not check_dimensions_consistent(self.ds_baseline, self.ds_EO):
            raise ValueError("❌ Dimensions of the datasets are not consistent.")
        if self.logger:
            self.logger.info("✅ Datasets passed dimension consistency check")
    
        if not check_time_consistent(self.ds_baseline, self.ds_EO):
            raise ValueError("❌ Time coordinates of the datasets are not consistent.")
        if self.logger:
            self.logger.info("✅ Datasets passed time coordinate consistency check")
    
        if not check_crs_consistent(self.ds_baseline, self.ds_EO):
            raise ValueError("❌ CRS of the datasets are not consistent.")
        if self.logger:
            self.logger.info("✅ Datasets passed CRS consistency check")
    
        # NaN mask at t0 consistency check
        try:
            check_nan_mask_t0_consistent(self.ds_baseline, self.ds_EO, variable=self.variable)
            if self.logger:
                self.logger.info("✅ NaN masks at t0 are consistent between datasets.")
        except ValueError as e:
            if self.logger:
                self.logger.error(f"❌ {e}")
            raise
    
        # NaN counts stable over time checks for both datasets
        try:
            check_nb_of_nan_over_time(self.ds_baseline, variable=self.variable[0])
            if self.logger:
                self.logger.info("✅ NaN counts are consistent over time in baseline dataset.")
        except ValueError as e:
            if self.logger:
                self.logger.error(f"❌ {e}")
            raise
    
        try:
            check_nb_of_nan_over_time(self.ds_EO, variable=self.variable[1])
            if self.logger:
                self.logger.info("✅ NaN counts are consistent over time in EO dataset.")
        except ValueError as e:
            if self.logger:
                self.logger.error(f"❌ {e}")
            raise


    def run(self):
        if self.logger:
            self.logger.info("📊 Starting accounting analysis")

        ds_eo = self.ds_EO
        ds_baseline = self.ds_baseline

        ds_net_irrigation = compute_net_irrigation(ds_baseline, ds_eo, variables=self.variable, freq=self.freq)
        
        if self.logger:
            self.logger.info("✅ Accounting analysis complete")
            
        return ds_net_irrigation



def compute_water_accounting(ds, variable='ETa', freq='M'):
    """
    Compute water accounting volumes and mean ETa aggregated by time frequency.

    Parameters:
    - ds: xarray.Dataset with ETa in mm/day
    - variable: variable name for ETa
    - freq: resampling frequency (e.g., 'M', '6M', 'A')

    Returns:
    - xarray.Dataset with:
        - 'volume': ET volume in m³ per pixel and period
        - 'volume_mm': sum of ETa in mm for the period
    """
    da_etha = ds[variable]

    # Compute pixel area assuming uniform spacing and UTM coordinates
    pixel_area = compute_pixel_area(da_etha)

    # Convert ETa (mm/day) to volume (m³/day)
    da_volume_day = et_mm_day_to_m3_day(da_etha, pixel_area)

    # Resample both to the desired frequency
    da_volume = da_volume_day.resample(time=freq).sum()
    da_volume.attrs.update({
        'units': f'm³/{freq}',
        'long_name': f'Aggregated {variable} volume for all pixels ({freq})'
    })

    da_volume_mm = da_etha.resample(time=freq).sum()
    da_volume_mm.attrs.update({
        'units': f'mm/{freq}',
        'long_name': f'Aggregated {variable} depth for all pixels ({freq})'
    })

    ds_out = xr.Dataset({
        'volume': da_volume,
        'volume_mm': da_volume_mm
    })

    return ds_out


def compute_net_irrigation(ds_baseline, ds_eo, variables=('ETa', 'ETa'), freq='M'):
    """
    Compute net irrigation as the difference between ETa baseline and ETa EO.

    Parameters:
    - ds_baseline: xarray.Dataset with baseline 'ETa' variable in mm/day
    - ds_eo: xarray.Dataset with EO 'ETa' variable in mm/day
    - variable: variable name for ETa
    - freq: time resampling frequency ('M' = month, '6M' = semester)

    Returns:
    - xarray.DataArray of net irrigation volume (m³) aggregated by freq, dims (time, y, x)
    """
    ds_volume_baseline = compute_water_accounting(ds_baseline, variable=variables[0], freq=freq)
    ds_volume_eo = compute_water_accounting(ds_eo, variable=variables[1], freq=freq)

    ds_net_irrigation =  ds_volume_eo - ds_volume_baseline
    ds_net_irrigation.attrs['description'] = "Net irrigation volume and depth (baseline - EO)"
    return ds_net_irrigation

     
def compute_pixel_area(da):
    """
    Compute the approximate area (m²) of each pixel based on coordinate spacing.
    Assumes coordinates are in meters (e.g., UTM projection).

    Parameters:
    - da: xarray.DataArray with spatial dims 'x' and 'y' and coordinate values in meters.

    Returns:
    - 2D numpy array of pixel areas in m² with shape (y, x)
    """
    # Normalize possible coordinate names
    x_dim = 'x' if 'x' in da.coords else 'X' if 'X' in da.coords else None
    y_dim = 'y' if 'y' in da.coords else 'Y' if 'Y' in da.coords else None
    
    if x_dim is None or y_dim is None:
        raise ValueError("DataArray must have spatial coordinates 'x'/'X' and 'y'/'Y'.")

    dx = np.abs(np.diff(da[x_dim].values).mean())
    dy = np.abs(np.diff(da[y_dim].values).mean())
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
    Compute water accounting volumes and mean ETa aggregated by time frequency.

    Parameters:
    - ds: xarray.Dataset with ETa in mm/day
    - variable: variable name for ETa
    - freq: resampling frequency (e.g., 'M', '6M', 'A')

    Returns:
    - xarray.Dataset with:
        - 'volume': ET volume in m³ per pixel and period
        - 'ETa_mean': mean daily ETa in mm/day for same periods
    """
    da_etha = ds[variable]

    # Compute pixel area assuming uniform spacing and UTM coordinates
    pixel_area = compute_pixel_area(da_etha)

    # Convert ETa (mm/day) to volume (m³/day)
    da_volume_day = et_mm_day_to_m3_day(da_etha, pixel_area)

    # Resample both to the desired frequency
    da_volume = da_volume_day.resample(time=freq).sum()/pixel_area
    da_volume.attrs.update({
        'units': f'm³/{freq}',
        'long_name': f'Aggregated {variable} volume for all pixel ({freq})'
    })

    da_volume_mm = da_etha.resample(time=freq).sum()/pixel_area
    da_volume_mm.attrs.update({
        'units': 'mm/{freq}',
        'long_name': f'Aggregated {variable} volume for all pixel ({freq})'
    })

    # Create unified dataset
    ds_out = xr.Dataset({
        'volume': da_volume,
        'volume_mm': da_volume_mm
    })

    return ds_out



def check_dimensions_consistent(ds1: xr.Dataset, ds2: xr.Dataset) -> bool:
    """
    Check if dimensions and time coordinates are consistent between two xarray Datasets.

    Parameters:
    - ds1: First xarray Dataset
    - ds2: Second xarray Dataset

    Returns:
    - bool: True if dimensions and time coordinates are consistent, False otherwise
    """
    # Check if dimension names are the same
    if set(ds1.dims) != set(ds2.dims):
        print("❌ Dimension names are not consistent.")
        print(f"Dataset 1 dimensions: {ds1.dims}")
        print(f"Dataset 2 dimensions: {ds2.dims}")
        return False

    # Check if dimension sizes are the same
    for dim in ds1.dims:
        if ds1.sizes[dim] != ds2.sizes[dim]:
            print(f"❌ Dimension size for '{dim}' is not consistent.")
            print(f"Size in Dataset 1: {ds1.sizes[dim]}")
            print(f"Size in Dataset 2: {ds2.sizes[dim]}")
            return False

    # Check time coordinate specifically
    if "time" not in ds1.coords or "time" not in ds2.coords:
        print("❌ One or both datasets do not contain a 'time' coordinate.")
        return False

    if not ds1["time"].equals(ds2["time"]):
        print("❌ Time coordinates are not identical.")
        return False

    print("✅ All dimensions and time coordinates are consistent.")
    return True

def check_time_consistent(ds1: xr.Dataset, ds2: xr.Dataset) -> bool:
    """
    Check if both datasets have a 'time' coordinate and that they are identical.

    Parameters:
    - ds1: First xarray Dataset
    - ds2: Second xarray Dataset

    Returns:
    - bool: True if 'time' coordinate exists and matches exactly, False otherwise
    """
    if "time" not in ds1.coords or "time" not in ds2.coords:
        print("❌ One or both datasets are missing the 'time' coordinate.")
        return False

    if not ds1["time"].equals(ds2["time"]):
        print("❌ Time coordinates are not identical.")
        return False

    print("✅ Time coordinates are consistent.")
    return True

def check_crs_consistent(ds1: xr.Dataset, ds2: xr.Dataset) -> bool:
    """
    Check if CRS is defined and consistent between two rioxarray-enabled datasets.

    Parameters:
    - ds1: First xarray Dataset
    - ds2: Second xarray Dataset

    Returns:
    - bool: True if CRS matches, False otherwise
    """
    crs1 = ds1.rio.crs
    crs2 = ds2.rio.crs

    if crs1 != crs2:
        print("❌ CRS mismatch:")
        print(f"Dataset 1 CRS: {crs1}")
        print(f"Dataset 2 CRS: {crs2}")
        return False

    print("✅ CRS is consistent.")
    return True


def check_nan_mask_t0_consistent(ds1: xr.Dataset, ds2: xr.Dataset, variable: Tuple[str, str] = ('ETa', 'ETa')) -> None:
    """
    Check if NaN mask at the first time step is spatially consistent between two datasets
    for the given pair of variables.

    Raises ValueError if masks differ.
    """
    da1 = ds1[variable[0]].isel(time=0)
    da2 = ds2[variable[1]].isel(time=0)

    mask1 = da1.isnull()
    mask2 = da2.isnull()

    if not mask1.equals(mask2):
        raise ValueError("NaN masks at t0 are not consistent between the datasets.")
    else:
        print("NaN masks at t0 are consistent between datasets.")

def check_nb_of_nan_over_time(ds: xr.Dataset, variable: str = 'ETa'):
    da = ds[variable]
    spatial_dims = [dim for dim in da.dims if dim != 'time']
    nan_counts = da.isnull().sum(dim=spatial_dims)

    if not (nan_counts == nan_counts[0]).all():
        raise ValueError(f"Inconsistent NaN counts over time: {nan_counts.values}")
    else:
        print(f"NaN counts are consistent over time: {nan_counts[0].item()} NaNs per time step.")
        

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

