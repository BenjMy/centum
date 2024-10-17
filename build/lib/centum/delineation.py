from dataclasses import dataclass
import xarray as xr

@dataclass
class ETAnalysisConfig:
    """
    Configuration class for ET analysis parameters.

    Attributes:
        ETa_name (str): Name of the actual ETa variable in the dataset.
        ETp_name (str): Name of the reference ETp variable in the dataset.
        threshold_local (float): Threshold for local ETa/ETp decisions.
        threshold_regional (float): Threshold for regional ETa/ETp decisions.
        stat (str): Statistical measure to compute (e.g., 'mean').
    """
    ETa_name: str = 'ACT. ETRA'
    ETp_name: str = 'ETp'
    threshold_local: float = -0.25
    threshold_regional: float = -0.25
    stat: str = 'mean'


def compute_ratio_ETap_regional(ds_analysis: xr.Dataset, config: ETAnalysisConfig) -> xr.Dataset:
    """
    Compute the regional ETa/ETp ratio and its mean over specified dimensions.

    Parameters:
        ds_analysis (xr.Dataset): The xarray Dataset containing ETa and ETp variables.
        config (ETAnalysisConfig): Configuration object containing analysis parameters.

    Returns:
        xr.Dataset: The updated dataset with the computed ETa/ETp ratio and its mean.
    """
    ds_analysis["ratio_ETap_regional"] = ds_analysis[config.ETa_name] / ds_analysis[config.ETp_name]

    if config.stat == 'mean':
        mean = ds_analysis["ratio_ETap_regional"].mean(dim=['x', 'y'])
        mean_dataarray = xr.full_like(ds_analysis['ratio_ETap_regional'], fill_value=0)
        for i, m in enumerate(mean.values):
            timei = mean_dataarray.time[i]
            mean_dataarray.loc[{'time': timei}] = m
            
        ds_analysis["ratio_ETap_regional_mean"] = mean_dataarray
        ds_analysis["ratio_ETap_regional_diff"] = ds_analysis["ratio_ETap_regional_mean"].diff(dim='time')
    
    return ds_analysis


def compute_bool_threshold_decision_local(ds_analysis: xr.Dataset, config: ETAnalysisConfig) -> xr.Dataset:
    """
    Compute a boolean threshold decision for local ETa/ETp changes.

    Parameters:
        ds_analysis (xr.Dataset): The xarray Dataset containing ETa/ETp ratio changes.
        config (ETAnalysisConfig): Configuration object containing analysis parameters.

    Returns:
        xr.Dataset: The updated dataset with the boolean threshold decision for local changes.
    """
    ds_analysis["threshold_local"] = xr.DataArray(False, 
                                                  coords=ds_analysis.coords, 
                                                  dims=ds_analysis.dims)
    checkon = ds_analysis["ratio_ETap_local_diff"]
    ds_analysis["threshold_local"] = xr.where(checkon <= config.threshold_local, True, False)

    return ds_analysis


def compute_bool_threshold_decision_regional(ds_analysis: xr.Dataset, config: ETAnalysisConfig) -> xr.Dataset:
    """
    Compute a boolean threshold decision for regional ETa/ETp changes.

    Parameters:
        ds_analysis (xr.Dataset): The xarray Dataset containing ETa/ETp ratio changes.
        config (ETAnalysisConfig): Configuration object containing analysis parameters.

    Returns:
        xr.Dataset: The updated dataset with the boolean threshold decision for regional changes.
    """
    ds_analysis["threshold_regional"] = xr.DataArray(False, 
                                                      coords=ds_analysis.coords, 
                                                      dims=ds_analysis.dims)
    checkon = ds_analysis["ratio_ETap_regional_diff"]
    ds_analysis["threshold_regional"] = xr.where(checkon <= config.threshold_regional, True, False)

    return ds_analysis


def define_decision_thresholds(ds_analysis: xr.Dataset, config: ETAnalysisConfig) -> xr.Dataset:
    """
    Define local and regional decision thresholds for ETa/ETp analysis.

    Parameters:
        ds_analysis (xr.Dataset): The xarray Dataset for analysis.
        config (ETAnalysisConfig): Configuration object containing analysis parameters.

    Returns:
        xr.Dataset: The updated dataset with both local and regional threshold decisions.
    """
    ds_analysis = compute_bool_threshold_decision_local(ds_analysis, config)
    ds_analysis = compute_bool_threshold_decision_regional(ds_analysis, config)
    
    return ds_analysis


def compute_rolling_time_mean(ds_analysis: xr.Dataset) -> xr.Dataset:
    """
    Compute the rolling mean over time for the dataset.

    Parameters:
        ds_analysis (xr.Dataset): The xarray Dataset for which to compute the rolling mean.

    Returns:
        xr.Dataset: The updated dataset with the rolling mean computed.
    """
    return ds_analysis.rolling(time=3).mean()
