# Welcome to the centum documentation

**Centum** is a Python package designed for water accounting, focusing on ET. Its primary goal is to provide researchers and practitioners with tools to analyze and manage water resources efficiently, leveraging remote sensing data and energy/water balance models.

The package supports the delineation of irrigated areas. Built with a modular and user-friendly design, `centum` enables seamless integration with geospatial data libraries like **xarray** and **geopandas**.

## Features

- **Delineation Tools**: Identify irrigated zones using ET-based methods.
- **Water Accounting**: Analyze water use and availability using the ET outcomes from energy balance models versus baseline e.g. water balance model.
- **Flexible Data Formats**: Works with NetCDF, and shapefiles.
- **Open Source**: Licensed under GPL-3.0 for collaborative development.


::: {admonition} Centum is Model-Agnostic
:class: tip
Inputs for Centum are NetCDF files, which can be produced by any kind of energy/water balance model.
:::



## Release roadmap
- [ ] V1.0: water delineation algoritm tested for synthetic irrigation time series (generated using AQUACROP)
- V1.*: 
  - [ ] test delineation over real field site data 
  - [ ] result visualisation utilities
  - [ ] ...
- V2.0: irrigation water quantification 
- V3.0: use ET from DA as input to estimate uncertainties
- V*: illegal Water Pumping Detection/ Ecosystem Resilience (Green water footprint evaluation)

## Installation

To install `centum` using pip:

```bash
pip install centum
```

Check out the content pages bundled with this sample book to see more.

```{tableofcontents}
```
