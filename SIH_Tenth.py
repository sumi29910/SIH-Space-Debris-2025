#limit 5 debris
import matplotlib
matplotlib.use("TkAgg") 

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from PIL import Image
import math 

# -----------------------------------------------------
# 1. ORBITAL MECHANICS & CALCULATION SETUP 
# -----------------------------------------------------
# --- EXACT SCIENTIFIC CONSTANTS (Original Values) ---
G = 6.6743e-11        # Gravitational Constant (N*m^2/kg^2)
M_earth = 5.9722e24   # Mass of Earth (kg)
R_earth = 6378137.0   # Equatorial Radius of Earth (m)

# --- REALISTIC INPUT ASSUMPTIONS (Optimized for Minutes) ---
H_current = 700000.0   # Current Debris Altitude (700 km) in meters
H_target = 200000.0    # Target De-orbit Altitude (200 km) in meters
M_debris_base = 2.0    # Base Assumed Debris Mass (kg) - will be adjusted
T_laser_thrust = 1.0   # Assumed Average Laser Thrust (Newtons)

# --- CORE CALCULATION FUNCTIONS (REUSED) ---

def calculate_orbital_velocity(R):
    """Calculates the orbital speed required at a given orbital radius (R)."""
    return math.sqrt((G * M_earth) / R)

def calculate_min_delta_v(R_current, R_target):
    """Calculates the magnitude of the velocity difference (Delta-V)."""
    V_current = calculate_orbital_velocity(R_current)
    V_target = calculate_orbital_velocity(R_target)
    Delta_V = abs(V_current - V_target)
    return Delta_V

def calculate_shortest_pulse_time(Delta_V, M_debris, T_laser_thrust):
    """Translates Delta-V into the shortest laser firing time (t_pulse)."""
    Pulse_Time = (M_debris * Delta_V) / T_laser_thrust
    return Pulse_Time

# --- EXECUTION OF BASE CALCULATION ---
# These are the *minimum* required for the smallest debris
R_current = R_earth + H_current
R_target = R_earth + H_target
min_Delta_V_base = calculate_min_delta_v(R_current, R_target)
shortest_t_pulse_base = calculate_shortest_pulse_time(min_Delta_V_base, M_debris_base, T_laser_thrust)

# Use a small scaled value for animation physics (the visual "push" speed)
min_Delta_V_scaled = min_Delta_V_base / 10000 

# -----------------------------------------------------
# 2. SIMULATION PARAMETERS (scaled for visibility)
# -----------------------------------------------------
plt.rcParams["font.family"] = "Segoe UI Emoji"
EARTH_RADIUS = 2 
LASER_RANGE = 5 
FRAME_INTERVAL = 25 

# Visual speed for de-orbiting (This is the visual fix to make debris fall quickly)
VISUAL_FALL_SPEED = 0.5 
GRAVITY_ACCEL = 0.0015 # Reduced gravity for stable orbits

orbit_radii = [3, 4.5, 6, 7.5, 9] 
orbit_speeds = [0.03, 0.025, 0.02, 0.017, 0.015] 

satellite = {"x": None, "y": None, "active": True, "name": "Defense Satellite", "angle": 0, "current_orbit": 0, "jumping": False, "jump_progress": 0}

active_satellites = [
    {"x": None, "y": None, "angle": 0, "orbit_radius": EARTH_RADIUS + 1, "speed": 0.02, "color": "#00FF00", "name": "Active Sat 1"},
    {"x": None, "y": None, "angle": 0, "orbit_radius": EARTH_RADIUS + 1.5, "speed": 0.025, "color": "#00FF00", "name": "Active Sat 2"},
    {"x": None, "y": None, "angle": 0, "orbit_radius": EARTH_RADIUS + 2, "speed": 0.018, "color": "#00FF00", "name": "Active Sat 3"},
    {"x": None, "y": None, "angle": 0, "orbit_radius": EARTH_RADIUS + 2.5, "speed": 0.022, "color": "#00FF00", "name": "Active Sat 4"},
    {"x": None, "y": None, "angle": 0, "orbit_radius": EARTH_RADIUS + 3, "speed": 0.019, "color": "#00FF00", "name": "Active Sat 5"},

   ]

debris_list = []
path_x, path_y = [], []

# -----------------------------------------------------
# 3. DEBRIS CHARACTERISTICS & METADATA (NEW SECTION)
# -----------------------------------------------------

