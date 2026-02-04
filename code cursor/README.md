## Orbital Nexus – Space Debris Mission Control (Prototype UI)

Eliminating Debris. Elevating Space. is a **space-themed mission control interface** designed to explore workflows around **space debris monitoring, collision prediction, and cleanup missions**.  
This prototype focuses on a **modern, responsive front-end** with placeholder simulations that can later be wired to a real backend.

---

### Front-end Structure

- **`index.html`**  
  - Single-page layout with top navigation for all major modules:
    - Debris Scan, Track Debris, Orbit Visualizer, Collision Prediction
    - Mission Planner, Rendezvous Mode, Laser Ablation
    - Deorbit Simulation, Rocket Launch Simulation, Mission Log, System Diagnostics
  - **Operations Dashboard** at the top of the page surfaces a live-style telemetry grid, CI/CD activity feed, and stack overview that references the planned Node.js + MongoDB backend.
  - **Homepage / Hero**: headline, call-to-action buttons, live-style metrics, and a mini-orbit visualization.
  - **Footer**: contact info, social placeholders, and copyright.

- **`styles.css`**  
  - Dark, futuristic theme with **neon blue/green/orange accents** and **Orbitron + Inter** typography.
  - Responsive grid layout for all sections (desktop, tablet, mobile).
  - Reusable components: `panel-card`, `pill` groups, `telemetry-grid`, `event-list`, mission log and diagnostics cards.

- **`app.js`**  
  - Smooth scrolling navigation, mobile menu, active-section highlighting.
  - **Hero orbit widget**: animated canvas showing Earth and debris orbits.
  - **Orbit visualizer**: parameterized orbit drawing (altitude, inclination, type) with motion.
  - Simulated controls for each module:
    - Debris Scan → generates fake detections table.
    - Track Debris → shows orbital telemetry tiles for a selected object.
    - Collision Prediction → builds a demo list of conjunction events.
    - Mission Planner → high-level timeline phases.
    - Rendezvous Mode → narrative approach profile in LVLH terms.
    - Laser Ablation → simple Δv / perigee shift estimation (conceptual).
    - Deorbit Simulation → qualitative lifetime and event milestones.
    - Rocket Launch Simulation → stepwise launch phases with animated plume.
  - **Mission Log**: central log stream where each module appends status lines.
  - **System Diagnostics**: simulated health states for core systems, sensors, and data pipelines.

---

### How Modules Fit into a Mission Control Workflow

- **Debris Scan → Track Debris → Orbit Visualizer**
  - Scans detect new objects and populate the debris catalogue (simulated table).
  - Operators pick an object to track, view its **telemetry tiles**, then visualize its orbit and surrounding shells.

- **Orbit Visualizer → Collision Prediction**
  - Once the orbit is understood, the **Collision Prediction** module estimates close approaches between mission assets and debris clusters over a prediction horizon.

- **Collision Prediction → Mission Planner**
  - High-risk conjunctions trigger planning of **cleanup or avoidance missions**.
  - Mission Planner generates a conceptual multi-phase campaign: launch, phasing, rendezvous, operations, deorbit/disposal.

- **Mission Planner → Rendezvous Mode / Laser Ablation / Deorbit Simulation**
  - Each mission phase uses specialized tools:
    - **Rendezvous Mode**: terminal approach and station-keeping around debris.
    - **Laser Ablation**: engagements to lower perigee gradually.
    - **Deorbit Simulation**: end-of-life trajectory and re-entry corridor analysis.

- **Rocket Launch Simulation**
  - Provides a **pedagogical view** of getting a servicer into orbit: thrust profile, fuel use, stage separation, orbital insertion.

- **Mission Log & System Diagnostics**
  - Every module writes to the **Mission Log**, acting as a central timeline of actions and simulated events.
  - **System Diagnostics** give a control-room-style overview of system health (compute cluster, sensors, pipelines) and would be backed by live backend metrics in production.
- **Operations Dashboard**
  - Tiles summarize the status/version/latency of each mission microservice so operators see platform readiness before diving into specific tools.
  - The “code activity feed” mimics pushes from the CI/CD toolchain so teams know when new builds are live without leaving the console.

---

### Backend Integration Suggestions

You can integrate this front-end with a backend using either **Node.js** or **Python** (or both), depending on your stack and physics toolchain.

