import numpy as np
import tkinter as tk
from tkinter import font
import math
import threading
import time
import os
from PIL import Image, ImageTk, ImageDraw
import cv2  # Added for video playback

# ======================================
# ORBIT PHYSICS — REALISTIC
# ======================================
G = 6.67430e-11
M_EARTH = 5.972e24
R_EARTH = 6371000
MU = G * M_EARTH

def orbital_step(pos, vel, dt):
    x, y, z = pos
    vx, vy, vz = vel
    r = np.sqrt(x*x + y*y + z*z)

    ax = -(MU * x) / r**3
    ay = -(MU * y) / r**3
    az = -(MU * z) / r**3

    # Euler integration
    vx += ax * dt
    vy += ay * dt
    vz += az * dt

    x += vx * dt
    y += vy * dt
    z += vz * dt

    return np.array([x, y, z]), np.array([vx, vy, vz])


class SpaceSim:
    def __init__(self, window):
        self.window = window
        self.window.title("Real-Time Space Debris Trajectory Viewer")
        self.window.geometry("1200x800")

        # Create a frame for the OpenGL canvas and info panel
        self.main_frame = tk.Frame(window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Info panel
        self.info_frame = tk.Frame(self.main_frame, width=300, bg="black")
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.info_frame.pack_propagate(False)

        # Title for info panel
        title_label = tk.Label(
            self.info_frame, 
            text="TELEMETRY DATA", 
            font=("Consolas", 14, "bold"), 
            bg="black", 
            fg="#00ff00",
            pady=10
        )
        title_label.pack()

        self.info = tk.Label(
            self.info_frame, 
            text="", 
            font=("Consolas", 11), 
            justify="left", 
            bg="black", 
            fg="white",
            anchor="nw"
        )
        self.info.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Canvas for rendering
        self.canvas = tk.Canvas(self.main_frame, width=900, height=700, bg='#000011')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas dimensions
        self.canvas_width = 900
        self.canvas_height = 700
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2
        
        # Add star background
        self.draw_star_background()

        # Scale factor for visualization (meters to pixels)
        # Show about 3x Earth radius
        self.scale = min(self.canvas_width, self.canvas_height) / (3 * R_EARTH)

        # Initial orbit (400 km altitude)
        altitude = 400000  # 400 km
        r0 = R_EARTH + altitude

        # Initial position and velocity for circular orbit
        self.pos = np.array([r0, 0, 0])
        self.vel = np.array([0, math.sqrt(MU / r0), 1200])

        # Trajectory history for drawing the path
        self.trajectory = []
        self.max_trajectory_points = 500

        # Earth visualization - now using video
        self.earth_radius_pixels = R_EARTH * self.scale
        self.earth_video_cap = cv2.VideoCapture('earth_globe.mp4')  # Path to downloaded video from https://pixabay.com/videos/earth-globe-country-africa-asia-1393/
        self.earth_video_frame = None
        self.earth_video_tk = None

        # Animation control
        self.running = True
        self.paused = False
        self.time_scale = 1.0  # Time acceleration factor
        
        # Zoom control
        self.zoom_factor = 1.0

        # Earth rotation variables (now handled by video)
        self.earth_rotation_angle = 0
        self.earth_rotation_speed = 0.005  # radians per frame - slower for more realistic rotation

        # Create space debris
        self.space_debris = self.create_space_debris()

        # Control buttons
        self.create_controls()

        # Start rendering thread
        threading.Thread(target=self.run, daemon=True).start()

        # Bind canvas resize
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Bind mouse wheel for zooming
        self.canvas.bind('<MouseWheel>', self.zoom_canvas)  # Windows
        self.canvas.bind('<Button-4>', self.zoom_canvas)    # Linux
        self.canvas.bind('<Button-5>', self.zoom_canvas)    # Linux

    def create_space_debris(self):
        """Create a list of space debris with random positions and orbits"""
        debris_list = []
        for i in range(5):
            # Random orbital parameters for each debris
            altitude = 300000 + i * 10000  # Different altitudes
            r0 = R_EARTH + altitude
            angle = i * (2 * math.pi / 5)  # Evenly spaced angles
            
            # Position in orbit
            pos = np.array([r0 * math.cos(angle), r0 * math.sin(angle), 0])
            
            # Velocity for circular orbit (perpendicular to position)
            vel = np.array([-math.sqrt(MU / r0) * math.sin(angle), math.sqrt(MU / r0) * math.cos(angle), 0])
            
            # Random debris characteristics - now using the same color as main debris
            debris = {
                'pos': pos.copy(),
                'vel': vel.copy(),
                'size': np.random.randint(2, 6),
                'color': "#ff9900",  # Same color as main debris
                'orbit_radius': r0,
                'angle': angle,
                'angular_velocity': math.sqrt(MU / (r0 ** 3))  # Angular velocity for circular orbit
            }
            debris_list.append(debris)
        return debris_list

    def draw_star_background(self):
        """Draw a star background on the canvas"""
        # Draw random stars
        for _ in range(200):
            x = np.random.randint(0, self.canvas_width)
            y = np.random.randint(0, self.canvas_height)
            size = np.random.uniform(0.5, 2)
            brightness = np.random.randint(10, 255)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")

    def create_controls(self):
        """Create control buttons in the info panel"""
        controls_frame = tk.Frame(self.info_frame, bg="black")
        controls_frame.pack(pady=10)

        self.pause_btn = tk.Button(
            controls_frame,
            text="Pause",
            command=self.toggle_pause,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            width=12
        )
        self.pause_btn.pack(pady=5)

        self.reset_btn = tk.Button(
            controls_frame,
            text="Reset Orbit",
            command=self.reset_orbit,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            width=12
        )
        self.reset_btn.pack(pady=5)

        # Zoom controls
        zoom_frame = tk.Frame(controls_frame, bg="black")
        zoom_frame.pack(pady=5)
        
        tk.Label(
            zoom_frame,
            text="Zoom:",
            font=("Consolas", 9),
            bg="black",
            fg="#888888"
        ).pack()
        
        zoom_btn_frame = tk.Frame(zoom_frame, bg="black")
        zoom_btn_frame.pack()
        
        zoom_in_btn = tk.Button(
            zoom_btn_frame,
            text="+",
            command=lambda: self.set_zoom(1.2),
            bg="#222222",
            fg="white",
            font=("Consolas", 8),
            width=3
        )
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_out_btn = tk.Button(
            zoom_btn_frame,
            text="-",
            command=lambda: self.set_zoom(0.8),
            bg="#222222",
            fg="white",
            font=("Consolas", 8),
            width=3
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        reset_zoom_btn = tk.Button(
            zoom_btn_frame,
            text="R",
            command=lambda: self.set_zoom(1.0),
            bg="#222222",
            fg="white",
            font=("Consolas", 8),
            width=3
        )
        reset_zoom_btn.pack(side=tk.LEFT, padx=2)

        # Time scale label
        scale_label = tk.Label(
            controls_frame,
            text="Time Scale:",
            font=("Consolas", 9),
            bg="black",
            fg="#888888"
        )
        scale_label.pack(pady=(10, 5))

        # Time scale buttons
        scale_frame = tk.Frame(controls_frame, bg="black")
        scale_frame.pack()

        for scale in [0.5, 1.0, 2.0, 5.0]:
            btn = tk.Button(
                scale_frame,
                text=f"{scale}x",
                command=lambda s=scale: self.set_time_scale(s),
                bg="#222222",
                fg="white",
                font=("Consolas", 8),
                width=4
            )
            btn.pack(side=tk.LEFT, padx=2)

    def draw_earth(self):
        """Draw Earth using video frames from https://pixabay.com/videos/earth-globe-country-africa-asia-1393/"""
        # Apply zoom factor to earth radius
        earth_radius_pixels = R_EARTH * self.scale * self.zoom_factor
        
        # Read next frame from video
        ret, frame = self.earth_video_cap.read()
        if ret:
            # Resize frame to fit Earth radius
            frame = cv2.resize(frame, (int(earth_radius_pixels * 2), int(earth_radius_pixels * 2)))
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            self.earth_video_frame = Image.fromarray(frame)
            self.earth_video_tk = ImageTk.PhotoImage(self.earth_video_frame)
        else:
            # If video ends, loop it
            self.earth_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.earth_video_cap.read()
            if ret:
                frame = cv2.resize(frame, (int(earth_radius_pixels * 2), int(earth_radius_pixels * 2)))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.earth_video_frame = Image.fromarray(frame)
                self.earth_video_tk = ImageTk.PhotoImage(self.earth_video_frame)
        
        # Calculate position to center the Earth
        x = self.center_x - earth_radius_pixels
        y = self.center_y - earth_radius_pixels

        # Draw the Earth video frame on the canvas
        self.canvas.create_image(self.center_x, self.center_y, image=self.earth_video_tk)
        
        # Draw a subtle outline for the Earth
        self.canvas.create_oval(
            x, y, x + earth_radius_pixels * 2, y + earth_radius_pixels * 2,
            outline="#2a6db0",
            width=2
        )
         
        # Add grid lines for reference
        # Horizontal line
        self.canvas.create_line(
            0, self.center_y,
            self.canvas_width, self.center_y,
            fill="#333333",
            width=1,
            dash=(5, 5)
        )
        # Vertical line
        self.canvas.create_line(
            self.center_x, 0,
            self.center_x, self.canvas_height,
            fill="#333333",
            width=1,
            dash=(5, 5)
        )
         
        # Add longitude and latitude lines
        for i in range(1, 4):
            angle = i * math.pi / 4
            # Longitude lines
            self.canvas.create_arc(
                x, y, x + earth_radius_pixels * 2, y + earth_radius_pixels * 2,
                start=math.degrees(angle),
                extent=0,
                style=tk.ARC,
                outline="#333355",
                width=1,
                dash=(3, 3)
            )
             
            # Latitude lines
            lat_offset = earth_radius_pixels * math.sin(angle)
            self.canvas.create_oval(
                x, self.center_y - lat_offset, x + earth_radius_pixels * 2, self.center_y + lat_offset,
                outline="#333355",
                width=1,
                dash=(3, 3)
            )

    def draw_space_debris(self):
        """Draw additional space debris for visual effect, now with orbit lines"""
        for debris in self.space_debris:
            # Draw orbit line
            orbit_points = []
            for angle in np.linspace(0, 2 * np.pi, 50):
                x = debris['orbit_radius'] * np.cos(angle)
                y = debris['orbit_radius'] * np.sin(angle)
                z = 0
                screen_x, screen_y = self.world_to_screen([x, y, z])
                orbit_points.append((screen_x, screen_y))
            for i in range(len(orbit_points) - 1):
                self.canvas.create_line(
                    orbit_points[i][0], orbit_points[i][1],
                    orbit_points[i+1][0], orbit_points[i+1][1],
                    fill="white", width=1, dash=(5, 5)
                )
            
            # Draw debris
            screen_x, screen_y = self.world_to_screen(debris['pos'])
            size = debris['size']
            
            # Draw debris as a small circle
            self.canvas.create_oval(
                screen_x - size, screen_y - size,
                screen_x + size, screen_y + size,
                fill=debris['color'],
                outline="#ffffff",
                width=1
            )
            
            # Add a glow effect
            glow_size = size * 2
            self.canvas.create_oval(
                screen_x - glow_size, screen_y - glow_size,
                screen_x + glow_size, screen_y + glow_size,
                fill="", outline=debris['color'], width=1, dash=(2, 2)
            )

    def draw_trajectory(self):
        """Draw the trajectory path with improved visualization"""
        if len(self.trajectory) < 2:
            return

        # Draw trajectory with fading effect
        points = []
        for i, pos in enumerate(self.trajectory):
            screen_x, screen_y = self.world_to_screen(pos)
            points.append((screen_x, screen_y))

        # Draw trajectory line segments with varying opacity
        for i in range(len(points) - 1):
            # Calculate opacity based on recency (newer = brighter)
            opacity = int(255 * (i / len(points)))
            # Use a more vibrant color gradient
            color = f"#{min(255, opacity//2):02x}{min(255, opacity):02x}{min(255, opacity//3):02x}"
            
            self.canvas.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill=color,
                width=2
            )
            
        # Draw predicted orbit path (if possible)
        self.draw_predicted_orbit()

    def draw_debris(self):
        """Draw the main debris/spacecraft with enhanced visualization"""
        screen_x, screen_y = self.world_to_screen(self.pos)

        # Draw debris as a more detailed object
        size = 8
        # Draw a spacecraft-like shape instead of just a circle
        self.canvas.create_oval(
            screen_x - size, screen_y - size,
            screen_x + size, screen_y + size,
            fill="#ff9900",
            outline="#ffcc00",
            width=2
        )
        
        # Add a glow effect
        glow_size = size * 2
        self.canvas.create_oval(
            screen_x - glow_size, screen_y - glow_size,
            screen_x + glow_size, screen_y + glow_size,
            fill="", outline="#ff6600", width=1, dash=(2, 2)
        )

        # Draw velocity vector
        vel_scale = 10000  # Scale for visibility
        vx, vy, vz = self.vel
        # Apply zoom factor to velocity vector
        current_scale = self.scale * self.zoom_factor
        end_x = screen_x + vx * current_scale * (vel_scale / np.linalg.norm(self.vel))
        end_y = screen_y - vy * current_scale * (vel_scale / np.linalg.norm(self.vel))
        
        self.canvas.create_line(
            screen_x, screen_y,
            end_x, end_y,
            fill="#00ff00",
            width=2,
            arrow=tk.LAST,
            arrowshape=(10, 12, 3)
        )
        
        # Draw direction indicator
        self.canvas.create_oval(
            end_x - 3, end_y - 3,
            end_x + 3, end_y + 3,
            fill="#00ff00", outline="#ffffff", width=1
        )

    def draw_ui(self):
        """Draw all UI elements"""
        self.canvas.delete("all")
        
        # Draw Earth
        self.draw_earth()
        
        # Draw space debris
        self.draw_space_debris()
        
        # Draw trajectory
        self.draw_trajectory()
        
        # Draw main debris
        self.draw_debris()

        # Draw info overlay
        self.draw_info_overlay()

    def draw_predicted_orbit(self):
        """Draw the predicted orbital path"""
        if len(self.trajectory) < 2:
            return
            
        # Calculate orbital elements to predict the full orbit
        r_vec = self.pos
        v_vec = self.vel
        r = np.linalg.norm(r_vec)
        v = np.linalg.norm(v_vec)
        
        # Calculate specific orbital energy
        energy = v*v/2 - MU/r
        
        # Skip if not in a stable orbit (hyperbolic trajectory)
        if energy >= 0:
            return
            
        # Calculate angular momentum
        h_vec = np.cross(r_vec, v_vec)
        h = np.linalg.norm(h_vec)
        
        # Calculate eccentricity vector
        e_vec = np.cross(v_vec, h_vec) / MU - r_vec / r
        eccentricity = np.linalg.norm(e_vec)
        
        # Calculate semi-major axis
        a = -MU / (2 * energy)
        
        # Draw the full predicted
        def draw_predicted_orbit(self):
            """Draw the predicted orbital path"""
            if len(self.trajectory) < 2:
                return
            
        # Calculate orbital elements to predict the full orbit
        r_vec = self.pos
        v_vec = self.vel
        r = np.linalg.norm(r_vec)
        v = np.linalg.norm(v_vec)
        
        # Calculate specific orbital energy
        energy = v*v/2 - MU/r
        
        # Skip if not in a stable orbit (hyperbolic trajectory)
        if energy >= 0:
            return
            
        # Calculate angular momentum
        h_vec = np.cross(r_vec, v_vec)
        h = np.linalg.norm(h_vec)
        
        # Calculate eccentricity vector
        e_vec = np.cross(v_vec, h_vec) / MU - r_vec / r
        eccentricity = np.linalg.norm(e_vec)
        
        # Calculate semi-major axis
        a = -MU / (2 * energy)
        
        # Draw the full predicted orbit
        if eccentricity < 1:  # Elliptical orbit
            # Draw orbit as a series of points
            orbit_points = []
            for true_anomaly in np.linspace(0, 2*np.pi, 100):
                # Calculate radius at this anomaly
                radius = a * (1 - eccentricity*eccentricity) / (1 + eccentricity * np.cos(true_anomaly))
                
                # Calculate position in orbital plane
                x_orb = radius * np.cos(true_anomaly)
                y_orb = radius * np.sin(true_anomaly)
                
                # Rotate to actual orbital plane (simplified)
                pos_orb = np.array([x_orb, y_orb, 0])
                screen_x, screen_y = self.world_to_screen(pos_orb)
                orbit_points.append((screen_x, screen_y))
            
            # Draw the predicted orbit path with dashed line
            if len(orbit_points) > 1:
                for i in range(len(orbit_points) - 1):
                    self.canvas.create_line(
                        orbit_points[i][0], orbit_points[i][1],
                        orbit_points[i+1][0], orbit_points[i+1][1],
                        fill="#5555ff",
                        width=1,
                        dash=(5, 5)
                    )

    def draw_info_overlay(self):
        """Draw overlay information on canvas"""
        r = np.linalg.norm(self.pos)
        altitude = r - R_EARTH
        
        # Draw altitude indicator
        info_text = f"Altitude: {altitude/1000:.1f} km | Zoom: {self.zoom_factor:.1f}x"
        self.canvas.create_text(
            10, 10,
            text=info_text,
            fill="#00ff00",
            font=("Consolas", 12, "bold"),
            anchor="nw"
        )

    def update_physics(self):
        """Update physics simulation"""
        if not self.paused:
            dt = 1.0 * self.time_scale  # Time step in seconds
            self.pos, self.vel = orbital_step(self.pos, self.vel, dt)

            # Add current position to trajectory
            self.trajectory.append(self.pos.copy())
            if len(self.trajectory) > self.max_trajectory_points:
                self.trajectory.pop(0)

            # Update space debris positions
            for debris in self.space_debris:
                # Update angle based on angular velocity
                debris['angle'] += debris['angular_velocity'] * dt * self.time_scale
                # Calculate new position based on updated angle - ensuring it follows proper orbit
                debris['pos'][0] = debris['orbit_radius'] * math.cos(debris['angle'])
                debris['pos'][1] = debris['orbit_radius'] * math.sin(debris['angle'])
                debris['pos'][2] = 0  # Keep debris on the same plane as the main debris

    def update_ui(self):
        """Update UI elements"""
        r = np.linalg.norm(self.pos)
        altitude = r - R_EARTH
        speed = np.linalg.norm(self.vel)
        
        # Calculate orbital period (approximate)
        semi_major_axis = r
        if semi_major_axis > 0:
            period = 2 * math.pi * math.sqrt(semi_major_axis**3 / MU)
        else:
            period = 0

        # Calculate position components
        x, y, z = self.pos
        vx, vy, vz = self.vel

        # Calculate orbital elements
        h_vec = np.cross(self.pos, self.vel)
        h = np.linalg.norm(h_vec)
        
        # Eccentricity (simplified)
        e_vec = np.cross(self.vel, h_vec) / MU - self.pos / r
        eccentricity = np.linalg.norm(e_vec)

        text = (
            f"--- REAL-TIME TELEMETRY ---\n\n"
            f"Position (km):\n"
            f"  X: {x/1000:>10.2f}\n"
            f"  Y: {y/1000:>10.2f}\n"
            f"  Z: {z/1000:>10.2f}\n\n"
            f"Velocity (m/s):\n"
            f"  Vx: {vx:>10.2f}\n"
            f"  Vy: {vy:>10.2f}\n"
            f"  Vz: {vz:>10.2f}\n\n"
            f"Orbital Parameters:\n"
            f"  Altitude: {altitude/1000:>8.2f} km\n"
            f" Speed: {speed:>10.2f} m/s\n"
            f"  Distance: {r/1000:>8.2f} km\n"
            f" Period: {period/60:>8.2f} min\n"
            f"  Eccentricity: {eccentricity:>6.4f}\n\n"
            f"Simulation:\n"
            f"  Time Scale: {self.time_scale:>6.1f}x\n"
            f"  Status: {'PAUSED' if self.paused else 'RUNNING'}\n"
            f"  Trail Points: {len(self.trajectory)}\n"
        )

        # Update the info label in the main thread
        self.window.after(0, lambda: self.info.config(text=text))
        
        # Update canvas drawing
        self.window.after(0, self.draw_ui)

    def world_to_screen(self, pos):
        """Convert world coordinates to screen coordinates"""
        x, y, z = pos
        screen_x = self.center_x + x * self.scale * self.zoom_factor
        screen_y = self.center_y - y * self.scale * self.zoom_factor  # Flip Y axis
        return screen_x, screen_y

    def run(self):
        """Main simulation loop"""
        while self.running:
            self.update_physics()
            self.update_ui()
            time.sleep(0.016)  # ~60 FPS

    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")

    def reset_orbit(self):
        """Reset the orbit to initial conditions"""
        altitude = 400000  # 400 km
        r0 = R_EARTH + altitude
        self.pos = np.array([r0, 0, 0])
        self.vel = np.array([0, math.sqrt(MU / r0), 1200])
        self.trajectory = []

    def set_zoom(self, factor):
        """Set zoom factor"""
        self.zoom_factor *= factor
        # Limit zoom to reasonable values
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))

    def set_time_scale(self, scale):
        """Set time scale factor"""
        self.time_scale = scale

    def on_canvas_resize(self, event):
        """Handle canvas resize"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2

    def zoom_canvas(self, event):
        """Handle mouse wheel zoom"""
        # Respond to mouse wheel events
        if event.num == 4 or event.delta > 0:
            # Zoom in
            self.set_zoom(1.1)
        elif event.num == 5 or event.delta < 0:
            # Zoom out
            self.set_zoom(0.9)


# ======================================
# START APP
# ======================================
def main():
    root = tk.Tk()
    app = SpaceSim(root)
    
    def on_closing():
        app.running = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
