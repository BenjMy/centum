[![pages-build-deployment](https://github.com/BenjMy/centum/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/BenjMy/centum/actions/workflows/pages/pages-build-deployment)
[![Publish Python Package](https://github.com/BenjMy/centum/actions/workflows/python-publish.yml/badge.svg)](https://github.com/BenjMy/centum/actions/workflows/python-publish.yml)


## 📥 Installation
Install Centum via pip:

```bash
pip install centum
```

# 💦  Centum
Centum, derived from the Latin word for "a hundred," is a Python package designed to streamline water accounting through energy and water balance modeling inputs. It equips users with tools to enhance water use efficiency, detect illegal water pumping, and protect essential mountain ecosystems, addressing key water management challenges.

<img width="2911" height="1246" alt="image" src="https://github.com/user-attachments/assets/7024d26a-95c5-491a-ac28-c8787a6ce8cf" />


## 🔍 Key inputs
For **irrigation water delimitation**:
- ETa and ETp (single NetCDF file) from Earth Observations

Additionnaly for **irrigation water quantification**:
- ETa from a water balance model (baseline without irrigation scheme)

Optionnaly:
- Corinne Land Cover
- Irrigation shapefiles: Import these with geopandas to define and analyze irrigation areas.


## ✨ Key Features
- Water Delineation: Map areas of interest using the ETa/ETp ratio.
- Type of irrigation classification
- Water Net Quantification: Calculate net water use based on ET baselines from Earth Observation data.
  
## 🌍 Additional Capabilities (expected)
- Illegal Water Pumping Detection: Identify unsanctioned water use.
- Ecosystem Resilience: Assess ecosystem drought resilience and green water footprint, aiding in ecosystem protection.

## 🔥 Core Models Used for testing
Centum relies on two main models for the testing datasets:
- Energy Balance Modeling 🌞: Provides ETa outputs using pyTSEB.
- Soil Water Balance Modeling 💧: Supplies ETa outputs using pyCATHY.
  

## Expected releases roadmap

- [x] V1.0: water delineation algoritm tested for synthetic irrigation time series (generated using AQUACROP)
- [ ] V1.*: 
  - [x] test delineation over real field site data 
  - [x] result visualisation utilities
  - [ ] ...
- [ ] V2.0: irrigation water quantification
  - [ ] use of soil database
  - [ ] type of irrigation identification (use microwave info!)
- [ ] V3.0: use ET from DA as input to estimate uncertainties
  - [ ] Soil parm. perturbation
  - [ ] ET ensemble
- [ ] V*: 
  - Illegal Water Pumping Detection
  - Ecosystem Resilience (Green water footprint evaluation)
  - QGIS plugin



## References 

Water delineation algoritm: 
- ETa/ETp ratio

Irrigation water quantification:

Type of irrigation identification:
- ETa versus SM from SAR ratio

ET from DA


