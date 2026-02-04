import pandas as pd

# -----------------------------
# CONFIGURE YOUR ORIGINAL FILE
# -----------------------------
input_csv = "simulation_log.csv"      # <-- change to your actual CSV filename
output_csv = "simulation_input.csv"       # <-- new corrected CSV

# -----------------------------
# REQUIRED COLUMNS FOR SIMULATION
# -----------------------------
required_cols = ['type', 'size', 'risk', 'r', 'angle', 'z']

# -----------------------------
# MAPPING YOUR LARGE CSV COLUMNS
# TO THE REQUIRED COLUMN NAMES
# -----------------------------
column_map = {
    'Object_Type': 'type',
    'Size_cm': 'size',
    'Risk_Level': 'risk',
    'Range_km': 'r',
    'Angle_deg': 'angle'
}

# -----------------------------
# LOAD LARGE CSV FILE
# -----------------------------
df = pd.read_csv(input_csv)

# -----------------------------
# RENAME MATCHING COLUMNS
# -----------------------------
df = df.rename(columns=column_map)

# -----------------------------
# ADD ANY MISSING COLUMNS
# -----------------------------
for col in required_cols:
    if col not in df.columns:
        if col == 'z':
            df[col] = 0     # default z-coordinate
        else:
            df[col] = None  # default filler for missing columns

# -----------------------------
# FILTER TO REQUIRED FORMAT ONLY
# -----------------------------
df = df[required_cols]

# -----------------------------
# SAVE CLEAN CSV FOR SIMULATION
# -----------------------------
df.to_csv(output_csv, index=False)

print("\nCSV successfully converted!")
print(f"Saved as: {output_csv}\n")
