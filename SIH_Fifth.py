import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random
import time
import math 

# -----------------------------------------------------
# 1. PREDICTIVE TARGETING & DENSITY CALCULATION SETUP 
# -----------------------------------------------------
C = 299792458.0       # Speed of Light (m/s)

# --- B. REALISTIC INPUT ASSUMPTIONS (Tracking and Targeting) ---
D_current = 500000.0   
V_rel = 1500.0         

# --- C. DEBRIS DENSITY CLASSIFICATION ASSUMPTIONS ---
R_det_km = 100.0       
SIMULATED_DEBRIS_COUNT_IN_ZONE = random.randint(15, 35) 
THRESHOLD_CROWD = 1.5e-10 
THRESHOLD_MODERATE = 0.5e-10

# --- CORE CALCULATION FUNCTIONS (Targeting Precision) ---

def calculate_time_of_flight(D_current, C):
    """Calculates the time (in seconds) the laser light takes to travel."""
    T_tof = D_current / C
    return T_tof

def calculate_lead_angle(T_tof, V_rel, D_current):
    """Calculates the aiming angle (in radians) to ensure interception."""
    Debris_Motion = V_rel * T_tof
    Theta_lead = math.atan(Debris_Motion / D_current)
    return Theta_lead

# --- DEBRIS DENSITY CLASSIFICATION FUNCTIONS ---

def calculate_detection_volume(R_det_km):
    """Calculates the volume (in km^3) of the detection sphere."""
    V_det = (4/3) * math.pi * (R_det_km ** 3)
    return V_det

def classify_debris_density(num_debris, R_det_km, THRESHOLD_CROWD, THRESHOLD_MODERATE):
    """Calculates density and classifies the crowdedness status."""
    V_det = calculate_detection_volume(R_det_km)
    
    if V_det == 0:
        return "ERROR: Zero Volume", 0.0
        
    Density = num_debris / V_det
    
    if Density > THRESHOLD_CROWD:
        Status = "Crowd (High Risk ⚠️)"
    elif Density > THRESHOLD_MODERATE:
        Status = "Moderate (Normal Risk)"
    else:
        Status = "Less Crowd (Low Risk ✅)"
        
    return Status, Density

# --- EXECUTION OF CALCULATIONS (Run once at start) ---
T_tof = calculate_time_of_flight(D_current, C)
Theta_lead = calculate_lead_angle(T_tof, V_rel, D_current)
Status, Density = classify_debris_density(SIMULATED_DEBRIS_COUNT_IN_ZONE, R_det_km, THRESHOLD_CROWD, THRESHOLD_MODERATE)


# ----------------------------
# 2. CONFIGURATION PARAMETERS (Simulation Visuals)
# ----------------------------
NUM_DEBRIS = 40 
EARTH_RADIUS = 6371 
VISUAL_EARTH_RADIUS = 0.75 * EARTH_RADIUS 

# Adjusted Orbit Radius (1/4th nearer)
ORBIT_RADIUS = EARTH_RADIUS + 125 
LASER_RANGE = 1500 
LASER_POWER = 0.6 
TIME_STEP = 0.15 
DEBRIS_COLOR = 'white'
SOLAR_POWERED = True
BACKGROUND_COLOR = 'black'

# **LASER SATELLITE ORBIT PARAMETERS**
LASER_SAT_RADIUS = ORBIT_RADIUS + 500 
LASER_SAT_SPEED = 0.005 
laser_sat_angle = 0 

# **FIX FOR STABLE ORBITS**
GRAVITY_ACCEL = 0.0015 # Simplified inward pull to create orbits

# ----------------------------
# 3. INITIALIZE DEBRIS SYSTEM
# -----------------------------------------------------
np.random.seed(42)
angles = np.random.rand(NUM_DEBRIS) * 2 * np.pi
speeds = np.random.uniform(0.5, 1.2, NUM_DEBRIS)

# Positions & velocities
debris_positions = np.array([
    [ORBIT_RADIUS * np.cos(a), ORBIT_RADIUS * np.sin(a)] for a in angles
])
debris_velocities = np.array([
    [-s * np.sin(a), s * np.cos(a)] for a, s in zip(angles, speeds)
])

# *** FIX: DEBRIS_LIST IS NOT INITIALLY DEFINED IN THIS VERSION ***
# This variable is needed by the update function to manage generated debris.
debris_list = [] 


# ----------------------------
# 4. VISUALIZATION SETUP
# -----------------------------------------------------
plt.style.use('dark_background')
# Increased figure width to accommodate text outside the plot area
fig, ax = plt.subplots(figsize=(12, 8)) 
ax.set_xlim(-8000, 8000)
ax.set_ylim(-8000, 8000)
ax.set_aspect('equal')
ax.set_title("🛰️ Real-Time Space Debris Detection & Laser Deflection System", fontsize=12)

