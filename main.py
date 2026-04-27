import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Headless backend for deployment
import matplotlib.pyplot as plt
import json
import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class SimulationConfig:
    # Time settings
    dt: float = 1.0  # Time step in hours
    duration: int = 72  # Total simulation duration in hours
    
    # Solar Field (CSP)
    peak_solar_thermal_output: float = 35.0  # MW_thermal at peak sun
    
    # Thermal Energy Storage (TES) - Silica particles
    tes_capacity: float = 120.0  # MWh_thermal
    tes_initial_soc: float = 0.5  # Initial State of Charge (0.0 to 1.0)
    tes_heat_loss_rate: float = 0.01  # 1% capacity loss per hour
    
    # Power Block (Rankine / sCO2)
    power_block_capacity_electrical: float = 6.0  # MW_electrical (Max electrical output)
    power_block_efficiency: float = 0.45  # 45% thermal-to-electrical efficiency
    power_block_min_load: float = 0.2  # Minimum load to operate (20%)
    
    # Desalination (Hybrid: MED + AD + RO)
    ro_capacity: float = 50.0  # m3/hour
    ro_specific_energy: float = 3.5  # kWh/m3 (Electrical)
    
    med_capacity: float = 15.0  # m3/hour
    med_specific_thermal_energy: float = 45.0  # kWh_thermal/m3 (High/Medium grade heat)
    med_specific_electrical_energy: float = 1.5  # kWh_electrical/m3
    
    ad_capacity: float = 10.0  # m3/hour
    ad_specific_waste_heat: float = 15.0  # kWh_thermal/m3 (Low grade waste heat)
    
    # Water Treatment
    treatment_electrical_energy: float = 0.5  # kWh/m3 (UV, Pumping)
    treatment_thermal_energy: float = 2.0  # kWh/m3 (Thermal Pasteurization from waste heat)

