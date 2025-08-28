#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions to plot 
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize

#%%
def plot_irrigation_schedule(event_type,time_steps,fig,axes):
        
    axes = axes.flatten()  # Flatten to easily iterate over
    # Custom colormap with discrete colors corresponding to 'No input', 'irrigation', 'rain'
    cmap = plt.cm.colors.ListedColormap(['white', 
                                         'red', 
                                         'blue'
                                         ])
    x_values = event_type['x'].values
    y_values = event_type['y'].values
    extent = [x_values.min(), x_values.max(), y_values.min(), y_values.max()]
    for i, ax in enumerate(axes):
        if i < time_steps:  # Only plot if there is corresponding data
            data = event_type.isel(time=i).values  # or event_type.sel(time=...) if using labels
            img = ax.imshow(data, 
                            cmap=cmap, 
                            vmin=0, 
                            vmax=2, 
                            extent=extent,
                            origin='lower'
                            )
            
            # Set the title with the time step
            # event_type['days'] = event_type['time'] / np.timedelta64(1, 'D')
    
            # ax.set_title(f'Day {np.round(event_type.days.values[i],1)}')
            ax.set_xlabel('x')  # Label for the x-axis
            ax.set_ylabel('y')  # Label for the y-axis
        else:
            ax.axis('off')  # Turn off empty subplots
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, 
                                              norm=plt.Normalize(vmin=0, vmax=2)
                                              ), 
                        ax=axes, 
                        orientation='horizontal', 
                        fraction=0.02, pad=0.04)  # Adjust placement
    cbar.set_ticks([0, 1, 2])
    cbar.set_ticklabels(['No input', 'irrigation', 'rain'])
    
    pass




def plot_monthly_volume_mm(ds, variable='volume_mm',axs=None, cmap='viridis'):
    time_index = pd.to_datetime(ds.time.values)
    months = time_index.to_period('M').unique()
    axsf = axs.flatten()

    vmin = 0
    vmax = float(ds[variable].max())
    norm = Normalize(vmin=vmin, vmax=vmax)

    for i, month in enumerate(months):
        mask = time_index.to_period('M') == month
        data = ds[variable].sel(time=mask).squeeze().values

        alpha = np.clip((data - vmin) / (vmax - vmin), 0.05, 1.0)
        rgba = plt.cm.get_cmap(cmap)(norm(data))
        rgba[..., -1] = alpha

        axsf[i].imshow(rgba, aspect='auto')
        axsf[i].set_title(month.strftime('%B %Y'))
        axsf[i].set_yticks([])

    for j in range(i + 1, np.shape(axs)[0] * np.shape(axs)[1]):
        axsf[j].axis('off')

    return norm



