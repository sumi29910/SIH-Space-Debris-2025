import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import sys
import os

# --- 1. CONFIGURATION ---
MAX_RANGE_XY = 100 # Max horizontal range (km)
MAX_ALTITUDE = 150 # Max Z-axis altitude (km)
DEBRIS_SPEED = 0.5 # Speed in degrees per frame (affects rotation speed)

# --- 2. GLOBAL LISTS & HELPERS ---
debris_data_list = []
debris_counter = 0

def polar_to_cartesian(r, theta, z):
    """Converts Polar (r, theta) and Altitude (z) to Cartesian (x, y, z)."""
    rad = np.radians(theta)
    x = r * np.cos(rad)
    y = r * np.sin(rad)
    return x, y, z

def get_risk_color(risk):
    """Maps risk level to a color and marker size."""
    risk = risk.upper()
    if risk == "CRITICAL":
        return 'red', 150
    elif risk == "HIGH":
        return 'orange', 100
    elif risk == "MODERATE":
        return 'yellow', 50
    else:
        return 'green', 30

def get_valid_input(prompt, data_type=str, min_val=None, max_val=None):
    """Helper function for robust command-line input validation."""
    while True:
        try:
            value = data_type(input(prompt).strip())
            if min_val is not None and value < min_val:
                print(f"Error: Value must be at least {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Error: Value cannot exceed {max_val}.")
                continue
            return value
        except ValueError:
            print("Error: Invalid data type. Please enter the correct format.")
        except EOFError:
             # Handle EOF (Ctrl+D/Z) in case user stops input midway
             return None 
        except Exception:
             # Handle other unexpected errors
             return None


# --- 3. INPUT FUNCTION (GUI Replacement) ---
def get_user_debris_data():
    """Gathers debris data from the user via command-line input."""
    print("\n" + "="*50)
    print("🚀 ORBITAL DEBRIS DATA INPUT")
    print("Enter 'done' for type when finished.")
    print("="*50)

    while True:
        global debris_counter
        
        # --- Get Debris Type and Exit Condition ---
        type_input = input("Debris Type (e.g., Fragment, Bolt) or 'done': ").strip()
        if type_input.lower() == 'done':
            break
        
        # --- Get Required Parameters with Validation ---
        size = get_valid_input("Size (cm, 1.0 - 10.0): ", float, 1.0, 10.0)
        if size is None: break

        risk = input("Risk (LOW, MODERATE, HIGH, CRITICAL): ").strip().upper()
        if risk not in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            print("Invalid risk level. Defaulting to LOW.")
            risk = "LOW"
        
        r = get_valid_input(f"Horizontal Range 'r' (km, 0 - {MAX_RANGE_XY:.0f}): ", float, 0, MAX_RANGE_XY)
        if r is None: break

        angle = get_valid_input("Orbital Angle (degrees, 0 - 360): ", float, 0, 360)
        if angle is None: break

        z = get_valid_input(f"Altitude 'z' (km, 0 - {MAX_ALTITUDE:.0f}): ", float, 0, MAX_ALTITUDE)
        if z is None: break

        # --- Create and Store Data Point ---
        debris_counter += 1
        color, scatter_size = get_risk_color(risk)
        
        new_debris = {
            "id": debris_counter,
            "r": r,
            "angle": angle,
            "z": z,
            "type": type_input,
            "size": size,
            "risk": risk,
            "color": color,
            "scatter_size": scatter_size,
        }
        debris_data_list.append(new_debris)
        print(f"--> Debris ID #{debris_counter} recorded. ({type_input} at {r:.1f}km range, {z:.1f}km altitude)")
        print("-" * 50)

    if not debris_data_list:
        print("No debris entered. Exiting program.")
        sys.exit()

# --- 4. EXECUTION START ---
get_user_debris_data()


# --- 5. FIGURE SETUP (3D View) ---
# (Setup remains the same as previous 3D code)
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
fig.patch.set_facecolor('#080808')
ax.set_facecolor('#000000') 

ax.set_title("3D ORBITAL DEBRIS FIELD (User Data Feed)", color='white', fontsize=14)
ax.set_xlabel('X - Downrange Distance (km)', color='white')
ax.set_ylabel('Y - Lateral Distance (km)', color='white')
ax.set_zlabel('Z - Altitude (km)', color='white')

ax.set_xlim([-MAX_RANGE_XY, MAX_RANGE_XY])
ax.set_ylim([-MAX_RANGE_XY, MAX_RANGE_XY])
ax.set_zlim([0, MAX_ALTITUDE])

ax.tick_params(axis='both', colors='white')
ax.w_xaxis.pane.fill = False
ax.w_yaxis.pane.fill = False
ax.w_zaxis.pane.fill = False

debris_scatters = ax.scatter([], [], [], marker='o')


# --- 6. ANIMATION FUNCTION (Movement in 3D) ---
def animate_3d(frame):
    """Updates the position of the debris and the camera view."""
    
    x_coords, y_coords, z_coords = [], [], []
    colors, sizes = [], []
    
    # Clear old annotations (workaround for Matplotlib 3D text persistence)
    ax.texts = []
    
    for d in debris_data_list:
        # Orbital Movement (Rotation around Z-axis)
        d["angle"] = (d["angle"] - DEBRIS_SPEED) % 360
        
        # Convert to 3D Cartesian coordinates
        x, y, z = polar_to_cartesian(d["r"], d["angle"], d["z"])
        
        x_coords.append(x)
        y_coords.append(y)
        z_coords.append(z)
        colors.append(d["color"])
        sizes.append(d["scatter_size"])
        
        # Annotate the CRITICAL debris
        if d['risk'] == "CRITICAL" and frame % 50 == 0:
             ax.text(x, y, z, f"ID:{d['id']} - {d['risk']} ({d['z']:.1f}km)", 
                     color='red', fontsize=8, zorder=15)

    # Update the 3D scatter plot data
    debris_scatters._offsets3d = (x_coords, y_coords, z_coords)
    debris_scatters.set_color(colors)
    debris_scatters.set_sizes(sizes)
    
    # Rotate the view (simulates orbiting camera)
    ax.view_init(elev=30, azim=frame * 0.5) 
    
    # Return the artist objects to be redrawn
    return debris_scatters,

# --- 7. EXECUTION ---
# blit=False is used for stability in 3D plots
print("\n" + "="*50)
print("3D Visualization Initiated. Close the plot window to exit.")
print("="*50)

ani = animation.FuncAnimation(fig, animate_3d, frames=360, interval=50, blit=False) 
plt.show()