- **Recommended overall architecture**
  - Front-end: static assets (`index.html`, `styles.css`, `app.js`) served via CDN or a lightweight web server.
  - Backend API:
    - **REST + WebSocket** endpoints for:
      - Debris catalog & telemetry (`/api/debris`, `/api/objects/:id`).
      - Collision prediction results (`/api/conjunctions`).
      - Mission plans, logs, and diagnostics (`/api/missions`, `/api/logs`, `/api/health`).
    - Real-time feeds (e.g., WebSocket) to stream:
      - Live mission logs.
      - System diagnostics & metrics.
      - Updated orbit/telemetry samples for tracked objects.
  - Database:
    - **MongoDB** (sharded) as the primary mission datastore for catalogues, mission logs, dashboard snapshots, and access control.
    - Optional PostgreSQL/time-series sidecars for analytics-heavy workloads.

#### Option A – Node.js Backend

- Use **Node.js + Express (or Fastify)** for the API layer.
- Use **Socket.IO** or native **WebSocket** for live updates (mission logs, diagnostics).
- Integrate:
  - **TLE / orbit propagation** via:
    - JS libraries such as `satellite.js` for SGP4 and coordinate transforms.
    - Or call into separate Python microservices for heavy-duty numerics.
  - Authentication and RBAC with **JWT** or OAuth2; each API route mapped to mission roles (operator, planner, analyst).

**Example route mapping (conceptual):**

- `GET /api/debris?region=LEO` → returns a paginated list of debris objects with orbital elements.
- `GET /api/objects/:id/telemetry` → current state vector + derived metrics.
- `POST /api/conjunctions/run` → triggers or fetches pre-computed conjunction assessments.
- `POST /api/missions` → creates a mission plan from selected debris targets and constraints.
- `GET /api/ops-dashboard` → streams the Operations Dashboard tiles/feed.
- `GET /api/health` → feeds the **System Diagnostics** tiles.

#### Option B – Python Backend

- Use **FastAPI** or **Django REST Framework** for the HTTP API.
- Leverage Python’s ecosystem for **orbital mechanics and physics**:
  - `sgp4`, `skyfield`, `poliastro`, or internal propagators.
  - Custom models for **aerodynamic drag**, **laser ablation**, and **deorbit lifetime**.
- Background workers (Celery, RQ, or built-in background tasks in FastAPI) for:
  - Heavy conjunction analysis.
  - Long-running mission simulations and optimization.

You can still expose WebSockets (e.g. via FastAPI’s WebSocket support) so the front-end can subscribe to real-time updates (telemetry, logs, diagnostics).

---

### Wiring the Front-end to a Real Backend

Currently, all module outputs are **simulated in `app.js`**. To connect to real APIs:

- Replace demo generators with `fetch` calls:
  - Debris Scan: `fetch('/api/debris-scan?region=LEO&minSize=10')` → populate the debris table.
  - Track Debris: `fetch('/api/objects/:id/telemetry')` → update telemetry tiles and orbit parameters.
  - Collision Prediction: `POST /api/conjunctions/run` → display returned close-approach list.
  - Mission Planner / Deorbit / Ablation: call respective planning/simulation endpoints and map responses into UI timelines and tiles.

- Connect **Mission Log** to a WebSocket:
  - Subscribe to `/ws/logs` and append incoming JSON messages to the log stream instead of using `appendLog()` from internal events.

- Connect **Diagnostics** panels to `/api/health` or `/ws/metrics`:
  - Periodically fetch health status or subscribe to metrics updates and translate them into `good/warn/bad` indicators.

---

### Development & Customization

- **Run locally**
  - No build step required; open `index.html` directly in a browser or serve via a simple HTTP server:

```bash
node -e "require('http').createServer((_,res)=>{require('fs').createReadStream('index.html').pipe(res)}).listen(8080)"
```

- **Theming**
  - Adjust colors, spacing, and radii in `styles.css` under the `:root` variables.

- **Replacing placeholder physics**
  - Each simulated module has a dedicated init function in `app.js` (e.g., `initOrbitVisualizer`, `initLaserAblation`, `initDeorbitSimulation`).
  - These are the key places to:
    - Parse backend responses.
    - Map real orbital/physics data into the existing UI tiles and diagrams.

---

### Notes

- All numbers shown in the interface (Δv, perigee shifts, lifetimes, etc.) are **illustrative only** and must be replaced with validated models for real missions.
- The UI is intentionally clean and minimal to keep the cognitive load low for operators while still **inspiring innovation** for space debris remediation concepts.


