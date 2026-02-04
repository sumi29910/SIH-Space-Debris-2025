import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import sys
import os

# --- 1. CONFIGURATION ---
MAX_RANGE_XY = 100  # Max horizontal range (km)
MAX_ALTITUDE = 150  # Max Z-axis altitude (km)
DEBRIS_SPEED = 0.5  # Speed in degrees per frame
CSV_FILENAME = 'debris_data.csv'  # External dataset file

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

# --- 3. DATA LOADING FUNCTION (FROM EXTERNAL CSV FILE) ---
def load_debris_data_from_file(filename):
    """Loads debris data from an external CSV file using pandas."""
    global debris_counter, debris_data_list
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"❌ Error: Dataset file '{filename}' not found!")
        print("📁 Please place your CSV file in the same directory as this script.")
        print("\n📋 Required CSV format (save as 'debris_data.csv'):")
        print("type,size,risk,r,angle,z")
        print("Rocket Body,Large,CRITICAL,80,45,105")
        print("Fragment,Small,HIGH,50,180,140")
        sys.exit(1)
    
    try:
        # Load CSV from external file
        df = pd.read_csv(filename)
        print(f"📊 Dataset loaded: {filename}")
        print(f"📈 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print("\n🔍 First 5 rows preview:")
        print(df.head())
        
        # Ensure required columns are present
        required_cols = ['type', 'size', 'risk', 'r', 'angle', 'z']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Error: CSV must contain columns: {required_cols}")
            print(f"📋 Current columns: {list(df.columns)}")
            sys.exit(1)

        # Clear previous data and populate from dataset
        debris_data_list.clear()
        debris_counter = 0
        
        for index, row in df.iterrows():
            debris_counter += 1
            risk = row['risk'].upper()
            color, scatter_size = get_risk_color(risk)
            
            new_debris = {
                "id": debris_counter,
                "r": float(row['r']),
                "angle": float(row['angle']),
                "z": float(row['z']),
                "type": row['type'],
                "size": row['size'],
                "risk": risk,
                "color": color,
                "scatter_size": scatter_size,
            }
            debris_data_list.append(new_debris)
        
        print(f"\n✅ Successfully loaded {len(debris_data_list)} debris objects from dataset.")
        print("🎨 Risk distribution:")
        risk_counts = df['risk'].value_counts()
        for risk_level, count in risk_counts.items():
            print(f"   {risk_level}: {count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading dataset file: {e}")
        sys.exit(1)

# --- 4. EXECUTION START (LOAD FROM EXTERNAL FILE) ---
print("🚀 Loading orbital debris dataset...")
load_success = load_debris_data_from_file(CSV_FILENAME)

if not load_success:
    sys.exit(1)

# --- 5. FIGURE SETUP (3D View) ---
fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')
fig.patch.set_facecolor('#080808')
ax.set_facecolor('#000000')

ax.set_title(f"3D ORBITAL DEBRIS FIELD - {len(debris_data_list)} Objects from Dataset", 
             color='white', fontsize=16, pad=20)
ax.set_xlabel('X - Downrange Distance (km)', color='white', fontsize=12)
ax.set_ylabel('Y - Lateral Distance (km)', color='white', fontsize=12)
ax.set_zlabel('Z - Altitude (km)', color='white', fontsize=12)

ax.set_xlim([-MAX_RANGE_XY, MAX_RANGE_XY])
ax.set_ylim([-MAX_RANGE_XY, MAX_RANGE_XY])
ax.set_zlim([0, MAX_ALTITUDE])

# Styling
ax.tick_params(axis='both', colors='white', labelsize=10)
ax.w_xaxis.pane.fill = False
ax.w_yaxis.pane.fill = False
ax.w_zaxis.pane.fill = False
ax.w_xaxis.line.set_color('white')
ax.w_yaxis.line.set_color('white')
ax.w_zaxis.line.set_color('white')

# --- 6. ENHANCED SINGLE-FRAME PLOTTING FUNCTION ---
def plot_single_frame(frame):
    """Calculates and plots all debris positions for a single frame."""
    
    x_coords, y_coords, z_coords = [], [], []
    colors, sizes = [], []
    
    for d in debris_data_list:
        # Apply Orbital Movement (Rotation around Z-axis)
        current_angle = (d["angle"] - frame * DEBRIS_SPEED) % 360
        
        # Convert to 3D Cartesian coordinates
        x, y, z = polar_to_cartesian(d["r"], current_angle, d["z"])
        
        x_coords.append(x)
        y_coords.append(y)
        z_coords.append(z)
        colors.append(d["color"])
        sizes.append(d["scatter_size"])
        
        # Annotate CRITICAL debris only
        if d['risk'] == "CRITICAL":
            ax.text(x, y, z+2, f"ID:{d['id']} - {d['risk']}", 
                   color='red', fontsize=9, weight='bold', zorder=10)

    # Create enhanced 3D scatter plot
    scatter = ax.scatter(x_coords, y_coords, z_coords, c=colors, s=sizes, 
                        marker='o', alpha=0.85, edgecolors='white', linewidth=0.8)
    
    # Dynamic camera view
    ax.view_init(elev=25, azim=frame * 0.8)
    
    return scatter

# --- 7. EXECUTION ---
print("\n" + "="*60)
print("🌌 3D ORBITAL DEBRIS VISUALIZATION - DATASET MODE")
print("="*60)

print("🎬 Rendering initial frame from dataset...")
plot_single_frame(frame=0)

# Add legend
risk_legend = {
    'CRITICAL': ('red', 150),
    'HIGH': ('orange', 100),
    'MODERATE': ('yellow', 50),
    'LOW': ('green', 30)
}

legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                             markerfacecolor=color, markersize=np.sqrt(size/6),
                             label=f"{risk} Risk", markeredgecolor='white') 
                  for risk, (color, size) in risk_legend.items()]
ax.legend(handles=legend_elements, loc='upper left', facecolor='black', 
          edgecolor='white', labelcolor='white')

plt.tight_layout()
plt.show()

print("\n✅ Visualization complete! Dataset successfully visualized.")
print(f"📊 Total debris objects: {len(debris_data_list)}")
