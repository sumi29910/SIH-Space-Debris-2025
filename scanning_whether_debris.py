import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import sys
import io

# --- 1. CONFIGURATION ---
MAX_RANGE_XY = 100 
MAX_ALTITUDE = 150 
DEBRIS_SPEED = 0.5 
CSV_FILENAME = 'debris_data.csv' 

# --- IN-MEMORY CSV DATA ---
csv_data = """type,size,risk,r,angle,z
Rocket Body,Large,CRITICAL,80,45,105
Fragment,Small,HIGH,50,180,140
Satellite,Medium,MODERATE,65,300,80
Fragment,Small,LOW,30,90,50
Other,Medium,CRITICAL,95,225,120
"""

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

# --- 3. DATA LOADING FUNCTION (CSV) ---
def load_debris_data_from_csv(csv_string):
    """Loads debris data from a CSV string using pandas and processes them one by one."""
    global debris_counter
    
    try:
        df = pd.read_csv(io.StringIO(csv_string))
        
        required_cols = ['type', 'size', 'risk', 'r', 'angle', 'z']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: CSV data must contain columns: {required_cols}")
            sys.exit()

        for index, row in df.iterrows():
            debris_counter += 1
            risk = row['risk'].upper()
            color, scatter_size = get_risk_color(risk)
            
            new_debris = {
                "id": debris_counter,
                "r": row['r'],
                "angle": row['angle'],
                "z": row['z'],
                "type": row['type'],
                "size": row['size'],
                "risk": risk,
                "color": color,
                "scatter_size": scatter_size,
            }
            # --- PROCESS AND ADD OBJECT ONE BY ONE ---
            debris_data_list.append(new_debris)
            print(f"-> Processing ID {new_debris['id']}: {new_debris['type']} at {new_debris['z']:.0f}km (Risk: {new_debris['risk']})")
            
        print(f"\nSuccessfully loaded {len(debris_data_list)} debris objects in total.")
        
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        sys.exit()

# --- 5. FIGURE SETUP (3D View TEMPLATE) ---
# (Setup done inside plot_cumulative_frame for fresh rendering)

def plot_cumulative_frame(frame_title, frame_number):
    """Plots the current list of debris in a new figure."""
    if not debris_data_list:
        return

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor('#080808')
    ax.set_facecolor('#000000') 

    ax.set_title(f"CUMULATIVE DEBRIS FIELD - {frame_title}", color='white', fontsize=14)
    ax.set_xlabel('X - Downrange Distance (km)', color='white')
    ax.set_ylabel('Y - Lateral Distance (km)', color='white')
    ax.set_zlabel('Z - Altitude (km)', color='white')

    ax.set_xlim([-MAX_RANGE_XY, MAX_RANGE_XY])
    ax.set_ylim([-MAX_RANGE_XY, MAX_RANGE_XY])
    ax.set_zlim([0, MAX_ALTITUDE])

    ax.tick_params(axis='both', colors='white')

    # --- Fix for Matplotlib 3.5+ ---
    try:
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        ax.zaxis.pane.set_visible(False)
    except AttributeError:
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis._axinfo['pane']['visible'] = False


    x_coords, y_coords, z_coords = [], [], []
    colors, sizes = [], []

    # Plot all debris added so far
    for d in debris_data_list:
        # Calculate position for static display (Frame 0 of movement)
        x, y, z = polar_to_cartesian(d["r"], d["angle"], d["z"])
        
        x_coords.append(x)
        y_coords.append(y)
        z_coords.append(z)
        colors.append(d["color"])
        sizes.append(d["scatter_size"])
        
        # Annotate CRITICAL debris
        if d['risk'] == "CRITICAL":
            ax.text(x, y, z, f"ID:{d['id']} ({d['z']:.0f}km)", color='red', fontsize=8, zorder=15)

    ax.scatter(x_coords, y_coords, z_coords, c=colors, s=sizes, marker='o')
    ax.view_init(elev=30, azim=30) # Fixed view
    
    # plt.show() # Disabled for text-based output

# --- 4. EXECUTION START ---
print("\n" + "="*70)
print("VISUAL PROCESSING INITIATED: Loading and Plotting Debris Object by Object")
print("="*70)

# Load data to populate debris_data_list
load_debris_data_from_csv(csv_data)

# --- 7. CUMULATIVE VISUALIZATION ---

print("\n--- Plotting Cumulative Stages ---")

# Stage 1: Plot only the first object (ID 1)
# Temporarily truncate the list to show only the first item
temp_list = list(debris_data_list)
debris_data_list = debris_data_list[:1] 
plot_cumulative_frame("Stage 1: Rocket Body (CRITICAL)", 1)
print(f"Visualization Output for Stage 1 (1 Debris Object):")


# Stage 2: Plot up to the second object (ID 2)
debris_data_list = temp_list[:2]
plot_cumulative_frame("Stage 2: Rocket Body + Fragment (HIGH)", 2)
print(f"\nVisualization Output for Stage 2 (2 Debris Objects):")


# Stage 3: Plot all objects (ID 1 through ID 5)
debris_data_list = temp_list # Restore the full list
plot_cumulative_frame("Stage 3: All 5 Debris Objects Loaded", 3)
print(f"\nVisualization Output for Stage 3 (5 Debris Objects):")
