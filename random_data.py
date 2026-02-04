import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Generate 2000 rows of orbital debris data
n_samples = 2000

# Define categorical options matching your visualization code
debris_types = ['Satellite', 'Rocket_Body', 'Fragment', 'Paint_Flake', 'Battery']
sizes = ['Small', 'Medium', 'Large', 'XL']
risk_levels = ['Low', 'Moderate', 'High', 'Critical']

# Create realistic distributions
data = {
    'type': np.random.choice(debris_types, n_samples, p=[0.3, 0.25, 0.25, 0.15, 0.05]),
    'size': np.random.choice(sizes, n_samples, p=[0.5, 0.3, 0.15, 0.05]),
    # Risk distribution: more low risk, fewer critical
    'risk': np.random.choice(risk_levels, n_samples, p=[0.5, 0.3, 0.15, 0.05]),
    # Radial distance: clustered around typical LEO/MEO orbits
    'r': np.random.normal(80, 25, n_samples).clip(10, 100),
    # Random initial angles (0-360 degrees)
    'angle': np.random.uniform(0, 360, n_samples),
    # Altitude: peaks around common orbital shells (LEO: 200-2000km, but capped at 150km for viz)
    'z': np.random.exponential(40, n_samples).clip(5, 150)
}

# Create DataFrame and save as CSV
df = pd.DataFrame(data)
df.to_csv('debris_data.csv', index=False)

print(f"✅ Created 'debris_data.csv' with {len(df)} rows")
print(f"📊 Columns: {list(df.columns)}")
print(f"🔢 Shape: {df.shape}")
print("\n📈 Data preview:")
print(df.head())
print(f"\nRisk distribution:\n{df['risk'].value_counts()}")