class AeternaSystem:
    def __init__(self, config: SimulationConfig):
        self.config = config
        
        # System State
        self.tes_current_energy = self.config.tes_capacity * self.config.tes_initial_soc
        self.time = 0.0
        
        # History for plotting
        self.history: List[Dict[str, float]] = []

    def get_solar_irradiance(self) -> float:
        """Simulate diurnal solar cycle (simple sine wave during day)"""
        hour_of_day = self.time % 24
        # Assuming sunrise at 6:00, sunset at 18:00
        if 6 <= hour_of_day <= 18:
            # Normalized sine wave peaking at noon (12:00)
            return np.sin((hour_of_day - 6) * np.pi / 12)
        return 0.0

    def step(self):
        dt = self.config.dt
        
        # 1. Solar Field Heat Generation
        irradiance_factor = self.get_solar_irradiance()
        solar_heat_generated = self.config.peak_solar_thermal_output * irradiance_factor * dt # MWh_th
        
        # 2. Add heat to TES
        self.tes_current_energy += solar_heat_generated
        
        # 3. TES Thermal losses
        self.tes_current_energy -= self.config.tes_capacity * self.config.tes_heat_loss_rate * dt
        self.tes_current_energy = max(0.0, self.tes_current_energy) # Prevent negative
        
        # 4. Power Block Operation (Determine thermal power drawn)
        # We try to run the power block at full capacity if we have enough thermal energy,
        # otherwise we scale down or shut off if below min load.
        required_thermal_power = self.config.power_block_capacity_electrical / self.config.power_block_efficiency
        required_thermal_energy = required_thermal_power * dt
        
        if self.tes_current_energy >= required_thermal_energy:
            thermal_energy_consumed = required_thermal_energy
        else:
            # Check if we can run at min load
            min_thermal_energy = required_thermal_energy * self.config.power_block_min_load
            if self.tes_current_energy >= min_thermal_energy:
                thermal_energy_consumed = self.tes_current_energy
            else:
                thermal_energy_consumed = 0.0
                
        self.tes_current_energy -= thermal_energy_consumed
        
        # Cap TES at max capacity (energy spilled/defocused if full)
        heat_spilled = 0.0
        if self.tes_current_energy > self.config.tes_capacity:
            heat_spilled = self.tes_current_energy - self.config.tes_capacity
            self.tes_current_energy = self.config.tes_capacity
            
        electricity_generated = thermal_energy_consumed * self.config.power_block_efficiency
        waste_heat_generated = thermal_energy_consumed * (1 - self.config.power_block_efficiency) # MWh_th
        
        # 5. Desalination Operation
        # Convert kWh to MWh for calculations
        ro_elec_needed = (self.config.ro_capacity * dt) * self.config.ro_specific_energy / 1000.0
        med_elec_needed = (self.config.med_capacity * dt) * self.config.med_specific_electrical_energy / 1000.0
        med_therm_needed = (self.config.med_capacity * dt) * self.config.med_specific_thermal_energy / 1000.0
        ad_waste_heat_needed = (self.config.ad_capacity * dt) * self.config.ad_specific_waste_heat / 1000.0
        
        total_elec_needed = ro_elec_needed + med_elec_needed
        
        # Desalination outputs
        water_ro = 0.0
        water_med = 0.0
        water_ad = 0.0
        
        # Can we run RO & MED electrically?
        electricity_available = electricity_generated
        if electricity_available >= total_elec_needed:
            electricity_available -= total_elec_needed
            water_ro = self.config.ro_capacity * dt
            # For MED, we also need direct medium-grade heat from TES or power block extraction
            # We'll take it from TES for simplicity here
            if self.tes_current_energy >= med_therm_needed:
                self.tes_current_energy -= med_therm_needed
                water_med = self.config.med_capacity * dt
            else:
                # Run MED partially
                fraction = self.tes_current_energy / med_therm_needed
                water_med = self.config.med_capacity * dt * fraction
                self.tes_current_energy = 0.0
                electricity_available += med_elec_needed * (1 - fraction) # return unused electricity
        else:
            # Partial operation based on available electricity (prioritize RO)
            if electricity_available >= ro_elec_needed:
                electricity_available -= ro_elec_needed
                water_ro = self.config.ro_capacity * dt
            else:
                fraction = electricity_available / ro_elec_needed
                water_ro = self.config.ro_capacity * dt * fraction
                electricity_available = 0.0
                
        # AD uses low-grade waste heat
        waste_heat_available = waste_heat_generated
        if waste_heat_available >= ad_waste_heat_needed:
            waste_heat_available -= ad_waste_heat_needed
            water_ad = self.config.ad_capacity * dt
        else:
            fraction = waste_heat_available / ad_waste_heat_needed
            water_ad = self.config.ad_capacity * dt * fraction
            waste_heat_available = 0.0
            
        total_desal_water = water_ro + water_med + water_ad
        
        # 6. Water Treatment
        # Uses electricity and waste heat
        treatment_elec_needed = total_desal_water * self.config.treatment_electrical_energy / 1000.0
        treatment_therm_needed = total_desal_water * self.config.treatment_thermal_energy / 1000.0
        
        treated_water = 0.0
        if electricity_available >= treatment_elec_needed and waste_heat_available >= treatment_therm_needed:
            electricity_available -= treatment_elec_needed
            waste_heat_available -= treatment_therm_needed
            treated_water = total_desal_water
        else:
            # Scale down if shortages (simplification: assume we treat as much as we can power)
            elec_fraction = min(1.0, electricity_available / (treatment_elec_needed + 1e-9))
            therm_fraction = min(1.0, waste_heat_available / (treatment_therm_needed + 1e-9))
            fraction = min(elec_fraction, therm_fraction)
            treated_water = total_desal_water * fraction
            electricity_available -= treatment_elec_needed * fraction
            waste_heat_available -= treatment_therm_needed * fraction

        # Remaining electricity is exported or used for local industry
        electricity_exported = electricity_available

        # Record state
        state = {
            'Time (h)': self.time,
            'Solar Irradiance': irradiance_factor,
            'Heat Generated (MWh_th)': solar_heat_generated,
            'TES State of Charge (%)': (self.tes_current_energy / self.config.tes_capacity) * 100,
            'Electricity Generated (MWh_e)': electricity_generated,
            'Electricity Exported (MWh_e)': electricity_exported,
            'Water Produced RO (m3)': water_ro,
            'Water Produced MED (m3)': water_med,
            'Water Produced AD (m3)': water_ad,
            'Total Treated Water (m3)': treated_water
        }
        self.history.append(state)
        
        self.time += dt

    def run(self):
        print(f"Starting Aeterna Sol-IV Simulation for {self.config.duration} hours...")
        steps = int(self.config.duration / self.config.dt)
        for _ in range(steps):
            self.step()
        print("Simulation complete.")

    def get_results_df(self):
        return pd.DataFrame(self.history)

