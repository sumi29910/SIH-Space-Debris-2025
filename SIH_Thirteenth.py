import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ============================================================
#      REAL-TIME SPACE DEBRIS MONITORING DASHBOARD
# ============================================================

CSV_FILE = "simulation_log.csv"      # The simulation continuously updates this file
MAX_ROWS = 50                        # Only read the last 50 rows
UPDATE_INTERVAL = 100                # 100 ms refresh

# ------------------------------------------------------------
# Styling (Dark Theme Dashboard)
# ------------------------------------------------------------
plt.style.use("dark_background")

fig = plt.figure(figsize=(10, 12))
fig.patch.set_facecolor("black")

# Subplots (Vertical layout)
ax1 = fig.add_subplot(3, 1, 1)     # Line chart: Debris status
ax2 = fig.add_subplot(3, 1, 2)     # Big number: Total Debris
ax3 = fig.add_subplot(3, 1, 3)     # Log window: Latest events

# ------------------------------------------------------------
# Subplot 1 — Debris Status Over Time
# ------------------------------------------------------------
ax1.set_title("Debris Status Over Time", color="white", fontsize=14)
ax1.set_xlabel("Frame", color="gray")
ax1.set_ylabel("Count", color="gray")

line_killed, = ax1.plot([], [], color="lime", label="Destroyed (Killed)")
line_undetected, = ax1.plot([], [], color="yellow", label="Undetected")
line_targeted, = ax1.plot([], [], color="red", label="Targeted")

ax1.legend(facecolor="black", edgecolor="gray", labelcolor="white")
ax1.grid(True, alpha=0.2)

# ------------------------------------------------------------
# Subplot 2 — Total Debris Display (Digital Style)
# ------------------------------------------------------------
ax2.set_title("Total Debris Created", color="white", fontsize=14)
ax2.set_xticks([])
ax2.set_yticks([])
ax2.set_facecolor("black")

digital_text = ax2.text(0.5, 0.5, "0",
                        color="cyan",
                        fontsize=48,
                        ha="center", va="center",
                        fontweight="bold")

# ------------------------------------------------------------
# Subplot 3 — Event Log Window
# ------------------------------------------------------------
ax3.set_title("Recent Event Log", color="white", fontsize=14)
ax3.set_xticks([])
ax3.set_yticks([])
ax3.set_facecolor("black")

log_text = ax3.text(0.02, 0.95, "",
                    fontsize=12,
                    color="white",
                    va="top",
                    family="monospace")


# ============================================================
#                      UPDATE FUNCTION
# ============================================================
def update(frame):
    try:
        # Read only the last 50 rows for efficiency
        df = pd.read_csv(CSV_FILE)

        if len(df) > MAX_ROWS:
            df = df.tail(MAX_ROWS)

        # Ensure required columns exist
        required = [
            "frame", "destroyed_debris_count", "undetected_count",
            "targeted_count", "total_debris_created", "events"
        ]
        for col in required:
            if col not in df.columns:
                print(f"ERROR: Column '{col}' not found in CSV.")
                return

        # ------------------------------------------------------------
        # Update Plot 1 (Line Chart)
        # ------------------------------------------------------------
        line_killed.set_data(df["frame"], df["destroyed_debris_count"])
        line_undetected.set_data(df["frame"], df["undetected_count"])
        line_targeted.set_data(df["frame"], df["targeted_count"])

        ax1.set_xlim(df["frame"].min(), df["frame"].max())
        max_y = max(df["destroyed_debris_count"].max(),
                    df["undetected_count"].max(),
                    df["targeted_count"].max()) + 2
        ax1.set_ylim(0, max_y)

        # ------------------------------------------------------------
        # Update Plot 2 (Digital Big Number)
        # ------------------------------------------------------------
        latest_total = df["total_debris_created"].iloc[-1]
        digital_text.set_text(str(latest_total))

        # ------------------------------------------------------------
        # Update Plot 3 (Event Log)
        # ------------------------------------------------------------
        raw_events = df["events"].iloc[-1]

        # Assume events are semicolon-separated
        events_list = raw_events.split(";")

        # Keep only last 5 events
        last_5_events = events_list[-5:]

        formatted = "\n".join(f"- {e.strip()}" for e in last_5_events if e.strip())
        log_text.set_text(formatted)

    except FileNotFoundError:
        digital_text.set_text("Missing CSV")
    except Exception as e:
        digital_text.set_text(f"Error: {e}")


# ============================================================
#                        RUN DASHBOARD
# ============================================================
ani = FuncAnimation(fig, update,
                    interval=UPDATE_INTERVAL,
                    blit=False)

plt.tight_layout()
plt.show()