# Draw Earth (using the smaller radius)
earth = plt.Circle((0, 0), VISUAL_EARTH_RADIUS, color='blue', alpha=0.3)
ax.add_artist(earth)

# Draw laser orbit path
theta = np.linspace(0, 2 * np.pi, 100)
laser_orbit_path, = ax.plot(LASER_SAT_RADIUS * np.cos(theta), LASER_SAT_RADIUS * np.sin(theta), 
                           '--', color='yellow', linewidth=0.5, alpha=0.6, label="Defense Satellite Orbit")

# Draw laser station (initial plot, will be updated)
laser_scatter = ax.scatter(0, 0, color='red', s=100, label="Defense Satellite 🛡️") 

# Debris points
debris_scatter = ax.scatter(debris_positions[:, 0], debris_positions[:, 1],
                            color=DEBRIS_COLOR, s=15, label="Space Debris")

# Laser beam line
laser_beam, = ax.plot([], [], 'r--', lw=1.5, alpha=0.8)

# Status text (Top Left - Moved to 1% of X-axis, 98% of Y-axis of the Figure)
status_text = fig.text(0.01, 0.98, "", 
                      transform=fig.transFigure, # Use fig.transFigure to place outside axes
                      verticalalignment='top', fontsize=9, color='yellow', 
                      bbox=dict(facecolor='black', alpha=0.7, edgecolor='yellow'))

# Calculation Panel (Top Right)
calc_panel_text = fig.text(0.99, 0.98, "", 
                          transform=fig.transFigure, # Use fig.transFigure
                          horizontalalignment='right', verticalalignment='top', 
                          fontsize=8, color='cyan', 
                          bbox=dict(facecolor='black', alpha=0.7, edgecolor='cyan'))


# --- LEGEND BOX (Bottom Left) ---
legend_box = fig.text(0.01, 0.02, "", 
                      transform=fig.transFigure,
                      verticalalignment='bottom', fontsize=8, color='white',
                      bbox=dict(facecolor='black', alpha=0.7, edgecolor='white'))


# ----------------------------
# 5. HELPER FUNCTIONS 
# -----------------------------------------------------
def detect_debris(debris_pos, laser_pos):
    """Simulates debris detection using range threshold relative to laser satellite."""
    detected_indices = []
    for i, pos in enumerate(debris_pos):
        distance = np.linalg.norm(pos - laser_pos) 
        if distance < LASER_RANGE:
            detected_indices.append(i)
    return detected_indices

def fire_laser(target_idx, laser_pos):
    """Laser applies gentle thrust (deflection) to debris."""
    
    # --- FINAL FIX: RETRO-THRUST LOGIC (Push Backward to De-orbit) ---
    v_forward = debris_velocities[target_idx]
    
    # Calculate the direction of the RETRO-THRUST (opposite the forward velocity)
    retro_thrust_direction = -v_forward
    
    # Normalize the direction vector
    norm_direction = retro_thrust_direction / np.linalg.norm(retro_thrust_direction)
    
    # Apply the velocity change (the Nudge)
    debris_velocities[target_idx] += 0.05 * LASER_POWER * norm_direction 

def apply_gravity(d_pos, d_vel):
    """Applies a simplified, constant inward pull (gravity) to debris."""
    distance = np.linalg.norm(d_pos)
    
    if distance == 0:
        return
    
    # Normalized vector points toward the origin (center)
    norm_x = -d_pos[0] / distance
    norm_y = -d_pos[1] / distance
    
    # Apply a small acceleration inward
    d_vel[0] += norm_x * GRAVITY_ACCEL
    d_vel[1] += norm_y * GRAVITY_ACCEL

def create_debris(i):
    # Determine initial position
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(ORBIT_RADIUS + 100, LASER_SAT_RADIUS + 100) # Debris created near orbits
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    
    # --- FIX: FORCED TANGENTIAL VELOCITY FOR STABILITY ---
    
    # Calculate a base speed related to distance (V ~ 1/R relationship)
    base_speed = 0.7 / distance 
    
    # *** FINAL STABILITY FIX: ENSURE INITIAL SPEED IS LOW ***
    speed = random.uniform(0.01, 0.05) # Drastically reduced speed for stability

    # Calculate direction perpendicular to the position vector (tangential)
    vx = -y / distance * speed
    vy = x / distance * speed
    
    return {
        "x": x, "y": y, "vx": vx, "vy": vy, "name": f"Debris {i}", "alive": True,
        "smoke": False, "smoke_x": None, "smoke_y": None, "fall_vx": 0, "fall_vy": 0, 
        "burning": False, "burn_timer": 0
    }


