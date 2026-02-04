import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random
from matplotlib.patches import Wedge

# --- CONFIGURATION ---
MAX_RANGE = 100
SWEEP_SPEED = 1.0     # <--- REDUCED SPEED (Was 3.0)
DEBRIS_SPEED = 0.5
SATELLITE_SPEED = 0.3
DETECTION_ARC = 10.0
SWEEP_WEDGE_ANGLE = 60.0

# --- UPDATED COUNTS ---
MAX_DEBRIS = 4        # Limit to 4 debris
MAX_SATELLITES = 3    # Limit to 3 active satellites

DECAY_RATE = 0.08
DEFENSE_SAT_ALTITUDE = 800  # km
EARTH_RADIUS = 6371  # km

# PHYSICS CONSTANTS
DENSITY_ALUMINUM = 2.7  # g/cm^3

# --- DEBRIS CLASSIFICATION ---
DEBRIS_CLASSES = [
    {"type": "Hull Fragment", "size_min": 7.0, "size_max": 10.0, "risk": "CRITICAL"},
    {"type": "Nozzle Shard", "size_min": 4.0, "size_max": 7.0, "risk": "HIGH"},
    {"type": "Loose Bolt", "size_min": 2.0, "size_max": 4.0, "risk": "MODERATE"},
    {"type": "Paint Chip", "size_min": 1.0, "size_max": 2.0, "risk": "LOW"},
]

debris_data_list = []
satellite_data_list = []
debris_counter = 0
current_sweep_angle = 90

# --- HELPER: SYNTHETIC IMAGE GENERATOR ---
def generate_synthetic_image(debris_type):
    base = np.zeros((64, 64))
    cx, cy = 32, 32
    for x in range(64):
        for y in range(64):
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            if "Fragment" in debris_type:
                if dist < 12 and (x + y) % 5 != 0: base[x, y] = random.uniform(0.6, 1.0)
            elif "Shard" in debris_type:
                if abs(x - y) < 5 and dist < 15: base[x, y] = random.uniform(0.6, 1.0)
            elif "Bolt" in debris_type:
                if dist < 6: base[x, y] = random.uniform(0.8, 1.0)
            else:
                if dist < 4: base[x, y] = random.uniform(0.5, 0.8)
    return base + np.random.rand(64, 64) * 0.2

# --- FIGURE SETUP ---
fig, (ax_radar, ax_info) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={'width_ratios': [2, 1.2]})
fig.patch.set_facecolor('#080808')

# 1. RADAR AXIS
ax_radar.set_facecolor('#080808')
ax_radar.set_xlim([-MAX_RANGE, MAX_RANGE])
ax_radar.set_ylim([-MAX_RANGE, MAX_RANGE])
ax_radar.set_aspect('equal')
ax_radar.set_xticks([]); ax_radar.set_yticks([])
ax_radar.set_title("ORBITAL SURVEILLANCE RADAR", color='#39FF14', fontsize=14, fontfamily='monospace', pad=20)

# 2. INFO AXIS
ax_info.set_facecolor('#001100')
ax_info.set_xticks([]); ax_info.set_yticks([])
ax_info.set_title("TARGET TELEMETRY & MITIGATION", color='white', fontsize=12, fontfamily='monospace')

empty_img = np.zeros((64, 64))
target_display = ax_info.imshow(empty_img, cmap='inferno', vmin=0, vmax=1, extent=[10, 90, 60, 95])
info_text = ax_info.text(5, 55, "STATUS: SCANNING...", color='#39FF14', fontsize=10, fontfamily='monospace', verticalalignment='top')
ax_info.set_xlim(0, 100); ax_info.set_ylim(0, 100)

# --- DRAW GRID ---
GRID_COLOR = '#39FF14'
ranges = np.linspace(0, MAX_RANGE, 5)
for r in ranges:
    ax_radar.plot(r * np.cos(np.linspace(0, 2 * np.pi, 100)),
                  r * np.sin(np.linspace(0, 2 * np.pi, 100)),
                  color=GRID_COLOR, linewidth=0.5, alpha=0.3)
    if r > 0:
        ax_radar.text(0, r + 2, f"{int(r)} km", color=GRID_COLOR, fontsize=8, alpha=0.8, fontfamily='monospace', ha='center', va='bottom')

radar_wedge = Wedge((0, 0), MAX_RANGE, theta1=0, theta2=0, color=GRID_COLOR, alpha=0.2)
ax_radar.add_patch(radar_wedge)

# --- SCATTER PLOTS ---
debris_scatters = ax_radar.scatter([], [], s=30, color='yellow', zorder=5, label='Unknown Debris')
satellite_scatters = ax_radar.scatter([], [], s=50, color='cyan', marker='s', zorder=4, label='Active Satellite')

legend = ax_radar.legend(loc='upper right', facecolor='#001100', edgecolor='#39FF14', fontsize=8)
for text in legend.get_texts(): text.set_color("white")

# --- LOGIC ---
def polar_to_cartesian(r, theta):
    rad = np.radians(theta)
    return r * np.cos(rad), r * np.sin(rad)

