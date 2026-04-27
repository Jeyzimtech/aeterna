# Project Aeterna Sol-IV: Simulation Framework

This project contains the simulation framework for **Aeterna Sol-IV**, a Modular CSP-Based Water-Energy Infrastructure System for Integrated Desalination and Treatment.

## Overview
The Python simulation models the thermodynamic and operational performance of the integrated system over a multi-day period. It handles:
- **Stage I**: Energy Generation (Solar Irradiance to Thermal Energy Storage & Power Block).
- **Stage II**: Desalination (Hybrid operation using Reverse Osmosis, Multi-Effect Distillation, and Adsorption Desalination).
- **Stage III**: Water Treatment (Energy consumption for pasteurization and UV disinfection).
- **Stage IV**: Outputs (Tracking exported electricity and total produced potable water).

## Setup
To run the simulation, install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Simulation
Execute the main script:
```bash
python main.py
```

## Output
The simulation will generate:
1. `simulation_data.csv`: A detailed timeline of all system metrics.
2. `aeterna_simulation_results.png`: A comprehensive graph illustrating TES state of charge, electricity generation, and water production.
