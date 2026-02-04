import math
# import numpy as np # Not needed for this block

# ====================================================================
# MINIMUM ENERGY ALGORITHM (SOLVES FOR LASER FIRING TIME)
# ====================================================================

# --- INPUTS (Based on project's physical feasibility study) ---
DEBRIS_MASS_KG = 2.0         
REQUIRED_DELTA_V_MS = 279.9760  
LASER_THRUST_N = 1.0         
MOMENTUM_COUPLING_CM = 1e-5  

def calculate_min_energy_time(m, delta_v, T, Cm):
    """
    Calculates the minimum laser pulse time and total energy required.
    Formula: T * t_pulse = m * Delta_v
    """
    
    # 1. Calculate Minimum Pulse Time (t_pulse)
    t_pulse_sec = (m * delta_v) / T
    t_pulse_min = t_pulse_sec / 60
    
    # 2. Calculate Total Energy Required (E_total)
    # E_total = (T * t_pulse) / Cm
    E_total_J = (T * t_pulse_sec) / Cm
    E_total_MJ = E_total_J / 1e6
    
    results = {
        "Time (minutes)": t_pulse_min,
        "Energy (MJ)": E_total_MJ
    }
    return results

# --- EXECUTION DEMONSTRATION ---
if __name__ == '__main__':
    energy_results = calculate_min_energy_time(DEBRIS_MASS_KG, REQUIRED_DELTA_V_MS, LASER_THRUST_N, MOMENTUM_COUPLING_CM)
    
    print("==================================================")
    print("MINIMUM ENERGY ALGORITHM (AI Efficiency Check)")
    print("==================================================")
    print(f"Input Mass: {DEBRIS_MASS_KG} kg | Required Delta-v: {REQUIRED_DELTA_V_MS} m/s")
    print("-" * 50)
    print(f"Calculated Time to Clear (t_pulse): {energy_results['Time (minutes)']:.2f} minutes")
    print(f"Total Energy Required: {energy_results['Energy (MJ)']:.2f} MJ")
    print("==================================================")