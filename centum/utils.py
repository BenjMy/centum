'''
Utilities for analyzing evapotranspiration (ET) data using xarray.
'''
import xarray as xr
from rasterio.enums import Resampling  # Import Resampling enum

def get_CLC_code_def():
    
    clc_codes = {
        "111": "Continuous urban fabric",
        "112": "Discontinuous urban fabric",
        "121": "Industrial or commercial units",
        "122": "Road and rail networks and associated land",
        "123": "Port areas",
        "124": "Airports",
        "131": "Mineral extraction sites",
        "132": "Dump sites",
        "133": "Construction sites",
        "141": "Green urban areas",
        "142": "Sport and leisure facilities",
        "211": "Non-irrigated arable land",
        "212": "Permanently irrigated land",
        "213": "Rice fields",
        "221": "Vineyards",
        "222": "Fruit trees and berry plantations",
        "223": "Olive groves",
        "231": "Pastures",
        "241": "Annual crops associated with permanent crops",
        "242": "Complex cultivation patterns",
        "243": "Land principally occupied by agriculture, with significant areas of natural vegetation",
        "244": "Agro-forestry areas",
        "311": "Broad-leaved forest",
        "312": "Coniferous forest",
        "313": "Mixed forest",
        "321": "Natural grasslands",
        "322": "Moors and heathland",
        "323": "Sclerophyllous vegetation",
        "324": "Transitional woodland-shrub",
        "331": "Beaches, dunes, sands",
        "332": "Bare rocks",
        "333": "Sparsely vegetated areas",
        "334": "Burnt areas",
        "335": "Glaciers and perpetual snow",
        "411": "Inland marshes",
        "412": "Peat bogs",
        "421": "Salt marshes",
        "422": "Salines",
        "423": "Intertidal flats",
        "511": "Water courses",
        "512": "Water bodies",
        "521": "Coastal lagoons",
        "522": "Estuaries",
        "523": "Sea and ocean"
    }
    
    return clc_codes



def get_resolution(ds, crs=None):
    """
    Calculate the spatial resolution of a rioxarray-enabled dataset.

    Parameters:
    - ds: xarray.Dataset or DataArray with spatial coordinates
    - crs: optional string or CRS object, e.g. 'EPSG:32630' or None

    Returns:
    - tuple (x_res, y_res) in units of the CRS
    """
    # Check if dataset has CRS
    has_crs = ds.rio.crs is not None

    if not has_crs:
        if crs is None:
            raise ValueError("Dataset has no CRS and no 'crs' argument was provided.")
        # Assign the CRS without reprojecting
        ds = ds.rio.write_crs(crs, inplace=False)
    else:
        # If CRS exists and crs argument is provided, reproject if different
        if crs is not None:
            if str(ds.rio.crs) != str(crs):
                ds = ds.rio.reproject(crs)

    # Now get resolution
    resolution = ds.rio.resolution()  # returns (xres, yres)
    return resolution


def remap_to_coarser(ds_fine, ds_coarse):
    """
    Remap the fine dataset to the grid of the coarse dataset using rioxarray.

    Parameters:
    - ds_fine: xarray Dataset with finer resolution
    - ds_coarse: xarray Dataset with coarser resolution
    - variable: variable name to remap

    Returns:
    - xarray Dataset: Coarse dataset with remapped variable from the fine dataset
    """
    # Reproject the fine dataset to match the coarse dataset
    # ds_fine_remapped = ds_fine.rio.reproject_match(ds_coarse, 
    #                                                 resampling=Resampling.nearest
    #                                                 )

    ds_remapped = xr.Dataset()
    
    for var in ds_fine.data_vars:
        # Step 1: Create a boolean valid-data mask
        valid_mask = ~ds_fine[var].isnull()
    
        # Step 2: Convert to float32 for reprojection (True → 1.0, False → NaN)
        valid_mask_float = valid_mask.astype("float32")
    
        # Step 3: Reproject the float mask to the coarse grid
        valid_mask_remapped_float = valid_mask_float.rio.reproject_match(
            ds_coarse, resampling=Resampling.nearest
        )
    
        # Step 4: Convert back to boolean mask
        valid_mask_remapped = valid_mask_remapped_float == 1.0
    
        # Step 5: Fill NaNs in the original fine variable
        ds_filled = ds_fine[var].fillna(0)
    
        # Step 6: Reproject the filled variable
        ds_var_remapped = ds_filled.rio.reproject_match(
            ds_coarse, resampling=Resampling.nearest
        )
    
        # Step 7: Mask out originally invalid areas
        ds_remapped[f'{var}_remapped'] = ds_var_remapped.where(valid_mask_remapped)

    return ds_remapped

def match_resolution(ds1, ds2):
    """
    Check which dataset has the finest resolution and remap the finest to the coarser one.

    Parameters:
    - ds1: First xarray Dataset
    - ds2: Second xarray Dataset
    - variable: variable name to remap

    Returns:
    - xarray Dataset: Dataset with the coarser resolution, including the remapped variable
    """
    # Calculate resolutions
    res1 = get_resolution(ds1)
    res2 = get_resolution(ds2)

    print(f"Resolution of Dataset 1: {res1}")
    print(f"Resolution of Dataset 2: {res2}")

    # Determine which dataset is finer
    if res1[0] < res2[0] and res1[1] < res2[1]:
        print("Dataset 1 has finer resolution. Remapping to Dataset 2 grid.")
        return remap_to_coarser(ds1, ds2)
    else:
        print("Dataset 2 has finer resolution. Remapping to Dataset 1 grid.")
        return remap_to_coarser(ds2, ds1)
    