DEBRIS_TYPES = [
    {"size_type": "Paint Fleck (Small)", "material": "Polymer/Aluminum", "mass_factor": 0.5},
    {"size_type": "Bolt (Medium)", "material": "Titanium Alloy", "mass_factor": 1.0},
    {"size_type": "Fragment (Large)", "material": "Composite/Steel", "mass_factor": 2.5},
    {"size_type": "Rocket Stage Remnant (Huge)", "material": "Thick Aluminum", "mass_factor": 5.0}
]

# -----------------------------------------------------
# Load Earth Image (Ensure this path is correct on your system)
# -----------------------------------------------------
# Placeholder for image path. Assuming the user's original path is unavailable for me.
# earth_img_path = r"C:\Users\hp\Downloads\SIH_Space_Debris\SIH_Space_Debris\Earth.jpg" 
# Use a fallback by default
earth_arr = None
# try:
#     earth_img = Image.open(earth_img_path).convert("RGBA")
#     earth_arr = np.array(earth_img)
#     threshold = 245
#     r, g, b, a = earth_arr.T
#     white_areas = (r > threshold) & (g > threshold) & (b > threshold)
#     earth_arr[..., 3][white_areas.T] = 0
# except FileNotFoundError:
#     print(f"INFO: Earth image not loaded. Using a default blue circle.")
#     earth_arr = None

# -----------------------------------------------------
# Figure Setup
# -----------------------------------------------------
plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(10, 7)) 
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)
ax.set_aspect("equal")
ax.set_title("SIH: Sustainable Laser Debris Defense (Software Innovation)", fontsize=16, pad=15)

# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------
def draw_laser(x1, y1, x2, y2):
    return ax.plot([x1, x2], [y1, y2], color="red", linewidth=2, alpha=0.7)[0]

def explosion_effect(x, y):
    return ax.scatter(x, y, s=300, color="yellow", alpha=0.9)

def smoke_cloud(x, y):
    return ax.scatter(x, y, s=150, color="gray", alpha=0.5, marker='o')

def burning_effect(x, y):
    offsets = np.random.uniform(-0.1, 0.1, (5, 2))
    burn_x = x + offsets[:, 0]
    burn_y = y + offsets[:, 1]
    return ax.scatter(burn_x, burn_y, s=10, color="orange", alpha=0.8)

def create_debris(i):
    # Determine initial position
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(EARTH_RADIUS + 1, EARTH_RADIUS + 6) 
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    
    # Select characteristics
    char = random.choice(DEBRIS_TYPES)
    
    # Calculate mass based on the base mass and factor
    debris_mass = M_debris_base * char["mass_factor"]
    
    # Calculate the required pulse time for this specific debris mass
    min_Delta_V_current = calculate_min_delta_v(distance * R_earth / EARTH_RADIUS, R_target) # Scale up R for accurate Delta-V
    required_t_pulse = calculate_shortest_pulse_time(min_Delta_V_current, debris_mass, T_laser_thrust)
    required_energy = (T_laser_thrust * required_t_pulse) # Assuming 1 Watt-second per Joule for 1 N-s/m/s thrust to simplify

    
    # --- FIX: FORCED TANGENTIAL VELOCITY FOR STABILITY ---
    base_speed = 0.7 / distance # Higher multiplier to balance the reduced gravity
    speed = random.uniform(base_speed * 0.9, base_speed * 1.1) 

    # Calculate direction perpendicular to the position vector (tangential)
    vx = -y / distance * speed
    vy = x / distance * speed
    
    return {
        "x": x, "y": y, "vx": vx, "vy": vy, "name": f"Debris {i}", "alive": True,
        "smoke": False, "smoke_x": None, "smoke_y": None, "fall_vx": 0, "fall_vy": 0, 
        "burning": False, "burn_timer": 0,
        
        # --- NEW METADATA ---
        "size_type": char["size_type"],
        "material": char["material"],
        "mass_kg": debris_mass,
        "pulse_time_s": required_t_pulse,
        "energy_J": required_energy 
    }

def draw_earth():
    if earth_arr is not None:
        ax.imshow(earth_arr, extent=[-EARTH_RADIUS, EARTH_RADIUS, -EARTH_RADIUS, EARTH_RADIUS])
    else:
        circle = plt.Circle((0, 0), EARTH_RADIUS, color='blue', alpha=0.8)
        ax.add_artist(circle)
        
    ax.text(0, -EARTH_RADIUS - 0.5, "🌍 Earth", color="white", ha="center", fontsize=12)

def draw_orbits():
    for r in orbit_radii:
        theta = np.linspace(0, 2*np.pi, 400)
        ax.plot(r * np.cos(theta), r * np.sin(theta), linestyle="--", color="#888", linewidth=0.7)

