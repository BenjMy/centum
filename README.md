[![pages-build-deployment](https://github.com/BenjMy/centum/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/BenjMy/centum/actions/workflows/pages/pages-build-deployment)
[![Publish Python Package](https://github.com/BenjMy/centum/actions/workflows/python-publish.yml/badge.svg)](https://github.com/BenjMy/centum/actions/workflows/python-publish.yml)

# 💦  Centum
Centum, derived from the Latin word for "a hundred," is a Python package designed to streamline water accounting through energy and water balance modeling. It equips users with tools to enhance water use efficiency, detect illegal water pumping, and protect essential mountain ecosystems, addressing key water management challenges.

## 🔍 Key inputs
- NetCDF files: These should be imported as rioxarray datasets and contain essential variables like ETa (Actual Evapotranspiration) and ETp (Potential Evapotranspiration).
- Irrigation shapefiles: Import these with geopandas to define and analyze irrigation areas.

## 🔥 Core Models Used
Centum relies on two main models:
- Energy Balance Modeling 🌞: Provides ETa outputs using pyTSEB.
- Soil Water Balance Modeling 💧: Supplies ETa outputs using pyCATHY.
  
## ✨ Key Features
- Water Delineation: Map areas of interest using the ETa/ETp ratio.
- Water Net Quantification: Calculate net water use based on ET baselines from Earth Observation data.
  
## 🌍 Additional Capabilities (expected)
- Illegal Water Pumping Detection: Identify unsanctioned water use.
- Ecosystem Resilience: Assess ecosystem drought resilience and green water footprint, aiding in ecosystem protection.

## 📥 Installation
Install Centum via pip:

```bash
pip install centum
