import numpy as np
import tkinter as tk
from tkinter import ttk
import math
import threading
import time

# ======================================
# ORBIT PHYSICS — REALISTIC
# ======================================
G = 6.67430e-11
M_EARTH = 5.972e24
R_EARTH = 6371000  # meters
MU = G * M_EARTH

def calculate_orbit_points(altitude_km, inclination_deg, eccentricity, num_points=360):
    """
    Calculate orbital path points for visualization
    Returns: list of (x, y) tuples in meters
    """
    altitude = altitude_km * 1000  # Convert to meters
    semi_major_axis = R_EARTH + altitude
    
    # For circular orbits, semi-major axis = radius
    # For elliptical orbits, adjust based on eccentricity
    if eccentricity > 0:
        # Perigee distance
        r_perigee = semi_major_axis * (1 - eccentricity)
        # Semi-major axis from perigee
        semi_major_axis = r_perigee / (1 - eccentricity)
    
    inclination = math.radians(inclination_deg)
    points = []
    
    for i in range(num_points):
        # True anomaly
        nu = 2 * math.pi * i / num_points
        
        # Distance from center (ellipse equation)
        r = semi_major_axis * (1 - eccentricity**2) / (1 + eccentricity * math.cos(nu))
        
        # Position in orbital plane (x, y)
        x_orbital = r * math.cos(nu)
        y_orbital = r * math.sin(nu)
        
        # Rotate by inclination (around x-axis)
        # For top-down view, we project to x-y plane
        x = x_orbital
        y = y_orbital * math.cos(inclination)
        z = y_orbital * math.sin(inclination)
        
        # For top-down view, we use x and y (projected)
        points.append((x, y))
    
    return points

def calculate_orbital_velocity(altitude_km, eccentricity=0):
    """Calculate orbital velocity for given altitude"""
    altitude = altitude_km * 1000
    r = R_EARTH + altitude
    # Circular orbit velocity
    v = math.sqrt(MU / r)
    return v

def calculate_orbital_period(altitude_km, eccentricity=0):
    """Calculate orbital period in minutes"""
    altitude = altitude_km * 1000
    semi_major_axis = R_EARTH + altitude
    if eccentricity > 0:
        r_perigee = semi_major_axis * (1 - eccentricity)
        semi_major_axis = r_perigee / (1 - eccentricity)
    
    period = 2 * math.pi * math.sqrt(semi_major_axis**3 / MU)
    return period / 60  # Convert to minutes


