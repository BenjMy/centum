from dataclasses import dataclass
import xarray as xr

@dataclass
class ETAnalysis:
    ETa_name: str = 'ACT. ETRA'
    ETp_name: str = 'ETp'
    threshold_local: float = -0.25
    threshold_regional: float = -0.25
    stat: str = 'mean'

    def compute_ratio_ETap_regional(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        ds_analysis["ratio_ETap_regional"] = ds_analysis[self.ETa_name] / ds_analysis[self.ETp_name]

        if self.stat == 'mean':
            mean = ds_analysis["ratio_ETap_regional"].mean(dim=['x', 'y'])
            mean_dataarray = xr.full_like(ds_analysis['ratio_ETap_regional'], fill_value=0)
            for i, m in enumerate(mean.values):
                timei = mean_dataarray.time[i]
                mean_dataarray.loc[{'time': timei}] = m

            ds_analysis["ratio_ETap_regional_mean"] = mean_dataarray
            ds_analysis["ratio_ETap_regional_diff"] = ds_analysis["ratio_ETap_regional_mean"].diff(dim='time')

        return ds_analysis

    def compute_bool_threshold_decision_local(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        ds_analysis["threshold_local"] = xr.DataArray(False, 
                                                      coords=ds_analysis.coords, 
                                                      dims=ds_analysis.dims)
        checkon = ds_analysis["ratio_ETap_local_diff"]
        ds_analysis["threshold_local"] = xr.where(checkon <= self.threshold_local, True, False)

        return ds_analysis

    def compute_bool_threshold_decision_regional(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        ds_analysis["threshold_regional"] = xr.DataArray(False, 
                                                          coords=ds_analysis.coords, 
                                                          dims=ds_analysis.dims)
        checkon = ds_analysis["ratio_ETap_regional_diff"]
        ds_analysis["threshold_regional"] = xr.where(checkon <= self.threshold_regional, True, False)

        return ds_analysis

    def define_decision_thresholds(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        ds_analysis = self.compute_bool_threshold_decision_local(ds_analysis)
        ds_analysis = self.compute_bool_threshold_decision_regional(ds_analysis)
        
        return ds_analysis

    def compute_rolling_time_mean(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        return ds_analysis.rolling(time=3).mean()
