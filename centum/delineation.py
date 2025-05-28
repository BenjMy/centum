'''
A class for analyzing evapotranspiration (ET) data using xarray.

This class provides methods to compute ratios of actual evapotranspiration (ETa) to potential evapotranspiration (ETp),
identify thresholds for decision-making based on changes in these ratios, and calculate rolling time means.

Attributes:
    ETa_name (str): Name of the variable representing actual evapotranspiration in the dataset.
                    Default is 'ETa'.
    ETp_name (str): Name of the variable representing potential evapotranspiration in the dataset.
                    Default is 'ETp'.
    threshold_local (float): Threshold value for identifying significant changes in local ETa/ETp ratios.
                              Default is -0.25.
    threshold_regional (float): Threshold value for identifying significant changes in regional ETa/ETp ratios.
                                Default is -0.25.
    stat (str): Statistical operation to apply to ETa/ETp ratios. Options include 'mean', 'sum', etc.
                Default is 'mean'.
'''
from dataclasses import dataclass, field
import xarray as xr
import numpy as np
from rich.console import Console
from dask.diagnostics import ProgressBar
from rich.panel import Panel
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.text import Text
import logging
import os 


@dataclass
class ETAnalysis:
    
    ETa_name: str = 'ETa'
    ETp_name: str = 'ETp'
    threshold_local: float = -0.25
    threshold_regional: float = -0.25

    log_file: str = "ET_analysis_log.md"
    console: Console = field(default_factory=Console, init=False, repr=False)
    logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self):
        # Remove existing log file if it exists
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

        # Setup logger
        self.logger = logging.getLogger("ETAnalysisLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # prevent double logging or interference

        # Only add handlers if none exist
        if not self.logger.hasHandlers():
            # rich_handler = RichHandler(console=self.console, rich_tracebacks=True, markup=True)
            # rich_handler.setLevel(logging.INFO)
            
            file_handler = logging.FileHandler(self.log_file, mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            file_handler.setLevel(logging.DEBUG)

            # self.logger.addHandler(rich_handler)
            self.logger.addHandler(file_handler)

        self.logger.info("📋 ETAnalysis initialized")
        
        
    def log_panel(self, title: str, **kwargs):
        # Format content with rich markup for console display
        content_lines = [f"[bold]{key}:[/bold] {value}" for key, value in kwargs.items()]
        content = "\n".join(content_lines)
    
        # Compose markdown header and content lines
        md_title = f"# {title}"
        md_lines = [f"- **{key}:** {value}" for key, value in kwargs.items()]
        
        panel = kwargs.pop('panel', False)

        if panel:
            toconsole = Panel.fit(
                f"{title}\n\n{content}",
                title=title,
                border_style="green"
            )
        else:
            toconsole = Text()
            toconsole.append(md_title)
            toconsole.append("\n")
            for line in md_lines:
                toconsole.append("- ")
                toconsole.append(line)
                toconsole.append("\n")
        
        self.console.print(toconsole)

    
        # Log the title **without** timestamp (disable formatter temporarily)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                old_formatter = handler.formatter
                handler.setFormatter(logging.Formatter('%(message)s'))  # no timestamp
                self.logger.info(md_title)
                handler.setFormatter(old_formatter)  # restore timestamp formatter
                handler.flush()

        # Then log each detail line with timestamp
        for line in md_lines:
            self.logger.info(line)



    def check_data_validity(self, ds: xr.Dataset):
        """
        Perform pre-processing checks before irrigation delimitation.
    
        Parameters:
        ds (xr.Dataset): Input dataset containing ETa, ETp, and time dimensions.
    
        Raises:
        ValueError: If critical issues are found in the dataset.
        """
    
        issues = []
    
        # Check for missing time steps
        if 'time' not in ds:
            issues.append("❌ Time dimension is missing in the dataset.")
        else:
            time_diff = np.diff(ds['time'].values)
            expected_diff = np.timedelta64(1, 'D')  # Expected daily frequency
            if not np.all(time_diff == expected_diff):
                issues.append("⚠️ Time data gaps detected. Ensure daily ETa values are continuous.")
    
        # Check for missing pixels (NaNs in ETa or ETp)
        if self.ETa_name in ds:
            missing_pixels_ETA = ds[self.ETa_name].isnull().sum().item()
            if missing_pixels_ETA > 0:
                issues.append(f"⚠️ ETa contains {missing_pixels_ETA} missing pixels.")
        else:
            issues.append(f"❌ {self.ETa_name} variable is missing in the dataset.")
    
        if self.ETp_name in ds:
            missing_pixels_ETP = ds[self.ETp_name].isnull().sum().item()
            if missing_pixels_ETP > 0:
                issues.append(f"⚠️ ETp contains {missing_pixels_ETP} missing pixels.")
        else:
            issues.append(f"❌ {self.ETp_name} variable is missing in the dataset.")
    
        # Check CRS consistency
        if not hasattr(ds, 'crs'):
            issues.append("⚠️ CRS information is missing. Ensure all datasets use the same projection.")
    
        # Print warnings or raise errors
        if issues:
            for issue in issues:
                print(issue)
            raise ValueError("Data validation failed. Please address the above issues before proceeding.")
    
        print("✅ Data validation passed. Ready for irrigation delineation.")

    def compute_ratio_ETap_local(
        self,
        ds_analysis: xr.Dataset,
        ETa_name: str = "ETa",
        ETp_name: str = "ETp",
        time_window: int = None,
        **kwargs
    ) -> xr.Dataset:
        """
        Computes the local ETa/ETp ratio and its temporal differences.

        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing ETa and ETp data.
        ETa_name : str, optional
            The variable name for ETa. Default is 'ETa'.
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
                ds_analysis,
                variable="ratio_ETap_local",
                time_window=time_window
            )

        return ds_analysis

    def compute_ratio_ETap_regional(
        self,
        ds_analysis: xr.Dataset,
        ETa_name: str = "ETa",
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
            The variable name for ETa. Default is 'ETa'.
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
                ds_analysis, window_size_x=window_size_x,
                window_size_y=window_size_x
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
                    ds_analysis,
                    variable="ratio_ETap_regional_spatial_avg",
                    time_window=time_window
                )

        return ds_analysis


    def compute_regional_ETap(
        self,
        ds_analysis: xr.Dataset,
        window_size_x: int = 1000,  # Spatial window size in meters (default: 1 km)
        window_size_y: int = 1000,  # Spatial window size in meters (default: 1 km)
    ) -> xr.Dataset:
        """
        Computes the regional mean of ETa and ETp using a moving window.

        Parameters
        ----------
        ds_analysis : xr.Dataset
            The dataset containing ETa and ETp data in a projected CRS with units in meters.
        window_size_x : int, optional
            The width of the moving window in meters. Default is 1000 (1 km).
        window_size_y : int, optional
            The height of the moving window in meters. Default is 1000 (1 km).

        Returns
        -------
        xr.Dataset
            A dataset with spatially averaged ETa and ETp for each pixel.
        """
        # Ensure the dataset has x and y dimensions (e.g., projected coordinates)
        if not all(dim in ds_analysis.dims for dim in ["x", "y"]):
            raise ValueError("The dataset must have 'x' and 'y' dimensions in meters.")

        # Compute the number of grid cells corresponding to the window size
        x_resolution = abs(ds_analysis.x[1] - ds_analysis.x[0])
        y_resolution = abs(ds_analysis.y[1] - ds_analysis.y[0])
        window_cells_x = max(1, int(window_size_x / x_resolution))
        window_cells_y = max(1, int(window_size_y / y_resolution))

        self.log_panel("\n 🧭 Running compute_regional_ETap()\n")
        self.log_panel(
                        "## 📍 Parameters",
                        **{
                            "Window Size": f"{window_size_x}m x {window_size_y}m",
                            "Grid Resolution": f"{x_resolution:.2f}m (x), {y_resolution:.2f}m (y)",
                            "Window Cells": f"{window_cells_x} (x), {window_cells_y} (y)"
                        }
                    )

        ds_analysis = ds_analysis.chunk(
                                        {'x': window_cells_x, 
                                         'y': window_cells_y}
                                        )

        with ProgressBar():
            reg_analysis = ds_analysis.rolling(
                x=window_cells_x,
                y=window_cells_y,
                center=True
            ).mean().compute()


        # import scipy.ndimage
        
        # def fast_rolling_mean(arr, size):
        #     return scipy.ndimage.uniform_filter(arr, size=size, mode='reflect')
        
        # # Apply to your data variable (numpy array)
        # rolling_result = fast_rolling_mean(ds_analysis['var_name'].values, 
        #                                    size=(window_cells_y, 
        #                                          window_cells_x)
        #                                    )

        return reg_analysis




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
                               **kwargs
                               ):


        self.log_panel("🚦 Starting irrigation delineation process...")

        # Perform pre-checks before processing
        # self.check_data_validity(decision_ds)
        
        
        # Compute local and regional ETa/ETp ratios
        self.log_panel("🔍 Computing local ETa/ETp ratio...", 
                       message="Starting calculation..."
                       )       
        decision_ds = self.compute_ratio_ETap_local(decision_ds,
                                                    time_window=time_window,
                                                    **kwargs)
    
        self.log_panel("🌍 Computing [bold]regional[/bold] ETa/ETp ratio...")      
        decision_ds = self.compute_ratio_ETap_regional(decision_ds,
                                                       time_window=time_window,
                                                       **kwargs)
    
        # Apply local and regional threshold decision rules
        self.log_panel("🎯 Applying [bold]local threshold[/bold] decision rule...")
        decision_ds = self.compute_bool_threshold_decision_local(decision_ds)
    
        self.log_panel("🧭 Applying [bold]regional threshold[/bold] decision rule...")
        decision_ds = self.compute_bool_threshold_decision_regional(decision_ds)
    
        # Drop initial time steps based on time mask
        time_mask = decision_ds['time'] > np.datetime64('0', 'D')
        self.log_panel("🧹 Cleaning time dimension (dropping initial steps)...")
    
        # Apply specific rules for rain and irrigation
        self.log_panel("🌧️ Applying [bold]rain rules[/bold]...")
        decision_ds = self.apply_rules_rain(decision_ds)
    
        self.log_panel("🚿 Applying [bold]irrigation rules[/bold]...")
        decision_ds = self.apply_rules_irrigation(decision_ds)
    
        # Classify events based on delineation rules
        self.log_panel("🏷️ Classifying events...")
        event_type = self.classify_event(decision_ds)
    
        self.log_panel("✅ [bold green]Irrigation delineation complete![/bold green]")

        return decision_ds, event_type
