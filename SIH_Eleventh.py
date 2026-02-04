import tkinter as tk
from tkinter import ttk
import numpy as np
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D


class OrbitSimulation:
    def __init__(self, root):
        self.root = root
        self.root.title("Realistic Earth Orbit – Satellite & Space Debris Simulation")
        self.root.geometry("1400x800")

        # --------------------------
        # LEFT FRAME (Visualization)
        # --------------------------
        self.left_frame = tk.Frame(root, bg="black")
        self.left_frame.pack(side="left", fill="both", expand=True)

        # Matplotlib setup
        self.fig = Figure(figsize=(7, 7), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor("black")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Earth model
        self.R_earth = 6371  # km (scaled down later)
        self.scale = 1500
        self.generate_earth()

        # Satellite
        self.sat_orbit_radius = self.R_earth + 500
        self.satellite, = self.ax.plot([], [], [], 'o', color='white', markersize=8)

        # Debris
        self.debris_count = 40
        self.debris_positions = self.generate_debris()
        self.debris_plots = []

        # --------------------------
        # RIGHT FRAME (Info Panel)
        # --------------------------
        self.right_frame = tk.Frame(root, width=400, bg="#111111")
        self.right_frame.pack(side="right", fill="y")

        title = tk.Label(self.right_frame, text="MISSION STATUS PANEL",
                         fg="cyan", bg="#111111", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        self.info_text = tk.Text(self.right_frame, width=40, height=35, bg="black", fg="white",
                                 font=("Consolas", 12))
        self.info_text.pack(padx=10, pady=10)

        # Start animation
        self.angle = 0
        self.animate()

    # ----------------------
    # EARTH RENDERING
    # ----------------------
    def generate_earth(self):
        u = np.linspace(0, 2*np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = (self.R_earth/self.scale) * np.outer(np.cos(u), np.sin(v))
        y = (self.R_earth/self.scale) * np.outer(np.sin(u), np.sin(v))
        z = (self.R_earth/self.scale) * np.outer(np.ones(np.size(u)), np.cos(v))

        self.ax.plot_surface(x, y, z, color='blue', alpha=0.7, linewidth=0)

        self.ax.set_xlim([-10, 10])
        self.ax.set_ylim([-10, 10])
        self.ax.set_zlim([-10, 10])
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_zticks([])

    # ----------------------
    # DEBRIS GENERATION
    # ----------------------
    def generate_debris(self):
        debris_list = []
        for _ in range(self.debris_count):
            r = self.R_earth + random.randint(300, 1500)
            theta = random.random() * 2 * np.pi
            phi = random.random() * np.pi
            debris_list.append([r, theta, phi])
        return debris_list

    # ----------------------
    # ANIMATION LOOP
    # ----------------------
    def animate(self):
        self.ax.cla()
        self.generate_earth()

        # Update satellite
        sat_r = self.sat_orbit_radius
        x = (sat_r/self.scale) * np.cos(self.angle)
        y = (sat_r/self.scale) * np.sin(self.angle)
        z = 0

        self.ax.scatter(x, y, z, color='white', s=40)

        # Update debris
        min_dist = float("inf")
        danger_debris = None

        for i in range(len(self.debris_positions)):
            r, theta, phi = self.debris_positions[i]
            theta += 0.01  # debris rotation
            self.debris_positions[i][1] = theta

            dx = (r/self.scale) * np.cos(theta) * np.sin(phi)
            dy = (r/self.scale) * np.sin(theta) * np.sin(phi)
            dz = (r/self.scale) * np.cos(phi)

            self.ax.scatter(dx, dy, dz, color='red', s=10)

            # Distance to satellite
            dist = np.sqrt((dx - x)**2 + (dy - y)**2 + (dz - z)**2)
            if dist < min_dist:
                min_dist = dist
                danger_debris = (dx, dy, dz)

        # --------------------------
        # INFO PANEL UPDATE
        # --------------------------
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, f"Satellite Orbit Radius: {self.sat_orbit_radius} km\n")
        self.info_text.insert(tk.END, f"Debris Count: {self.debris_count}\n\n")

        self.info_text.insert(tk.END, "Nearest Debris Distance:\n")
        self.info_text.insert(tk.END, f"  → {min_dist*1000:.2f} meters\n\n")

        if min_dist < 0.02:
            self.info_text.insert(tk.END, "⚠ COLLISION WARNING ⚠\n", "warning")
            self.info_text.tag_config("warning", foreground="red")
        else:
            self.info_text.insert(tk.END, "Safe – No immediate threat.\n", "safe")
            self.info_text.tag_config("safe", foreground="lime")

        # Update angle
        self.angle += 0.01

        # Render
        self.canvas.draw()

        # Loop
        self.root.after(30, self.animate)


# -------------------------
# RUN APPLICATION
# -------------------------
root = tk.Tk()
app = OrbitSimulation(root)
root.mainloop()
