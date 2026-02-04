#SIH_Ninth.py
import matplotlib
matplotlib.use("TkAgg")  # IMPORTANT for animation on Windows

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from PIL import Image

# -----------------------------------------------------
# Enable emoji for plot text
# -----------------------------------------------------
plt.rcParams["font.family"] = "Segoe UI Emoji"

# -----------------------------------------------------
# Simulation Parameters
# -----------------------------------------------------
EARTH_RADIUS = 6371
TARGET_ORBIT = EARTH_RADIUS + 500  # Not used for orbit circle now

# Rocket initial position
rocket = {"x": -3000, "y": -EARTH_RADIUS - 1000, "name": "Rocket"}

# Satellite
satellite = {"x": None, "y": None, "active": False, "name": "Defense Satellite"}

# Debris list
debris_list = []

# -----------------------------------------------------
# Load Earth image and create alpha mask to remove white bg
# Note: Requires Earth.jpg in the same directory, or provide correct path
# For now, we'll skip loading the image and use a blue circle instead
# If Earth.jpg is available, uncomment the lines below and provide the correct path
# earth_img_path = r"Earth.jpg"  # Place Earth.jpg in the project root directory
try:
    earth_img_path = "Earth.jpg"
    earth_img = Image.open(earth_img_path).convert("RGBA")
except FileNotFoundError:
    # If image not found, create a placeholder
    earth_img = Image.new("RGBA", (100, 100), (0, 0, 255, 255))
earth_arr = np.array(earth_img)

# Make white pixels transparent
# Any pixel close to white (255,255,255) will be fully transparent
threshold = 245
r, g, b, a = earth_arr.T
white_areas = (r > threshold) & (g > threshold) & (b > threshold)
earth_arr[..., 3][white_areas.T] = 0  # Set alpha to 0

# -----------------------------------------------------
# Figure Setup
# -----------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_facecolor("black")
ax.set_aspect("equal")

# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------
def draw_laser(x1, y1, x2, y2):
    return ax.plot([x1, x2], [y1, y2], color="red", linewidth=2, alpha=0.7)[0]

def explosion_effect(x, y):
    return ax.scatter(x, y, s=300, color="yellow", alpha=0.9)

def smoke_cloud(x, y):
    return ax.scatter(x, y, s=200, color="gray", alpha=0.5)

def create_debris(i):
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(EARTH_RADIUS + 1000, EARTH_RADIUS + 6000)
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    speed = random.uniform(5, 30)
    direction = random.uniform(0, 2 * np.pi)
    vx = speed * np.cos(direction)
    vy = speed * np.sin(direction)
    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "name": f"Debris {i}",
        "alive": True,
        "smoke": False,
        "smoke_y": None
    }

def draw_earth():
    try:
        ax.imshow(earth_arr, extent=[-EARTH_RADIUS, EARTH_RADIUS, -EARTH_RADIUS, EARTH_RADIUS])
    except:
        # Fallback: draw a blue circle if image is not available
        circle = plt.Circle((0, 0), EARTH_RADIUS, color='blue', alpha=0.3)
        ax.add_patch(circle)
    ax.text(0, -EARTH_RADIUS - 500, "🌍 Earth", color="white", ha="center", fontsize=12)

# -----------------------------------------------------
# Animation Logic
# -----------------------------------------------------
frame_count = 0
debris_counter = 0

def update(frame):
    global frame_count, debris_counter
    frame_count += 1
    ax.clear()
    ax.set_facecolor("black")

    draw_earth()

    # Rocket Launch
    if not satellite["active"]:
        rocket["y"] += 120
        ax.scatter(rocket["x"], rocket["y"], s=200, color="orange")
        ax.text(rocket["x"] + 300, rocket["y"], "🚀 Rocket Launch", color="white")
        if rocket["y"] >= TARGET_ORBIT:
            satellite["active"] = True
            satellite["x"] = rocket["x"]
            satellite["y"] = rocket["y"]
    else:
        angle = frame * 0.05
        satellite["x"] = TARGET_ORBIT * np.cos(angle)
        satellite["y"] = TARGET_ORBIT * np.sin(angle)
        ax.scatter(satellite["x"], satellite["y"], s=150, color="cyan")
        ax.text(satellite["x"] + 200, satellite["y"], "🛰 Defense Satellite", color="white")

    # Debris
    if frame_count % 10 == 0:
        debris_counter += 1
        debris_list.append(create_debris(debris_counter))

    for d in debris_list:
        if d["alive"]:
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            ax.scatter(d["x"], d["y"], s=100, color="red")
            ax.text(d["x"] + 200, d["y"], d["name"], color="white", fontsize=8)
        elif d["smoke"]:
            d["smoke_y"] -= 150
            smoke_cloud(d["x"], d["smoke_y"])
            if d["smoke_y"] <= -EARTH_RADIUS:
                d["smoke"] = False

    # Laser
    if satellite["active"]:
        alive_debris = [d for d in debris_list if d["alive"]]
        if alive_debris:
            target = min(alive_debris, key=lambda d: np.hypot(satellite["x"] - d["x"], satellite["y"] - d["y"]))
            if frame_count % 20 == 0:
                draw_laser(satellite["x"], satellite["y"], target["x"], target["y"])
                explosion_effect(target["x"], target["y"])
                target["alive"] = False
                target["smoke"] = True
                target["smoke_y"] = target["y"]

    ax.set_xlim(-9000, 9000)
    ax.set_ylim(-9000, 9000)
    ax.set_title("Space Debris Defense System (Live Simulation)", color="white")

# -----------------------------------------------------
# Run Animation
# -----------------------------------------------------
ani = animation.FuncAnimation(fig, update, frames=1000, interval=80)
plt.show()
