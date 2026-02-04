# for your works   Real-Time Space Debris Tracking & Laser Deflection (Python Simulation) 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random

# --- System Configuration ---
NUM_DEBRIS = 25
EARTH_RADIUS = 6371   # km
ORBIT_RADIUS = EARTH_RADIUS + 500  # ~500 km LEO orbit
LASER_RANGE = 1000    # km range of laser
LASER_POWER = 1.0     # relative laser intensity
TIME_STEP = 0.1       # seconds per frame (simulation time)
SOLAR_POWER = True     # laser powered by solar energy

# --- Initialize Debris Objects ---
np.random.seed(42)
angles = np.random.rand(NUM_DEBRIS) * 2 * np.pi
speeds = np.random.uniform(0.5, 1.0, NUM_DEBRIS)
debris_positions = np.array([
    [ORBIT_RADIUS * np.cos(a), ORBIT_RADIUS * np.sin(a)] for a in angles
])
debris_velocities = np.array([
    [-s * np.sin(a), s * np.cos(a)] for a, s in zip(angles, speeds)
])

# Laser station on Earth (equatorial)
laser_position = np.array([EARTH_RADIUS + 100, 0])  # at ground + 100 km

# --- Visualization Setup ---
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-8000, 8000)
ax.set_ylim(-8000, 8000)
ax.set_aspect('equal')
ax.set_title("Real-Time Space Debris Detection and Laser Deflection")

# Draw Earth
earth = plt.Circle((0, 0), EARTH_RADIUS, color='blue', alpha=0.3)
ax.add_artist(earth)

# Scatter plots
debris_scatter = ax.scatter(debris_positions[:, 0], debris_positions[:, 1], color='white', s=20)
laser_beam, = ax.plot([], [], 'r--', lw=1.5)

# --- Mock ML Detection Function ---
def detect_debris(debris_pos):
    """
    Simulates ML detection: returns debris within laser range and line of sight.
    """
    detected = []
    for i, pos in enumerate(debris_pos):
        distance = np.linalg.norm(pos - laser_position)
        if distance < LASER_RANGE:
            detected.append(i)
    return detected

# --- Laser Targeting Logic ---
def fire_laser(target_index):
    """
    Laser gently changes debris trajectory (ablation thrust).
    """
    thrust_vector = (debris_positions[target_index] - laser_position)
    thrust_vector /= np.linalg.norm(thrust_vector)
    debris_velocities[target_index] += 0.05 * LASER_POWER * thrust_vector  # push away

# --- Real-Time Update Function ---
def update(frame):
    global debris_positions, debris_velocities
    debris_positions += debris_velocities * TIME_STEP * 100  # scaled motion

    detected = detect_debris(debris_positions)
    if detected:
        target = random.choice(detected)
        fire_laser(target)
        # Show laser beam
        laser_beam.set_data([laser_position[0], debris_positions[target][0]],
                            [laser_position[1], debris_positions[target][1]])
    else:
        laser_beam.set_data([], [])

    # Update debris visuals
    debris_scatter.set_offsets(debris_positions)
    return debris_scatter, laser_beam

# --- Run Animation ---
ani = FuncAnimation(fig, update, frames=500, interval=100, blit=True)
plt.style.use('dark_background')
plt.show()