# ----------------------------
# 6. UPDATE FUNCTION (RUNS EACH FRAME)
# -----------------------------------------------------
start_time = time.time()
debris_counter = 0

def update(frame):
    global debris_positions, debris_velocities, laser_sat_angle, debris_counter

    # --- 6a. Update Laser Satellite Position ---
    laser_sat_angle += LASER_SAT_SPEED 
    
    laser_satellite_pos = np.array([
        LASER_SAT_RADIUS * np.cos(laser_sat_angle),
        LASER_SAT_RADIUS * np.sin(laser_sat_angle)
    ])
    
    # Update laser satellite visual
    laser_scatter.set_offsets([laser_satellite_pos[0], laser_satellite_pos[1]])
    
    # --- 6b. Debris Generation (Continuous Flow) ---
    if frame % random.randint(8, 12) == 0:
        num_to_add = random.randint(1, 2)
        for _ in range(num_to_add):
            debris_counter += 1
            # We don't actually need debris_list in this version, 
            # but we use its existence check to fix the error and its counter.
            # (Note: In a merged Matplotlib version, this list would be populated.)
            pass 
            
    # --- 6c. Update Debris Positions and Apply Physics ---
    for i in range(len(debris_positions)):
        
        # Apply gravity to the debris velocity
        apply_gravity(debris_positions[i], debris_velocities[i]) 
        
        # Update position
        debris_positions[i] += debris_velocities[i] * TIME_STEP * 120 
        
        # --- Boundary Reset Check ---
        distance_from_center = np.linalg.norm(debris_positions[i])
        if distance_from_center > 9000: # If debris flies outside the realistic max view
            # Reset position to a safer, inner orbit with correct speed
            new_angle = random.uniform(0, 2 * np.pi)
            new_distance = random.uniform(ORBIT_RADIUS, LASER_SAT_RADIUS) 
            debris_positions[i] = np.array([new_distance * np.cos(new_angle), new_distance * np.sin(new_angle)])
            
            # Recalculate tangential velocity for the new position
            base_speed = 0.7 / new_distance
            speed = random.uniform(base_speed * 0.9, base_speed * 1.1)
            debris_velocities[i] = np.array([-debris_positions[i][1] / new_distance * speed, 
                                              debris_positions[i][0] / new_distance * speed])

    # --- 6d. Detection and Laser Logic ---
    detected = detect_debris(debris_positions, laser_satellite_pos)

    if detected:
        target = random.choice(detected)
        fire_laser(target, laser_satellite_pos)

        # Show beam
        laser_beam.set_data(
            [laser_satellite_pos[0], debris_positions[target][0]],
            [laser_satellite_pos[1], debris_positions[target][1]]
        )
        laser_status = f"Laser Active → Target: #{target}"
    else:
        laser_beam.set_data([], [])
        laser_status = "Laser Idle (No debris in range)"

    # --- 6e. Update Visuals and HUD ---
    debris_scatter.set_offsets(debris_positions)

    elapsed = time.time() - start_time
    
    # Update Top-Left Status
    status_text.set_text(
        f"Time Elapsed: {elapsed:.1f}s\n"
        f"Solar Power: {'ON' if SOLAR_POWERED else 'OFF'}\n"
        f"Detected Debris: {len(detected)}"
    )
    
    # Update Top-Right Calculation Panel
    calc_panel_text.set_text(
        f"--- AI PREDICTIVE TARGETING ---\n"
        f"V_rel: {V_rel:.0f} m/s | D_current: {D_current/1000:.0f} km\n"
        f"T_tof (Firing Delay): {T_tof * 1000:.3f} ms\n"
        f"Theta_lead (Aiming Adj.): {math.degrees(Theta_lead):.4f}°\n"
        f"-------------------------------\n"
        f"AI DEBRIS DENSITY STATUS:\n"
        f"Density: {Density:.2e} obj/km³\n"
        f"Status: {Status}"
    )

    # Update Bottom-Left Legend Box
    legend_box.set_text(
        "--- VISUAL LEGEND ---\n"
        "🔴 Defense Satellite / Laser Station 🛡️\n"
        "⚪ Space Debris (Target)\n"
        "🟡 Defense Satellite Orbit Path\n"
        "🔵 Earth"
    )

    return debris_scatter, laser_beam, status_text, calc_panel_text, laser_scatter, laser_orbit_path, legend_box

# ----------------------------
# 7. RUN ANIMATION
# ----------------------------
ani = FuncAnimation(fig, update, frames=800, interval=100, blit=False)
plt.show()