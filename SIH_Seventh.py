from vpython import *
import numpy as np
import csv
import math
import time

# ---------- CONFIG / PHYSICAL CONSTANTS ----------
g0 = 9.80665                 # m/s^2
mu = 3.986004418e14          # Earth gravitational parameter (m^3/s^2)
Re = 6371000.0               # Earth radius (m)
rho0 = 1.225                 # sea-level air density (kg/m^3)
H_atm = 8500.0               # scale height (m)

# ---------- VISUAL SCENE ----------
scene = canvas(title='LVM3-like Ascent & Payload Insertion',
               width=1200, height=700, background=color.black,
               center=vector(0,15000,0))

ground = box(pos=vector(0,-0.5,0), size=vector(10000,1,10000), color=vector(0.1,0.5,0.1))
earth_patch = sphere(pos=vector(0, -Re, 0), radius=Re, color=color.cyan, opacity=0.05, shininess=0)

# ---------- ROCKET GEOMETRY (scaled to meters) ----------
rocket_length = 30.0     # m
rocket_radius = 2.5      # m

rocket = cylinder(pos=vector(0,0,0), axis=vector(0,rocket_length,0),
                  radius=rocket_radius, color=color.white)
fairing = cone(pos=rocket.pos + rocket.axis, axis=vector(0,8,0), radius=3.0, color=color.gray(0.9))

# boosters (attached initially)
booster_L = cylinder(pos=rocket.pos + vector(-4,0,0), axis=vector(0,rocket_length*0.9,0),
                     radius=1.2, color=color.red)
booster_R = cylinder(pos=rocket.pos + vector(4,0,0), axis=vector(0,rocket_length*0.9,0),
                     radius=1.2, color=color.red)

# flame particle (simple cone)
flame = cone(pos=rocket.pos - vector(0,1,0), axis=vector(0,-10,0), radius=2.0, color=color.orange, visible=False)

# telemetry label
tele = label(pos=scene.center + vector(-8000, 20000, 0), xoffset=0, yoffset=0,
             text='', height=12, box=False, line=False)

# ---------- VEHICLE STAGING & PROPULSION ----------
# Stage parameters (approximate / simplified)
stages = [
    # stage 0: S200 boosters (treated as parallel boosters attached)
    {'name':'S200_boosters', 'thrust':2.3e6, 'Isp':250, 'prop_mass': 500000.0, 'dry_mass': 25000.0, 'burn_time':130.0},
    # stage 1: L110 core
    {'name':'L110_core', 'thrust':4.5e5, 'Isp':320, 'prop_mass': 180000.0, 'dry_mass': 12000.0, 'burn_time':200.0},
    # stage 2: C25 cryo upper
    {'name':'C25_cryo', 'thrust':1.0e5, 'Isp':450, 'prop_mass': 20000.0, 'dry_mass': 3000.0, 'burn_time':720.0}
]

# Initial aggregated rocket mass (including boosters/propmasses)
total_prop = sum(s['prop_mass'] for s in stages)
total_dry = sum(s['dry_mass'] for s in stages)
payload_mass = 1800.0   # kg
vehicle_mass = total_prop + total_dry + payload_mass

# state variables (SI units)
pos = vector(0, 0, 0)               # m (launch pad)
vel = vector(0, 0, 0)               # m/s
att_pitch = 90.0                    # degrees (vertical)
current_stage_index = 0
stage_time = 0.0
t = 0.0
dt = 0.2                            # simulation time-step (s)
logfile = "ascent_log.csv"

# telemetry CSV header
with open(logfile, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['t','stage','alt_m','speed_m_s','pitch_deg','mass_kg','thrust_N'])

# ---------- UTILITY FUNCTIONS ----------
def atmosphere_density(h):
    """Exponential atmosphere model (h in meters)."""
    return rho0 * math.exp(-h / H_atm) if h >= 0 else rho0

def pitch_program(t_total, stage_idx, stage_time_local):
    """Gravity turn / pitch program — smooth transition from vertical to near-horizontal."""
    # Simple program: hold vertical for 20s, then linear pitch down to 10-30deg depending on stage
    if t_total < 20.0:
        return 90.0
    else:
        # after 20s, reduce pitch at 0.25 deg/s for 300s until 25 deg
        target = 25.0
        rate_deg_per_s = 0.25
        new = max(target, 90.0 - rate_deg_per_s*(t_total-20.0))
        return new