def display_control_panel(target_debris=None, distance_to_target=None):
    # Display the calculated algorithmic results on the plot
    results_text = f"--- Software Innovation (Min Energy Algorithm) ---\n"
    results_text += f"Laser Thrust (T_thrust): {T_laser_thrust:.1f} Newtons\n"
    results_text += f"Required Delta-V (Nudge): {min_Delta_V_base:.4f} m/s (Base)\n"
    results_text += f"--------------------------------------------------\n"
    
    if target_debris:
        results_text += f"🎯 **TARGETED DEBRIS: {target_debris['name']}**\n"
        results_text += f"  Size/Type: {target_debris['size_type']}\n"
        results_text += f"  Material: {target_debris['material']}\n"
        results_text += f"  Mass: {target_debris['mass_kg']:.2f} kg\n"
        results_text += f"  Distance (Scaled): {distance_to_target:.2f} units\n"
        results_text += f"  Energy Required (Pulse Time): {target_debris['pulse_time_s']:.3f} s\n"
        results_text += f"  Total Energy (Approx): {target_debris['energy_J']:.1f} Joules\n"
        results_text += f"  De-orbiting Time Implication: {target_debris['pulse_time_s']/60:.2f} minutes\n"
    else:
        results_text += f"System Status: Searching for Debris within {LASER_RANGE} units...\n"
        
    results_text += f"--------------------------------------------------\n"
    results_text += f"Debris Count (Alive): {sum(1 for d in debris_list if d['alive'])}"
    
    ax.text(1.05, 0.95, results_text, transform=ax.transAxes, 
            verticalalignment='top', fontsize=8, color='cyan', 
            bbox=dict(facecolor='black', alpha=0.8, edgecolor='cyan', boxstyle='round,pad=0.5'))

def apply_gravity(d):
    """Applies a simplified, constant inward pull (gravity) to debris."""
    if not d["alive"]:
        return
    
    distance = np.hypot(d["x"], d["y"])
    
    if distance == 0:
        return
    
    # Normalized vector points toward the origin (center)
    norm_x = -d["x"] / distance
    norm_y = -d["y"] / distance
    
    # Apply a small acceleration inward
    d["vx"] += norm_x * GRAVITY_ACCEL
    d["vy"] += norm_y * GRAVITY_ACCEL


# -----------------------------------------------------
# 4. Animation Logic
# -----------------------------------------------------
frame_count = 0
debris_counter = 0

