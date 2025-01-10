'''
A class for analyzing evapotranspiration (ET) data using xarray.

This class provides methods to compute ratios of actual evapotranspiration (ETa) to potential evapotranspiration (ETp),
identify thresholds for decision-making based on changes in these ratios, and calculate rolling time means.

Attributes:
    ETa_name (str): Name of the variable representing actual evapotranspiration in the dataset. 
                    Default is 'ACT. ETRA'.
    ETp_name (str): Name of the variable representing potential evapotranspiration in the dataset. 
                    Default is 'ETp'.
    threshold_local (float): Threshold value for identifying significant changes in local ETa/ETp ratios. 
                              Default is -0.25.
    threshold_regional (float): Threshold value for identifying significant changes in regional ETa/ETp ratios. 
                                Default is -0.25.
    stat (str): Statistical operation to apply to ETa/ETp ratios. Options include 'mean', 'sum', etc. 
                Default is 'mean'.
'''
from dataclasses import dataclass
import xarray as xr
import numpy as np

@dataclass
class ETAnalysis:
    ETa_name: str = 'ACT. ETRA'
    ETp_name: str = 'ETp'
    threshold_local: float = -0.25
    threshold_regional: float = -0.25


    def compute_ratio_ETap_local(
        self,
        ds_analysis: xr.Dataset,
        ETa_name: str = "ACT. ETRA",
        ETp_name: str = "ETp",
        time_window: int = None,
    ) -> xr.Dataset:
        """
        Computes the local ETa/ETp ratio and its temporal differences.
    
        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing ETa and ETp data.
        ETa_name : str, optional
            The variable name for ETa. Default is 'ACT. ETRA'.
        ETp_name : str, optional
            The variable name for ETp. Default is 'ETp'.
        time_window : int, optional
            The rolling time window size for temporal averaging. Default is None.
    
        Returns
        -------
        xr.Dataset
            The dataset with added local ETa/ETp ratio and temporal differences.
        """
        # Compute the local ratio of ETa/ETp
        ds_analysis["ratio_ETap_local"] = ds_analysis[ETa_name] / ds_analysis[ETp_name]
    
        # Compute the absolute temporal difference of the local ratio
        ds_analysis["ratio_ETap_local_diff"] = abs(
            ds_analysis["ratio_ETap_local"].diff(dim="time")
        )
    
        # Apply rolling time-window mean if time_window is specified
        if time_window is not None:
            ds_analysis = self.apply_time_window_mean(
                ds_analysis, variable="ratio_ETap_local", time_window=time_window
            )
    
        return ds_analysis

    def compute_ratio_ETap_regional(
        self,
        ds_analysis: xr.Dataset,
        ETa_name: str = "ACT. ETRA",
        ETp_name: str = "ETp",
        stat: str = "mean",
        window_size_x: int = 10,  # Window size in km for regional averaging
        time_window: int = None,  # Rolling time window size
    ) -> xr.Dataset:
        """
        Computes the regional ETa/ETp ratio and its temporal differences.
    
        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing ETa and ETp data.
        ETa_name : str, optional
            The variable name for ETa. Default is 'ACT. ETRA'.
        ETp_name : str, optional
            The variable name for ETp. Default is 'ETp'.
        stat : str, optional
            The statistic to compute for regional aggregation (e.g., 'mean'). Default is 'mean'.
        window_size_x : int, optional
            The spatial window size in kilometers for regional averaging. Default is 10.
        time_window : int, optional
            The rolling time window size for temporal averaging. Default is None.
    
        Returns
        -------
        xr.Dataset
            The dataset with added regional ETa/ETp ratio and temporal differences.
        """
        if stat == "mean":
            # Compute regional ETa and ETp
            reg_analysis = self.compute_regional_ETap(
                ds_analysis, stat=stat, window_size_x=window_size_x
            )
    
            # Compute the regional ratio of ETa/ETp
            ds_analysis["ratio_ETap_regional_spatial_avg"] = (
                reg_analysis[ETa_name] / reg_analysis[ETp_name]
            )
    
            # Compute the absolute temporal difference of the regional ratio
            ds_analysis["ratio_ETap_regional_diff"] = abs(
                ds_analysis["ratio_ETap_regional_spatial_avg"].diff(dim="time")
            )
    
            # Apply rolling time-window mean if time_window is specified
            if time_window is not None:
                ds_analysis = self.apply_time_window_mean(
                    ds_analysis, variable="ratio_ETap_regional_spatial_avg", time_window=time_window
                )
    
        return ds_analysis
    
    
    def compute_regional_ETap(self, 
                              ds_analysis: xr.Dataset, stat: str, window_size_x: int) -> xr.Dataset:
        """
        Placeholder function to compute regional ETa and ETp.
    
        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing ETa and ETp data.
        stat : str
            The statistic to compute for regional aggregation (e.g., 'mean').
        window_size_x : int
            The spatial window size in kilometers for regional averaging.
    
        Returns
        -------
        xr.Dataset
            A dataset containing spatially averaged ETa and ETp.
        """
        # Implement spatial aggregation logic here
        # This is a placeholder for the actual implementation
        return ds_analysis
    
    
    def apply_time_window_mean(self,
                               ds_analysis: xr.Dataset, variable: str, time_window: int) -> xr.Dataset:
        """
        Applies a rolling time-window mean to a specified variable.
    
        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing the variable to process.
        variable : str
            The name of the variable to which the rolling mean is applied.
        time_window : int
            The rolling time window size.
    
        Returns
        -------
        xr.Dataset
            The dataset with the time-averaged variable added.
        """
        time_diff = np.diff(ds_analysis["time"].values)
        time_diff_days = time_diff / np.timedelta64(1, "D")
        time_mask = np.concatenate([[True], time_diff_days <= 1.1])
    
        ds_analysis[f"{variable}_time_avg"] = (
            ds_analysis[variable]
            .where(time_mask[:, np.newaxis, np.newaxis], drop=False)
            .rolling(time=time_window, center=True)
            .mean()
        )
    
        return ds_analysis


    def compute_bool_threshold_decision_local(self, ds_analysis: xr.Dataset, 
                                              checkp: str = "ratio_ETap_local_time_avg") -> xr.Dataset:
        """
        Computes a boolean threshold decision for the local ETa/ETp ratio.

        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing the local ETa/ETp ratio data.
        checkp : str, optional
            The name of the variable in the dataset to check against the threshold.
            Default is 'ratio_ETap_local_time_avg'.

        Returns
        -------
        xr.Dataset
            The updated dataset with a new variable `threshold_local` indicating where
            the specified variable exceeds the threshold.
        """
        ds_analysis["threshold_local"] = xr.where(ds_analysis[checkp] > self.threshold_local, True, False)
        return ds_analysis
    
    
    # def compute_bool_threshold_decision_regional(self, ds_analysis: xr.Dataset) -> xr.Dataset:
    #     ds_analysis["threshold_regional"] = xr.DataArray(False, 
    #                                                       coords=ds_analysis.coords, 
    #                                                       dims=ds_analysis.dims)
    #     checkon = ds_analysis["ratio_ETap_regional_diff"]
    #     ds_analysis["threshold_regional"] = xr.where(checkon <= self.threshold_regional, True, False)

    #     return ds_analysis
    
    # def compute_bool_threshold_decision_regional(ds_analysis,
    #                                              threshold_regional=0.25,
    #                                              checkp='ratio_ETap_regional_spatial_avg_time_avg'
    #                                              ):
        
    #     ds_analysis["threshold_regional"] = xr.DataArray(False, 
    #                                                   coords=ds_analysis.coords, 
    #                                                   dims=ds_analysis.dims
    #                                                      )
    #     checkon = ds_analysis[checkp]
    #     ds_analysis["threshold_regional"] = xr.where(checkon > threshold_regional, True, False)
    #     return ds_analysis
    
    def compute_bool_threshold_decision_regional(self, 
                                                 ds_analysis: xr.Dataset, 
                                                 checkp: str = "ratio_ETap_regional_spatial_avg_time_avg") -> xr.Dataset:
        """
        Computes a boolean threshold decision for the regional ETa/ETp ratio.

        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing the regional ETa/ETp ratio data.
        checkp : str, optional
            The name of the variable in the dataset to check against the threshold.
            Default is 'ratio_ETap_regional_spatial_avg_time_avg'.

        Returns
        -------
        xr.Dataset
            The updated dataset with a new variable `threshold_regional` indicating where
            the specified variable exceeds the threshold.
        """
        ds_analysis["threshold_regional"] = xr.where(ds_analysis[checkp] > self.threshold_regional, True, False)
        return ds_analysis
        

    def define_decision_thresholds(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        ds_analysis = self.compute_bool_threshold_decision_local(ds_analysis)
        ds_analysis = self.compute_bool_threshold_decision_regional(ds_analysis)
        
        return ds_analysis

    def compute_rolling_time_mean(self, ds_analysis: xr.Dataset) -> xr.Dataset:
        return ds_analysis.rolling(time=3).mean()


    def apply_rules_rain(self, decision_ds: xr.Dataset) -> xr.Dataset:
        """
        Applies the rules for detecting rain events based on the change in regional and local ETa/ETp ratios.

        Parameters
        ----------
        decision_ds : xr.Dataset
            An xarray Dataset containing the necessary variables to apply the rules.

        Returns
        -------
        xr.Dataset
            The updated xarray Dataset with new conditions ('condRain1', 'condRain2', 'condRain').
        """
        # Condition 1: Threshold for regional ETa/ETp ratio
        decision_ds['condRain1'] = decision_ds['threshold_regional'] == 1
        
        # Condition 2: Comparison between regional and local ETa/ETp ratios
        decision_ds['condRain2'] = (
                                    abs(decision_ds['ratio_ETap_regional_spatial_avg_time_avg']) 
                                    >= abs(decision_ds['ratio_ETap_local_time_avg'])
                                    )
        
        # Final condition for rain
        decision_ds['condRain'] = decision_ds['condRain1'] & decision_ds['condRain2']
        
        return decision_ds

    def apply_rules_irrigation(self, decision_ds: xr.Dataset) -> xr.Dataset:
        """
        Applies the rules for detecting irrigation events based on the change in local and regional ETa/ETp ratios.

        Parameters
        ----------
        decision_ds : xr.Dataset
            An xarray Dataset containing the necessary variables to apply the rules.

        Returns
        -------
        xr.Dataset
            The updated xarray Dataset with new conditions ('condIrrigation1', 'condIrrigation2', 'condIrrigation').
        """
        # Condition 1: Threshold for local ETa/ETp ratio
        decision_ds['condIrrigation1'] = decision_ds['threshold_local'] == 1
        
        # Condition 2: Comparison between local and regional ETa/ETp ratios (local ratio must be greater than 1.5 times the regional ratio)
        a = abs(decision_ds['ratio_ETap_local_time_avg'])
        b = abs(1.5 * decision_ds['ratio_ETap_regional_spatial_avg_time_avg'])
        decision_ds['condIrrigation2'] = a > b
        
        # Final condition for irrigation
        decision_ds['condIrrigation'] = decision_ds['condIrrigation1'] & decision_ds['condIrrigation2']
        
        return decision_ds
    
    def classify_event(
        self,
        decision_ds: xr.Dataset,
        irrigation_condition: str = "condIrrigation",
        rain_condition: str = "condRain",
    ) -> xr.DataArray:
        """
        Classifies events into irrigation, rain, or no event based on conditions.
    
        Parameters
        ----------
        decision_ds : xr.Dataset
            The dataset containing the event classification conditions.
        irrigation_condition : str, optional
            The name of the variable indicating irrigation conditions. Default is "condIrrigation".
        rain_condition : str, optional
            The name of the variable indicating rain conditions. Default is "condRain".
    
        Returns
        -------
        xr.DataArray
            An array representing event types:
            1 = Irrigation event
            2 = Rain event
            0 = No event
        """
        event_type = xr.where(
            decision_ds[irrigation_condition],
            1,
            xr.where(decision_ds[rain_condition], 2, 0),
        )
        return event_type


    def irrigation_delineation(self,
                               decision_ds,
                               threshold_local=0.25,
                               threshold_regional=0.25,
                               time_window=10,
                               ):
        
        # Compute local and regional ETa/ETp ratios
        decision_ds = self.compute_ratio_ETap_local(decision_ds,time_window=time_window)
        decision_ds = self.compute_ratio_ETap_regional(decision_ds,time_window=time_window)

        # Apply local and regional threshold decision rules
        decision_ds = self.compute_bool_threshold_decision_local(decision_ds)
        decision_ds = self.compute_bool_threshold_decision_regional(decision_ds)

        # Drop initial time steps based on time mask
        time_mask = decision_ds['time'] > np.timedelta64(0, 'D')
        decision_ds = decision_ds.where(time_mask, drop=True)

        # Apply specific rules for rain and irrigation
        decision_ds = self.apply_rules_rain(decision_ds)
        decision_ds = self.apply_rules_irrigation(decision_ds)

        # Classify events based on delineation rules
        event_type = self.classify_event(decision_ds)
        
        # Create a dataset event_type of dim x,y,times
        # -------------------------------------------------------------------------
        # event_type = xr.DataArray(0, 
        #                           coords=decision_ds.coords, 
        #                           dims=decision_ds.dims
        #                           )
        # event_type = event_type.where(time_mask,drop=True)
    
        # Drop time 0 as the analysis is conducted on values differences (ti - t0)
        # -------------------------------------------------------------------------
        # time_mask = decision_ds['time'] > np.timedelta64(time_window, 'D')

        return decision_ds, event_type