def thrust_for_current_stage(stage_idx, stage_t):
    """Return thrust (N) and mass_flow (kg/s) for current stage or 0 if none."""
    if stage_idx >= len(stages):
        return 0.0, 0.0
    s = stages[stage_idx]
    if stage_t <= s['burn_time'] and s['prop_mass'] > 0:
        T = s['thrust']
        m_dot = T / (s['Isp'] * g0)
        return T, m_dot
    return 0.0, 0.0

def unit(v):
    n = mag(v)
    return v / n if n != 0 else vector(0,0,0)

# For drawing orbit arc later
orbit_path = curve(color=color.yellow, radius=2000)

# ---------- EVENT FLAGS ----------
boosters_detached = False
core_separated = False
payload_deployed = False

# ---------- MAIN SIMULATION LOOP ----------
print("Starting ascent simulation... (log -> {})".format(logfile))
scene.autoscale = False

while True:
    rate(60)
    # check if all stages done and payload deployed -> stop after short coasting
    if current_stage_index >= len(stages) and payload_deployed:
        # coast orbital phase for some seconds then exit loop
        if t > t_last_event + 60.0:
            print("Simulation finished.")
            break

    # determine thrust and massflow for current stage
    thrust, m_dot = thrust_for_current_stage(current_stage_index, stage_time)
    # pitch command
    att_pitch = pitch_program(t, current_stage_index, stage_time)
    pitch_rad = radians(att_pitch)

    # unit direction of thrust based on pitch (2D: x vertical, z horizontal)
    thrust_dir = vector(0, math.cos(pitch_rad), -math.sin(pitch_rad))  # positive y upward, z forward

    # aerodynamic drag (approx)
    h = pos.y
    rho = atmosphere_density(h)
    speed = mag(vel)
    Cd = 0.5
    A = math.pi * rocket_radius**2
    drag_mag = 0.5 * rho * speed**2 * Cd * A
    drag = -unit(vel) * drag_mag if speed > 0.1 else vector(0,0,0)

    # gravity acceleration at altitude
    r = Re + max(h, 0)
    g = mu / (r*r)   # m/s^2 towards center
    gravity = vector(0, -g, 0)

    # thrust acceleration
    if thrust > 0:
        a_thrust = thrust / vehicle_mass * thrust_dir
    else:
        a_thrust = vector(0,0,0)

    # total accel
    accel = a_thrust + drag / vehicle_mass + gravity

    # integrate velocity and position (simple Euler)
    vel = vel + accel * dt
    pos = pos + vel * dt

    # mass flow update
    if m_dot > 0:
        # consume propellant
        dm = m_dot * dt
        # reduce prop mass of current stage
        available = stages[current_stage_index]['prop_mass']
        used = min(dm, available)
        stages[current_stage_index]['prop_mass'] -= used
        vehicle_mass -= used

    # update stage timers and check separation
    stage_time += dt
    t += dt

    # Update visuals (scale geometry positions to current rocket pos)
    # rocket visually anchored at pos
    rocket.pos = vector(pos.x, pos.y, pos.z)
    rocket.axis = vector(0, rocket_length*math.cos(pitch_rad), -rocket_length*math.sin(pitch_rad))
    fairing.pos = rocket.pos + rocket.axis

    # boosters (attached until S200 separation)
    if not boosters_detached and current_stage_index == 0 and stage_time > stages[0]['burn_time']:
        # detach boosters
        boosters_detached = True
        print(">>> S200 Boosters separated at t={:.1f}s, alt={:.1f} m".format(t, pos.y))
        # assign velocities for boosters slightly outward + downward
        booster_L.velocity = vel + vector(-20.0, -40.0, 0)
        booster_R.velocity = vel + vector(20.0, -40.0, 0)
        booster_L.color = color.gray(0.5)
        booster_R.color = color.gray(0.5)
        # reduce vehicle mass by booster dry mass (approx)
        vehicle_mass -= stages[0]['dry_mass']
        # create separate small objects to represent boosters now independent
        booster_L_obj = cylinder(pos=rocket.pos + vector(-4,0,0), axis=vector(0,rocket_length*0.9,0),
                                 radius=1.2, color=color.gray(0.5))
        booster_R_obj = cylinder(pos=rocket.pos + vector(4,0,0), axis=vector(0,rocket_length*0.9,0),
                                 radius=1.2, color=color.gray(0.5))

    # if boosters detached, animate them
    if boosters_detached:
        # step booster objects if exist
        try:
            booster_L_obj.pos += booster_L.velocity * dt
            booster_R_obj.pos += booster_R.velocity * dt
            # apply gravity to boosters (simplified)
            booster_L.velocity += vector(0, -g, 0) * dt
            booster_R.velocity += vector(0, -g, 0) * dt
        except NameError:
            pass

    # check if current stage prop exhausted
    if current_stage_index < len(stages) and stages[current_stage_index]['prop_mass'] <= 0:
        print(">>> Stage {} ({}) burned out at t={:.1f}s, alt={:.1f} m".format(
            current_stage_index, stages[current_stage_index]['name'], t, pos.y))
        # subtract dry mass of burnt stage
        vehicle_mass -= stages[current_stage_index]['dry_mass']
        current_stage_index += 1
        stage_time = 0.0
        t_last_event = t

        # L110 core separation event (for visual)
        if current_stage_index == 1:
            print(">>> Core stage separation (L110)")
        if current_stage_index == 2:
            print(">>> Upper stage ignition (C25)")

    # payload deployment: after final stage burn finishes, create satellite and simulate orbit
    if not payload_deployed and current_stage_index >= len(stages):
        # deploy payload
        payload_deployed = True
        payload_pos = pos + rocket.axis.norm()*(rocket_length + 5.0)
        # compute approximate orbital velocity for circular orbit at altitude
        alt = payload_pos.y
        r_orbit = Re + alt
        v_circ = math.sqrt(mu / r_orbit)
        # set velocity direction tangential: assume forward along -z in our 2D plane
        vel_unit_tangent = vector(0, 0, -1)
        sat_vel = vel_unit_tangent * v_circ + vel  # add current vehicle velocity residual
        satellite = sphere(pos=payload_pos, radius=2.5, color=color.white, emissive=True)
        satellite.v = sat_vel
        print(">>> Payload deployed at t={:.1f}s, alt={:.1f} m, v_target={:.1f} m/s".format(t, alt, v_circ))
        # visualize predicted orbit arc for a short time (reset path)
        orbit_path.clear()
        orbit_steps = 600
        rvec = satellite.pos
        vv = satellite.v
        dt_orb = 10.0
        # compute a short orbit trace (simple two-body propagation)
        r_temp = vector(rvec)
        v_temp = vector(vv)
        for i in range(orbit_steps):
            rnorm = mag(r_temp)
            a_temp = -mu * r_temp / (rnorm**3)
            v_temp = v_temp + a_temp * dt_orb
            r_temp = r_temp + v_temp * dt_orb
            orbit_path.append(r_temp)
        # record last event time
        t_last_event = t

    # if satellite exists, propagate two-body motion (in same loop) and plot trailing path
    try:
        # compute acceleration towards Earth's center
        r_sat = satellite.pos
        rmag = mag(r_sat)
        a_sat = -mu * r_sat / (rmag**3)
        satellite.v = satellite.v + a_sat * dt
        satellite.pos = satellite.pos + satellite.v * dt
        # append to trail
        orbit_path.append(satellite.pos)
    except NameError:
        pass

    # simple flame visibility during active thrust
    flame.visible = (thrust > 0)
    flame.pos = rocket.pos - unit(rocket.axis)*5
    flame.axis = -unit(rocket.axis) * (8 + 4*math.sin(t*10))

    # telemetry text
    tele.text = ("t={:.1f}s\nalt={:.1f} m\nspeed={:.1f} m/s\npitch={:.1f} deg\nmass={:.1f} kg\nstage={}\nthrust={:.0f} N"
                 .format(t, pos.y, mag(vel), att_pitch, vehicle_mass, current_stage_index, thrust))

    # write log row
    with open(logfile, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([round(t,2), current_stage_index, round(pos.y,3), round(mag(vel),3), round(att_pitch,3), round(vehicle_mass,3), round(thrust,3)])

    # safety cutoff if rocket falls back to ground
    if pos.y < -1000:
        print("Vehicle crashed / fell back. Ending simulation.")
        break

# end of simulation
print("Log written to:", logfile)