class OrbitVisualizer:
    def __init__(self, window):
        self.window = window
        self.window.title("Interactive Orbit Visualizer")
        self.window.geometry("1400x900")
        self.window.configure(bg='#0a0e27')
        
        # Orbit parameters
        self.altitude = 500  # km
        self.inclination = 51.6  # degrees
        self.eccentricity = 0.01
        self.orbit_type = "LEO"
        
        # Animation state
        self.animation_angle = 0
        self.animation_running = True
        self.animation_thread = None
        
        # Create UI
        self.create_ui()
        
        # Start animation
        self.start_animation()
        
    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_container = tk.Frame(self.window, bg='#0a0e27')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Visualization canvas
        canvas_frame = tk.Frame(main_container, bg='#0a0e27')
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas title
        title_label = tk.Label(
            canvas_frame,
            text="ORBITAL VISUALIZATION",
            font=("Arial", 16, "bold"),
            bg='#0a0e27',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 10))
        
        # Canvas for visualization
        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=700,
            bg='#0a0e27',
            highlightthickness=2,
            highlightbackground='#1a3a5a'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Control panel
        control_frame = tk.Frame(main_container, bg='#1a1a2e', width=400)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        control_frame.pack_propagate(False)
        
        self.create_control_panel(control_frame)
        
    def create_control_panel(self, parent):
        """Create the control panel with input fields"""
        # Title
        title = tk.Label(
            parent,
            text="ORBIT PARAMETERS",
            font=("Arial", 14, "bold"),
            bg='#1a1a2e',
            fg='#00d4ff'
        )
        title.pack(pady=20)
        
        # Input fields container
        inputs_frame = tk.Frame(parent, bg='#1a1a2e')
        inputs_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Altitude input
        self.create_input_field(
            inputs_frame,
            "ORBIT ALTITUDE (KM)",
            self.altitude,
            self.on_altitude_change
        )
        
        # Inclination input
        self.create_input_field(
            inputs_frame,
            "INCLINATION (°)",
            self.inclination,
            self.on_inclination_change
        )
        
        # Eccentricity input
        self.create_input_field(
            inputs_frame,
            "ECCENTRICITY",
            self.eccentricity,
            self.on_eccentricity_change
        )
        
        # Orbit type dropdown
        orbit_frame = tk.Frame(inputs_frame, bg='#1a1a2e')
        orbit_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(
            orbit_frame,
            text="ORBIT TYPE",
            font=("Arial", 10, "bold"),
            bg='#1a1a2e',
            fg='#ffffff'
        ).pack(anchor='w', pady=(0, 5))
        
        self.orbit_type_var = tk.StringVar(value=self.orbit_type)
        orbit_combo = ttk.Combobox(
            orbit_frame,
            textvariable=self.orbit_type_var,
            values=["LEO (Low Earth Orbit)", "MEO (Medium Earth Orbit)", 
                   "GEO (Geostationary Orbit)", "HEO (High Earth Orbit)"],
            state="readonly",
            font=("Arial", 10)
        )
        orbit_combo.pack(fill=tk.X)
        orbit_combo.bind("<<ComboboxSelected>>", self.on_orbit_type_change)
        
        # Update button
        update_btn = tk.Button(
            inputs_frame,
            text="UPDATE ORBIT",
            font=("Arial", 12, "bold"),
            bg='#00a8ff',
            fg='#ffffff',
            activebackground='#0099e6',
            activeforeground='#ffffff',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.update_orbit
        )
        update_btn.pack(pady=20, fill=tk.X)
        
        # Info display
        info_frame = tk.Frame(parent, bg='#1a1a2e')
        info_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        tk.Label(
            info_frame,
            text="ORBITAL INFORMATION",
            font=("Arial", 12, "bold"),
            bg='#1a1a2e',
            fg='#00d4ff'
        ).pack(pady=(0, 10))
        
        self.info_label = tk.Label(
            info_frame,
            text="",
            font=("Consolas", 10),
            bg='#1a1a2e',
            fg='#ffffff',
            justify=tk.LEFT,
            anchor='nw'
        )
        self.info_label.pack(fill=tk.BOTH, expand=True)
        
        # How to read section
        read_frame = tk.Frame(parent, bg='#1a1a2e')
        read_frame.pack(padx=20, pady=20, fill=tk.X)
        
        tk.Label(
            read_frame,
            text="HOW TO READ THIS VISUAL",
            font=("Arial", 11, "bold"),
            bg='#1a1a2e',
            fg='#ffffff'
        ).pack(anchor='w', pady=(0, 5))
        
        read_text = tk.Label(
            read_frame,
            text="The canvas shows a stylized top-down view of Earth with multiple orbital tracks. "
                 "The highlighted track corresponds to your selected parameters, while additional "
                 "rings indicate common operational shells. In a production system, this module "
                 "would connect to live TLE data or a dynamics engine.",
            font=("Arial", 9),
            bg='#1a1a2e',
            fg='#a0a0a0',
            justify=tk.LEFT,
            wraplength=360
        )
        read_text.pack(anchor='w')
        
    def create_input_field(self, parent, label_text, default_value, callback):
        """Create a labeled input field"""
        frame = tk.Frame(parent, bg='#1a1a2e')
        frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            frame,
            text=label_text,
            font=("Arial", 10, "bold"),
            bg='#1a1a2e',
            fg='#ffffff'
        ).pack(anchor='w', pady=(0, 5))
        
        entry = tk.Entry(
            frame,
            font=("Arial", 11),
            bg='#2a2a3e',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief=tk.FLAT,
            borderwidth=0
        )
        entry.insert(0, str(default_value))
        entry.pack(fill=tk.X, ipady=8)
        entry.bind('<Return>', lambda e: callback())
        entry.bind('<FocusOut>', lambda e: callback())
        
        # Store reference
        if label_text.startswith("ORBIT ALTITUDE"):
            self.altitude_entry = entry
        elif label_text.startswith("INCLINATION"):
            self.inclination_entry = entry
        elif label_text.startswith("ECCENTRICITY"):
            self.eccentricity_entry = entry
    
    def on_altitude_change(self):
        try:
            value = float(self.altitude_entry.get())
            if 160 <= value <= 36000:
                self.altitude = value
                self.update_orbit()  # Update orbit immediately when value changes
        except ValueError:
            pass
    
    def on_inclination_change(self):
        try:
            value = float(self.inclination_entry.get())
            if 0 <= value <= 180:
                self.inclination = value
                self.update_orbit()  # Update orbit immediately when value changes
        except ValueError:
            pass
    
    def on_eccentricity_change(self):
        try:
            value = float(self.eccentricity_entry.get())
            if 0 <= value < 1:
                self.eccentricity = value
                self.update_orbit()  # Update orbit immediately when value changes
        except ValueError:
            pass

    def update_orbit_parameters(self, altitude=None, inclination=None, eccentricity=None):
        """Method to update orbit parameters externally, useful for web interfaces"""
        if altitude is not None and 160 <= altitude <= 2000:
            self.altitude = altitude
        if inclination is not None and 0 <= inclination <= 180:
            self.inclination = inclination
        if eccentricity is not None and 0 <= eccentricity <= 0.1:
            self.eccentricity = eccentricity
        
        self.update_info()
        self.draw_visualization()
        
        return self.export_orbit_data()
    
    def on_orbit_type_change(self, event=None):
        orbit_type = self.orbit_type_var.get()
        # Extract orbit type abbreviation
        if "LEO" in orbit_type:
            self.orbit_type = "LEO"
            if not hasattr(self, 'altitude_entry') or not self.altitude_entry.get():
                self.altitude = 500
                if hasattr(self, 'altitude_entry'):
                    self.altitude_entry.delete(0, tk.END)
                    self.altitude_entry.insert(0, "500")
        elif "MEO" in orbit_type:
            self.orbit_type = "MEO"
            if not hasattr(self, 'altitude_entry') or not self.altitude_entry.get():
                self.altitude = 20000
                if hasattr(self, 'altitude_entry'):
                    self.altitude_entry.delete(0, tk.END)
                    self.altitude_entry.insert(0, "20000")
        elif "GEO" in orbit_type:
            self.orbit_type = "GEO"
            if not hasattr(self, 'altitude_entry') or not self.altitude_entry.get():
                self.altitude = 35786
                if hasattr(self, 'altitude_entry'):
                    self.altitude_entry.delete(0, tk.END)
                    self.altitude_entry.insert(0, "35786")
        elif "HEO" in orbit_type:
            self.orbit_type = "HEO"
            if not hasattr(self, 'altitude_entry') or not self.altitude_entry.get():
                self.altitude = 50000
                if hasattr(self, 'altitude_entry'):
                    self.altitude_entry.delete(0, tk.END)
                    self.altitude_entry.insert(0, "50000")
    
    def update_orbit(self):
        """Update orbit visualization"""
        # Only update if the values have actually changed
        try:
            new_altitude = float(self.altitude_entry.get())
            if 160 <= new_altitude <= 36000:
                self.altitude = new_altitude
        except ValueError:
            pass
        
        try:
            new_inclination = float(self.inclination_entry.get())
            if 0 <= new_inclination <= 180:
                self.inclination = new_inclination
        except ValueError:
            pass
        
        try:
            new_eccentricity = float(self.eccentricity_entry.get())
            if 0 <= new_eccentricity < 1:
                self.eccentricity = new_eccentricity
        except ValueError:
            pass
        
        self.update_info()
        self.draw_visualization()
    
    def update_info(self):
        """Update orbital information display"""
        velocity = calculate_orbital_velocity(self.altitude, self.eccentricity)
        period = calculate_orbital_period(self.altitude, self.eccentricity)
        
        info_text = (
            f"Altitude: {self.altitude:.1f} km\n"
            f"Inclination: {self.inclination:.1f}°\n"
            f"Eccentricity: {self.eccentricity:.4f}\n"
            f"Orbit Type: {self.orbit_type}\n\n"
            f"Orbital Velocity: {velocity/1000:.2f} km/s\n"
            f"Orbital Period: {period:.1f} minutes\n"
            f"({period/60:.2f} hours)\n\n"
            f"Perigee: {(R_EARTH + self.altitude * 1000 * (1 - self.eccentricity))/1000:.1f} km\n"
            f"Apogee: {(R_EARTH + self.altitude * 1000 * (1 + self.eccentricity))/1000:.1f} km"
        )
        
        self.info_label.config(text=info_text)
    
    def draw_earth(self):
        """Draw Earth at the center using Earth.jpg image"""
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        
        # Earth radius in pixels (scaled)
        earth_radius_px = 80
        
        # Try to load and draw Earth.jpg if it exists
        try:
            from PIL import Image, ImageTk, ImageDraw
            import os
            
            # Check if Earth.jpg exists in the current directory
            earth_img_path = "Earth.jpg"
            if os.path.exists(earth_img_path):
                # Load the image
                img = Image.open(earth_img_path)
                
                # Convert to RGBA to handle transparency
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a circular mask to remove the background
                mask = Image.new('L', img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
                
                # Apply the mask to the image
                img.putalpha(mask)
                
                # Resize the image to fit within the earth radius
                img = img.resize((int(earth_radius_px * 2), int(earth_radius_px * 2)), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                self.earth_photo = ImageTk.PhotoImage(img)
                
                # Draw the image at the center
                self.canvas.create_image(center_x, center_y, image=self.earth_photo)
            else:
                # Fallback: Draw Earth with gradient effect (multiple circles)
                for i in range(5, 0, -1):
                    radius = earth_radius_px * (i / 5)
                    alpha = 0.3 + 0.7 * (i / 5)
                    color_int = int(30 + (60 - 30) * (i / 5))
                    color = f"#{color_int:02x}{color_int + 20:02x}{color_int + 40:02x}"
                    self.canvas.create_oval(
                        center_x - radius, center_y - radius,
                        center_x + radius, center_y + radius,
                        fill=color, outline="", width=0
                    )
                
                # Main Earth circle
                self.canvas.create_oval(
                    center_x - earth_radius_px, center_y - earth_radius_px,
                    center_x + earth_radius_px, center_y + earth_radius_px,
                    fill="#1e3a8a", outline="#3b82f6", width=2
                )
                
                # Add some detail (continents suggestion)
                for i in range(3):
                    offset_x = (i - 1) * 20
                    offset_y = (i % 2) * 15 - 7
                    self.canvas.create_oval(
                        center_x + offset_x - 10, center_y + offset_y - 10,
                        center_x + offset_x + 10, center_y + offset_y + 10,
                        fill="#2563eb", outline="", width=0
                    )
        except ImportError:
            # PIL not available, fallback to original drawing
            for i in range(5, 0, -1):
                radius = earth_radius_px * (i / 5)
                alpha = 0.3 + 0.7 * (i / 5)
                color_int = int(30 + (60 - 30) * (i / 5))
                color = f"#{color_int:02x}{color_int + 20:02x}{color_int + 40:02x}"
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    fill=color, outline="", width=0
                )
            
            # Main Earth circle
            self.canvas.create_oval(
                center_x - earth_radius_px, center_y - earth_radius_px,
                center_x + earth_radius_px, center_y + earth_radius_px,
                fill="#1e3a8a", outline="#3b82f6", width=2
            )
            
            # Add some detail (continents suggestion)
            for i in range(3):
                offset_x = (i - 1) * 20
                offset_y = (i % 2) * 15 - 7
                self.canvas.create_oval(
                    center_x + offset_x - 10, center_y + offset_y - 10,
                    center_x + offset_x + 10, center_y + offset_y + 10,
                    fill="#2563eb", outline="", width=0
                )
        except Exception as e:
            # Handle any other errors by using fallback
            for i in range(5, 0, -1):
                radius = earth_radius_px * (i / 5)
                alpha = 0.3 + 0.7 * (i / 5)
                color_int = int(30 + (60 - 30) * (i / 5))
                color = f"#{color_int:02x}{color_int + 20:02x}{color_int + 40:02x}"
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    fill=color, outline="", width=0
                )
            
            # Main Earth circle
            self.canvas.create_oval(
                center_x - earth_radius_px, center_y - earth_radius_px,
                center_x + earth_radius_px, center_y + earth_radius_px,
                fill="#1e3a8a", outline="#3b82f6", width=2
            )
            
            # Add some detail (continents suggestion)
            for i in range(3):
                offset_x = (i - 1) * 20
                offset_y = (i % 2) * 15 - 7
                self.canvas.create_oval(
                    center_x + offset_x - 10, center_y + offset_y - 10,
                    center_x + offset_x + 10, center_y + offset_y + 10,
                    fill="#2563eb", outline="", width=0
                )
    
    def draw_reference_orbits(self):
        """Draw reference orbital shells"""
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        
        # Common orbital altitudes (in km)
        reference_orbits = [
            (400, "#4a5568", "ISS/Starlink"),
            (800, "#4a5568", "SLEO"),
            (2000, "#4a5568", "MEO"),
            (35786, "#4a5568", "GEO")
        ]
        
        # Scale factor: pixels per km
        scale = min(self.canvas.winfo_width(), self.canvas.winfo_height()) / (45000 * 2)
        
        for alt_km, color, label in reference_orbits:
            radius_px = (R_EARTH + alt_km * 1000) * scale / 1000  # Simplified scaling
            if radius_px > 100:  # Only draw if visible
                self.canvas.create_oval(
                    center_x - radius_px, center_y - radius_px,
                    center_x + radius_px, center_y + radius_px,
                    outline=color, width=1, dash=(3, 3)
                )
    
    def draw_user_orbit(self):
        """Draw the user's selected orbit"""
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        
        # Calculate orbit points with more detail for smoother drawing
        orbit_points = calculate_orbit_points(
            self.altitude, self.inclination, self.eccentricity, 720 # Increased from 360 to 720 for smoother orbit
        )
        
        # Scale factor
        max_radius = max([math.sqrt(x**2 + y**2) for x, y in orbit_points])
        scale = min(self.canvas.winfo_width(), self.canvas.winfo_height()) / (max_radius * 2.5)
        
        # Convert to screen coordinates
        screen_points = []
        for x, y in orbit_points:
            screen_x = center_x + x * scale
            screen_y = center_y - y * scale  # Flip Y axis
            screen_points.append((screen_x, screen_y))
        
        # Draw main orbit path
        if len(screen_points) > 1:
            for i in range(len(screen_points)):
                x1, y1 = screen_points[i]
                x2, y2 = screen_points[(i + 1) % len(screen_points)]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#00ff88", width=2, smooth=True  # Brighter green for main orbit
                )
        
        # Draw multiple consecutive satellites in the same orbit band
        num_satellites = 5  # Number of consecutive satellites in the orbit
        for sat_idx in range(num_satellites):
            # Calculate phase offset for consecutive satellites
            phase_offset = (sat_idx * 2 * math.pi) / num_satellites  # Distribute satellites evenly around the orbit
            offset_angle = (self.animation_angle + math.degrees(phase_offset)) % 360
            
            # Calculate the satellite position using the offset angle
            angle_idx = int(offset_angle) % len(screen_points)
            next_idx = (angle_idx + 1) % len(screen_points)
            
            # Interpolate for smoother movement between points
            fraction = offset_angle - int(offset_angle)
            sat_x = screen_points[angle_idx][0] + fraction * (screen_points[next_idx][0] - screen_points[angle_idx][0])
            sat_y = screen_points[angle_idx][1] + fraction * (screen_points[next_idx][1] - screen_points[angle_idx][1])
            
            # Draw satellite marker with different colors to distinguish them
            colors = ["#ffffff", "#ff9999", "#99ff9", "#9999ff", "#ffff99"]
            main_color = colors[sat_idx % len(colors)]
            outline_color = "#00ff88" if sat_idx == 0 else "#cccccc"  # Highlight the first satellite
            
            self.canvas.create_oval(
                sat_x - 6, sat_y - 6,
                sat_x + 6, sat_y + 6,
                fill=main_color, outline=outline_color, width=2
            )
            self.canvas.create_oval(
                sat_x - 3, sat_y - 3,
                sat_x + 3, sat_y + 3,
                fill=outline_color if sat_idx == 0 else "#99999", outline="", width=0
            )
    
    def draw_visualization(self):
        """Draw the complete visualization"""
        self.canvas.delete("all")
        
        # Draw reference orbits
        self.draw_reference_orbits()
        
        # Draw Earth
        self.draw_earth()
        
        # Draw user's orbit
        self.draw_user_orbit()
        
        # Draw labels
        self.draw_labels()
    
    def draw_labels(self):
        """Draw orbital labels"""
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        
        # Label positions
        labels = [
            (center_x, center_y - 100, "SLEO", "#888888"),
            (center_x, center_y - 120, "Starlink", "#888888")
        ]
        
        for x, y, text, color in labels:
            self.canvas.create_text(
                x, y, text=text,
                fill=color, font=("Arial", 10),
                anchor='center'
            )
    
    def start_animation(self):
        """Start the animation loop"""
        def animate():
            while self.animation_running:
                if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                    self.animation_angle += 1.0  # Increase speed for continuous movement
                    if self.animation_angle >= 360:
                        self.animation_angle = 0
                    self.draw_visualization()
                    time.sleep(0.01)  # Reduced sleep for smoother and faster animation
                else:
                    break
        
        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def export_orbit_data(self):
        """Export orbit data for use in web interfaces"""
        orbit_points = calculate_orbit_points(
            self.altitude, self.inclination, self.eccentricity, 720
        )
        
        # Calculate orbital information
        velocity = calculate_orbital_velocity(self.altitude, self.eccentricity)
        period = calculate_orbital_period(self.altitude, self.eccentricity)
        
        return {
            "orbit_points": orbit_points,
            "velocity": velocity,
            "period": period,
            "perigee": (R_EARTH + self.altitude * 1000 * (1 - self.eccentricity))/1000,
            "apogee": (R_EARTH + self.altitude * 1000 * (1 + self.eccentricity))/1000,
            "altitude": self.altitude,
            "inclination": self.inclination,
            "eccentricity": self.eccentricity
        }
    
    def on_closing(self):
        """Handle window closing"""
        self.animation_running = False
        self.window.destroy()


def main():
    root = tk.Tk()
    app = OrbitVisualizer(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