def create_debris_instance():
    global debris_counter
    debris_counter += 1
    debris_info = random.choice(DEBRIS_CLASSES)

    size_cm = random.uniform(debris_info['size_min'], debris_info['size_max'])
    velocity_kms = random.uniform(7.5, 12.0)

    # Physics
    radius_cm = size_cm / 2
    volume_cm3 = (4 / 3) * np.pi * (radius_cm ** 3)
    mass_g = volume_cm3 * DENSITY_ALUMINUM
    mass_kg = mass_g / 1000
    
    velocity_ms = velocity_kms * 1000
    energy_joules = 0.5 * mass_kg * (velocity_ms ** 2)
    energy_kj = energy_joules / 1000

    return {
        "id": debris_counter,
        "r": random.uniform(20, MAX_RANGE * 0.9),
        "angle": random.uniform(0, 360),
        "elevation": random.uniform(-15.0, 15.0),
        "velocity": velocity_kms,
        "mass_kg": mass_kg,
        "mitigation_kj": energy_kj,
        "vector_x": random.uniform(-1, 1),
        "vector_y": random.uniform(-1, 1),
        "vector_z": random.uniform(-0.5, 0.5),
        "status": 0.0,
        "type": debris_info['type'],
        "size": size_cm,
        "risk": debris_info['risk'],
        "image_data": generate_synthetic_image(debris_info['type'])
    }

# Initialize Satellites
for _ in range(MAX_SATELLITES):
    satellite_data_list.append({
        "r": random.uniform(40, MAX_RANGE * 0.8),
        "angle": random.uniform(0, 360)
    })

def animate(frame):
    global current_sweep_angle

    # 1. Generate Debris (Up to MAX_DEBRIS)
    if len(debris_data_list) < MAX_DEBRIS and frame % 20 == 0:
        debris_data_list.append(create_debris_instance())

    # 2. Update Radar Sweep
    old_angle = current_sweep_angle
    current_sweep_angle = (current_sweep_angle - SWEEP_SPEED) % 360
    radar_wedge.set_theta1((current_sweep_angle - SWEEP_WEDGE_ANGLE) % 360)
    radar_wedge.set_theta2(current_sweep_angle)

    start_angle = (current_sweep_angle - DETECTION_ARC) % 360
    end_angle = old_angle

    # 3. Process Debris
    debris_coords = []
    debris_sizes = []
    debris_colors = []
    target_lock = None

    i = 0
    while i < len(debris_data_list):
        d = debris_data_list[i]
        d["angle"] = (d["angle"] - DEBRIS_SPEED) % 360
        debris_coords.append(polar_to_cartesian(d["r"], d["angle"]))

        # Check Detection
        in_arc = False
        if start_angle > end_angle:
            in_arc = (d["angle"] >= start_angle) or (d["angle"] <= end_angle)
        else:
            in_arc = (d["angle"] >= start_angle and d["angle"] <= end_angle)

        if in_arc and d["status"] == 0:
            d["status"] = 1.0
            target_lock = d

        if d["status"] > 0:
            d["status"] -= DECAY_RATE
            if d["status"] <= 0: d["status"] = 0

        # Visuals
        if d["status"] > 0:
            debris_sizes.append(150)
            debris_colors.append((1, 0, 0, d["status"]))
        else:
            debris_sizes.append(20)
            debris_colors.append((1, 1, 0, 0.4))
        i += 1

    debris_scatters.set_offsets(debris_coords)
    debris_scatters.set_sizes(debris_sizes)
    debris_scatters.set_color(debris_colors)

    # 4. Process Satellites
    sat_coords = []
    for sat in satellite_data_list:
        sat["angle"] = (sat["angle"] - SATELLITE_SPEED) % 360
        sat_coords.append(polar_to_cartesian(sat["r"], sat["angle"]))
    satellite_scatters.set_offsets(sat_coords)

    # 5. Update Target Info Panel
    if target_lock:
        target_display.set_data(target_lock['image_data'])

        dist_to_sat = target_lock['r']
        az = target_lock['angle']
        el = target_lock['elevation']
        traj_vec = f"[{target_lock['vector_x']:.2f}, {target_lock['vector_y']:.2f}, {target_lock['vector_z']:.2f}]"

        # --- STATS BLOCK WITH FULL KNOWLEDGE ---
        stats = (
            f"ID: #{target_lock['id']} | TYPE: {target_lock['type']}\n"
            f"--------------------------------------\n"
            f"DETECTED RANGE:        {dist_to_sat:.2f} km\n"
            f"OBJECT SIZE (DIA):     {target_lock['size']:.2f} cm\n"
            f"EST. MASS:             {target_lock['mass_kg']*1000:.1f} g\n"
            f"RELATIVE VELOCITY:     {target_lock['velocity']:.2f} km/s\n"
            f"\n"
            f"BEARING (AZ/EL):       {az:.1f}° / {el:.1f}°\n"
            f"TRAJECTORY:           {traj_vec}\n"
            f"\n"
            f"MITIGATION ENERGY REQ: {target_lock['mitigation_kj']:.2f} kJ\n"
            f"RISK LEVEL:            {target_lock['risk']}"
        )
        info_text.set_text(stats)

        if target_lock['risk'] == "CRITICAL":
            info_text.set_color('#FF3333')  # Red
        elif target_lock['risk'] == "HIGH":
            info_text.set_color('#FFAA00')  # Orange
        else:
            info_text.set_color('#39FF14')  # Green
    else:
        info_text.set_color('#39FF14')

    return radar_wedge, debris_scatters, satellite_scatters, target_display, info_text

ani = animation.FuncAnimation(fig, animate, interval=50, blit=True)
plt.show()