def plot_results(df: pd.DataFrame):
    plt.style.use('dark_background') # Professional aesthetic
    
    fig, axs = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    fig.suptitle('Project Aeterna Sol-IV: Modular CSP Water-Energy System Simulation', fontsize=16, fontweight='bold', color='#00d2ff')
    
    time = df['Time (h)']
    
    # 1. Energy Storage and Generation
    ax1 = axs[0]
    ax1.plot(time, df['TES State of Charge (%)'], label='TES State of Charge (%)', color='#ff9900', linewidth=2)
    ax1.set_ylabel('TES SOC (%)')
    ax1.set_ylim(0, 105)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    ax1_twin = ax1.twinx()
    ax1_twin.fill_between(time, 0, df['Heat Generated (MWh_th)'], color='#ffcc00', alpha=0.3, label='Solar Heat (MWh_th)')
    ax1_twin.set_ylabel('Heat Generation (MWh_th)')
    ax1_twin.legend(loc='upper right')
    
    # 2. Electricity Profile
    ax2 = axs[1]
    ax2.plot(time, df['Electricity Generated (MWh_e)'], label='Electricity Generated (MWh)', color='#00ff99', linewidth=2)
    ax2.plot(time, df['Electricity Exported (MWh_e)'], label='Electricity Exported/Surplus (MWh)', color='#00ccff', linestyle='--', linewidth=2)
    ax2.set_ylabel('Electrical Energy (MWh)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Water Production Profile
    ax3 = axs[2]
    ax3.stackplot(time, 
                  df['Water Produced RO (m3)'], 
                  df['Water Produced MED (m3)'], 
                  df['Water Produced AD (m3)'],
                  labels=['RO (Electrical)', 'MED (Thermal)', 'AD (Waste Heat)'],
                  colors=['#0055ff', '#0099ff', '#00ddff'], alpha=0.8)
    
    ax3.plot(time, df['Total Treated Water (m3)'], label='Total Treated Output', color='white', linewidth=2, linestyle=':')
    ax3.set_ylabel('Water Volume (m3/h)')
    ax3.set_xlabel('Time (Hours)')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper left')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig('aeterna_simulation_results.png', dpi=300, bbox_inches='tight')
    print("Saved simulation plot to 'aeterna_simulation_results.png'")
    
def print_summary(df: pd.DataFrame):
    print("\n" + "="*50)
    print("AETERNA SOL-IV SIMULATION SUMMARY (72 Hours)")
    print("="*50)
    total_elec_gen = df['Electricity Generated (MWh_e)'].sum()
    total_elec_exp = df['Electricity Exported (MWh_e)'].sum()
    total_water = df['Total Treated Water (m3)'].sum()
    
    print(f"Total Electricity Generated: {total_elec_gen:.2f} MWh")
    print(f"Total Electricity Exported : {total_elec_exp:.2f} MWh (Available for Grid/Industry)")
    print(f"Total Treated Water        : {total_water:.2f} m³")
    
    # Daily averages
    days = df['Time (h)'].max() / 24.0
    print(f"\nAverage Daily Electricity Generated: {total_elec_gen/days:.2f} MWh/day")
    print(f"Average Daily Treated Water        : {total_water/days:.2f} m³/day")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Create configuration
    config = SimulationConfig()
    
    # Initialize and run system
    system = AeternaSystem(config)
    system.run()
    
    # Analyze results
    results_df = system.get_results_df()
    
    # Output to CSV
    results_df.to_csv('simulation_data.csv', index=False)
    print("Saved raw data to 'simulation_data.csv'")
    
    # Output to Web Dashboard format
    os.makedirs('webapp', exist_ok=True)
    with open('webapp/data.js', 'w', encoding='utf-8') as f:
        # Optimize data size by rounding numbers
        compact_data = results_df.round(2).to_dict(orient='records')
        f.write(f"const simData = {json.dumps(compact_data)};")
    print("Exported data to 'webapp/data.js' (optimized) for Digital Twin dashboard")
    
    # Print summary
    print_summary(results_df)
    
    # Plot
    plot_results(results_df)