def update(frame):
    global frame_count, debris_counter
    frame_count += 1
    ax.clear()
    ax.set_facecolor("black")

    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_aspect("equal") 
    ax.set_title("SIH: Sustainable Laser Debris Defense (Software Innovation)", fontsize=16, pad=15)


    draw_earth()
    draw_orbits() 
    
    # Variables for control panel update
    targeted_debris = None
    target_distance = None


    # --- Defense Satellite Movement and Path ---
    satellite["angle"] += orbit_speeds[satellite["current_orbit"]]

    if not satellite["jumping"]:
        r = orbit_radii[satellite["current_orbit"]]
        satellite["x"] = r * np.cos(satellite["angle"])
        satellite["y"] = r * np.sin(satellite["angle"])

        if satellite["angle"] >= 2 * np.pi:
            satellite["angle"] = 0
            if satellite["current_orbit"] < len(orbit_radii) - 1:
                satellite["jumping"] = True
                satellite["jump_progress"] = 0
    else:
        r1 = orbit_radii[satellite["current_orbit"]]
        r2 = orbit_radii[satellite["current_orbit"] + 1]
        satellite["jump_progress"] += 0.01
        t = min(satellite["jump_progress"], 1)
        r = r1 * (1 - t) + r2 * t
        satellite["x"] = r * np.cos(satellite["angle"])
        satellite["y"] = r * np.sin(satellite["angle"])
        if t >= 1:
            satellite["jumping"] = False
            satellite["current_orbit"] += 1

    ax.plot(satellite["x"], satellite["y"], marker="o", color="white", markersize=5)
    ax.text(satellite["x"] + 0.5, satellite["y"], "🛰 Defense Satellite", color="white", fontsize=8)

    path_x.append(satellite["x"])
    path_y.append(satellite["y"])
    ax.plot(path_x, path_y, color="white", linewidth=0.9, alpha=0.9)

    # --- Active Satellites Movement ---
    for sat in active_satellites:
        sat["angle"] += sat["speed"]
        sat["x"] = sat["orbit_radius"] * np.cos(sat["angle"])
        sat["y"] = sat["orbit_radius"] * np.sin(sat["angle"])
        ax.scatter(sat["x"], sat["y"], s=50, color=sat["color"]) 
        ax.text(sat["x"] + 0.5, sat["y"], sat["name"], color="white", fontsize=6)

    # --- Debris Generation (Continuous Flow) ---
    MAX_DEBRIS = 5 # Limit the debris count
    alive_count = sum(1 for d in debris_list if d["alive"])
    
    if alive_count < MAX_DEBRIS and frame_count % random.randint(8, 12) == 0:
        num_to_add = random.randint(1, 2)
        
        # Check to ensure we don't exceed the limit in this frame
        if alive_count + num_to_add <= MAX_DEBRIS: 
            for _ in range(num_to_add):
                debris_counter += 1
                debris_list.append(create_debris(debris_counter))
                alive_count += 1
    
    # --- Debris Movement, De-orbit, and Burning ---
    for d in debris_list:
        if d["alive"]:
            # --- STEP B: APPLY GRAVITY ---
            apply_gravity(d) 
            
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            
            ax.scatter(d["x"], d["y"], s=50, color="red")
            ax.text(d["x"] + 0.5, d["y"], d["name"], color="white", fontsize=6)
            
            # *** FINAL FIX: BOUNDARY CHECK AND RESET ***
            distance_from_center = np.hypot(d["x"], d["y"])
            if distance_from_center > 9.0: # If debris flies outside the outermost orbit (9.0)
                # Reset position to a safer, inner orbit with correct speed
                new_angle = random.uniform(0, 2 * np.pi)
                new_distance = random.uniform(3.0, 5.0) 
                d["x"] = new_distance * np.cos(new_angle)
                d["y"] = new_distance * np.sin(new_angle)
                
                # Recalculate tangential velocity for the new position
                base_speed = 0.7 / new_distance
                speed = random.uniform(base_speed * 0.9, base_speed * 1.1)
                d["vx"] = -d["y"] / new_distance * speed
                d["vy"] = d["x"] / new_distance * speed

        
        elif d["smoke"]:
            d["smoke_x"] += d["fall_vx"]
            d["smoke_y"] += d["fall_vy"]
            d["fall_vx"] *= 0.99 
            d["fall_vy"] *= 0.99
            smoke_cloud(d["smoke_x"], d["smoke_y"])
            distance_from_center = np.hypot(d["smoke_x"], d["smoke_y"])
            if distance_from_center <= EARTH_RADIUS: 
                d["smoke"] = False
                d["burning"] = True 
        
        elif d["burning"]:
            d["burn_timer"] += 1
            if d["burn_timer"] < 10: 
                burn_x = d["smoke_x"] if d["smoke_x"] is not None else 0
                burn_y = d["smoke_y"] if d["smoke_y"] is not None else 0
                angle = np.arctan2(burn_y, burn_x)
                burn_x = EARTH_RADIUS * np.cos(angle)
                burn_y = EARTH_RADIUS * np.sin(angle)
                burning_effect(burn_x, burn_y)
            else:
                d["burning"] = False

    # --- Laser Targeting and Firing Logic ---
    if satellite["active"]:
        alive_debris = [d for d in debris_list if d["alive"]]
        if alive_debris:
            distances = [np.hypot(satellite["x"] - d["x"], satellite["y"] - d["y"]) for d in alive_debris]
            min_dist = min(distances)
            
            if min_dist <= LASER_RANGE:
                target_idx = distances.index(min_dist)
                target = alive_debris[target_idx]
                
                # Set targeted info for control panel
                targeted_debris = target
                target_distance = min_dist
                
                if frame_count % 20 == 0: 
                    draw_laser(satellite["x"], satellite["y"], target["x"], target["y"])
                    explosion_effect(target["x"], target["y"])
                    
                    # Destruction Logic (Push is Applied)
                    target["alive"] = False
                    target["smoke"] = True
                    target["smoke_x"] = target["x"]
                    target["smoke_y"] = target["y"]
                    
                    dist = np.hypot(target["x"], target["y"])
                    
                    # --- FIX: Use VISUAL_FALL_SPEED to ensure immediate, visible fall ---
                    fall_speed = VISUAL_FALL_SPEED 
                    
                    target["fall_vx"] = -target["x"] / dist * fall_speed
                    target["fall_vy"] = -target["y"] / dist * fall_speed
                    
                    target["burning"] = False

    # --- Display Control Panel ---
    display_control_panel(targeted_debris, target_distance)
    
    return

# -----------------------------------------------------
# 5. Run Animation
# -----------------------------------------------------
# Set frames to a high number (e.g., 10000) to ensure continuous, long-running operation
ani = animation.FuncAnimation(fig, update, frames=10000, interval=FRAME_INTERVAL, blit=False)
plt.show()