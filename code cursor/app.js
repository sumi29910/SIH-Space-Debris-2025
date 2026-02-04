// Core navigation & layout interactions
document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll("main section[id]");
  const menuToggle = document.querySelector(".menu-toggle");
  const mainNav = document.querySelector(".main-nav");
  const footerYear = document.getElementById("footer-year");

  if (footerYear) {
    footerYear.textContent = new Date().getFullYear();
  }

  // Smooth scroll for nav and hero buttons
  function smoothScrollTo(targetId) {
    const el = document.querySelector(targetId);
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const offset = window.scrollY + rect.top - 84; // account for header
    window.scrollTo({ top: offset, behavior: "smooth" });
  }

  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const href = link.getAttribute("href");
      if (!href) return;
      smoothScrollTo(href);
      mainNav.classList.remove("is-open");
    });
  });

  document.querySelectorAll("[data-scroll-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-scroll-target");
      if (target) smoothScrollTo(target);
      // Also trigger the dashboard simulation when the "Debris Trajectory View" button is clicked
      if (btn.classList.contains('btn') && btn.classList.contains('ghost') && btn.textContent.trim() === 'Debris Trajectory View') {
        triggerDashboardSimulation();
        console.log("Successfully executed the SIH_Eighth.py script.");
      }
    });
  });

  const heroLauncherBtn = document.getElementById("btn-mission-launcher");
  if (heroLauncherBtn) {
    heroLauncherBtn.addEventListener("click", () => {
      triggerMissionSimulation();
      console.log("Successfully exectued the python script.");
      // Also scroll to the Mission Planner section
      smoothScrollTo('#mission-planner');
    });
  }

  const missionSimulationBtn = document.getElementById("btn-mission-simulation");
  if (missionSimulationBtn) {
    missionSimulationBtn.addEventListener("click", () => {
      triggerMissionSimulation();
      console.log("Mission Simulation button clicked. Executing Python script.");
    });
  }

  // Mobile nav toggle
  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      mainNav.classList.toggle("is-open");
    });
  }

  // Active nav link on scroll
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.getAttribute("id");
        if (!id) return;
        navLinks.forEach((link) => {
          const href = link.getAttribute("href");
          link.classList.toggle("active", href === `#${id}`);
        });
      });
    },
    { threshold: 0.3 }
  );

  sections.forEach((section) => observer.observe(section));

  // --- NEW: Debris Simulation Configuration and Logic ---
const MAX_RANGE = 100;
const SWEEP_SPEED = 2.0; // Degrees per frame
const DEBRIS_SPEED = 0.5;
const DETECTION_ARC = 2.0; // Narrow angle for detection
const DECAY_RATE = 0.05;
const MAX_DEBRIS = 20;
const DESTRUCTION_PROBABILITY = 0.4;
const RANGE_ZONE_THRESHOLD = 50; // Debris within this distance are "in range zone"

let debrisDataList = [];
let debrisCounter = 0;
let currentSweepAngle = 90;

// RNG Class (inspired by Python RNG)
class DebrisInspiredRNG {
    constructor(seed = null) {
        this.seed = seed ? seed : Math.random();
    }

    randomFloat(min, max) {
        return Math.random() * (max - min) + min;
    }

    randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    randomChoice(probability) {
        return Math.random() < probability;
    }

    generateDebris() {
        debrisCounter++;
        return {
            id: debrisCounter,
            r: this.randomFloat(10, MAX_RANGE * 0.9),
            angle: this.randomFloat(0, 360),
            status: 0.0 // 0: undetected, >0: detected/fading
        };
    }
}

const rng = new DebrisInspiredRNG(); // Initialize RNG

// Polar to Cartesian conversion
function polarToCartesian(r, theta) {
    const rad = (theta * Math.PI) / 180;
    return { x: r * Math.cos(rad), y: r * Math.sin(rad) };
}

// Create new debris
function createDebrisInstance() {
    return rng.generateDebris();
}

// Simulation loop (runs every 1 second)
function simulateDebrisSweep() {
    // Generate new debris occasionally
    if (debrisDataList.length < MAX_DEBRIS && rng.randomInt(0, 10) < 2) { // ~20% chance per tick
        debrisDataList.push(createDebrisInstance());
    }

    // Update sweep angle
    currentSweepAngle = (currentSweepAngle - SWEEP_SPEED) % 360;

    // Define detection arc
    const startAngle = (currentSweepAngle - DETECTION_ARC) % 360;
    const endAngle = currentSweepAngle;

    // Update debris
    for (let i = debrisDataList.length - 1; i >= 0; i--) {
        const d = debrisDataList[i];
        d.angle = (d.angle - DEBRIS_SPEED) % 360;

        // Check if in detection arc
        let inArc = false;
        if (startAngle > endAngle) {
            inArc = (d.angle >= startAngle) || (d.angle <= endAngle);
        } else {
            inArc = (d.angle >= startAngle && d.angle <= endAngle);
        }

        if (inArc && d.status === 0) {
            d.status = 1.0; // Newly detected
        }

        // Decay/removal logic
        if (d.status > 0) {
            d.status -= DECAY_RATE;
            if (d.status <= 0.05) {
                if (rng.randomChoice(DESTRUCTION_PROBABILITY)) {
                    debrisDataList.splice(i, 1); // Remove
                    continue;
                } else {
                    d.status = 0; // Reset to undetected
                }
            }
        }
    }

    // Count debris "in range zone" (r < RANGE_ZONE_THRESHOLD)
      const inRangeCount = debrisDataList.filter(d => d.r < RANGE_ZONE_THRESHOLD).length;

    // --- ENHANCED FLUCTUATING UI LOGIC ---
    // Generate a random count with fluctuations to simulate scanning activity
    const baseCount = inRangeCount;
    // Add random fluctuation to make it more dynamic
    const fluctuation = Math.floor(Math.random() * 5) - 2; // -2 to +2 fluctuation
    const dynamicCount = Math.max(0, baseCount + fluctuation);
    
    // Generate random time for additional dynamic effect
    const randomTime = (Math.random() * 5 + 0.5).toFixed(2); // Between 0.50 and 5.50 hours

    // Format the new content using the dynamic debris count and the fluctuating time
    const newCountHTML = `${dynamicCount} <span style="font-size: 15px; font-weight: 100;">+${randomTime} hours</span>`;

      // Update the HTML element
      const countElement = document.getElementById('debris-range-count');
      if (countElement) {
          countElement.innerHTML = newCountHTML;
      }
      
      // Update the Orbital Safety Index based on debris count
      const safetyIndexElement = document.querySelector('.panel-row .panel-card:nth-child(2) .panel-value');
      if (safetyIndexElement) {
          if (dynamicCount >= 15) {
              safetyIndexElement.textContent = 'High Risk';
              safetyIndexElement.className = 'panel-value value-bad'; // Red text
          } else if (dynamicCount >= 8) {
              safetyIndexElement.textContent = 'Moderate Risk';
              safetyIndexElement.className = 'panel-value value-warn'; // Yellow/orange text
          } else if (dynamicCount >= 3) {
              safetyIndexElement.textContent = 'Low Risk';
              safetyIndexElement.className = 'panel-value value-medium'; // Amber text
          } else {
              safetyIndexElement.textContent = 'All Green';
              safetyIndexElement.className = 'panel-value value-good'; // Green text
          }
      }
}

  // Generic pill toggle
  document.querySelectorAll(".pill-group").forEach((group) => {
    group.addEventListener("click", (e) => {
      const btn = e.target.closest(".pill");
      if (!btn) return;
      group.querySelectorAll(".pill").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  initHeroOrbit();
  initDebrisScan();
  initTrackDebris();
  initOrbitVisualizer();
  initCollisionPrediction();
  initOpsDashboard();
  initMissionPlanner();
  initRendezvous();
  initLaserAblation();
  initDeorbitSimulation();
  initRocketSimulation();
  initMissionLog();
  initDiagnostics();
  
  // Start the debris sweep simulation loop
  setInterval(simulateDebrisSweep, 1000); // Update every 1 second
});

// ========== HERO ORBIT MINI-VISUAL ==========
function initHeroOrbit() {
  const canvas = document.getElementById("hero-orbit-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  let t = 0;
  function draw() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;

    // Earth
    const earthRadius = Math.min(w, h) * 0.18;
    const grad = ctx.createRadialGradient(
      cx - earthRadius / 3,
      cy - earthRadius / 3,
      earthRadius * 0.1,
      cx,
      cy,
      earthRadius
    );
    grad.addColorStop(0, "#3ad1ff");
    grad.addColorStop(0.4, "#214aff");
    grad.addColorStop(1, "#020618");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, earthRadius, 0, Math.PI * 2);
    ctx.fill();

    // Orbits
    ctx.save();
    ctx.translate(cx, cy);
    const baseRadius = earthRadius * 1.6;
    const orbitColors = ["#33b5ff", "#4ce3b2", "#ffb35c"];
    for (let i = 0; i < 3; i++) {
      const r = baseRadius + i * 12;
      ctx.strokeStyle = `${orbitColors[i]}33`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(0, 0, r, r * 0.75, (i * Math.PI) / 6, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Debris dots
    const debrisCount = 40;
    for (let i = 0; i < debrisCount; i++) {
      const angle = (t * 0.002 + (i / debrisCount) * Math.PI * 2) % (Math.PI * 2);
      const radius = baseRadius + (i % 3) * 10;
      const ex = Math.cos(angle) * radius;
      const ey = Math.sin(angle) * radius * 0.76;
      const color = orbitColors[i % orbitColors.length];
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.8;
      ctx.beginPath();
      ctx.arc(ex, ey, 1.4, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    t += 16;
    requestAnimationFrame(draw);
  }
  draw();
}

// ========== DEBRIS SCAN ==========
function initDebrisScan() {
  const thresholdRange = document.getElementById("scan-threshold");
  const thresholdValue = document.getElementById("scan-threshold-value");
  const runButton = document.getElementById("btn-run-scan");
  const tableBody = document.getElementById("debris-scan-table-body");

  if (!thresholdRange || !thresholdValue || !runButton || !tableBody) return;

  thresholdRange.addEventListener("input", () => {
    thresholdValue.textContent = `${thresholdRange.value} cm`;
  });

  runButton.addEventListener("click", () => {
    const sizeMin = Number(thresholdRange.value);
    const rows = [];
    for (let i = 0; i < 6; i++) {
      const size = (sizeMin + Math.random() * 70).toFixed(1);
      const alt = (350 + Math.random() * 1500).toFixed(0);
      const inc = (Math.random() * 98).toFixed(1);
      const riskVal = Math.random();
      const risk =
        riskVal > 0.8 ? "High" : riskVal > 0.55 ? "Medium" : riskVal > 0.3 ? "Low" : "Minimal";
      rows.push(
        `<tr>
          <td>OBJ-${Math.floor(Math.random() * 90000 + 10000)}</td>
          <td>${size}</td>
          <td>${alt}</td>
          <td>${inc}</td>
          <td>${risk}</td>
        </tr>`
      );
    }
    tableBody.innerHTML = rows.join("");
    appendLog("Debris Scan", "Executed simulated debris sweep.");

    triggerTrackSimulation("DEBRIS_SCAN_TARGET");
    
    // Also trigger the SIH_Twelfth.py debris scan simulation
    triggerDebrisScanSimulation();
  });
}

// ========== OPS DASHBOARD ==========
function initOpsDashboard() {
  const metricGrid = document.getElementById("ops-metric-grid");
  const activityFeed = document.getElementById("ops-activity-feed");
  if (!metricGrid || !activityFeed) return;

  const systems = [
    { name: "Debris Scan Engine", value: "v1.8.2", status: "good", detail: "Nominal" },
    { name: "Orbit Visualizer Core", value: "GPU mesh 60%", status: "good", detail: "Nominal" },
    { name: "Collision Predictor", value: "Job queue: 3", status: "warn", detail: "Lag 2.1s" },
    { name: "Mission Planner API", value: "Latency 110ms", status: "good", detail: "Nominal" },
    { name: "Diagnostics Stream", value: "WS 5.1 kb/s", status: "good", detail: "Live" },
    { name: "Mission Log Writer", value: "Mongo sync", status: "good", detail: "Nominal" },
  ];

  const feedMessages = [
    "CI pipeline green-lit the new debris classifier.",
    "Mission log replicaset synced with backup node.",
    "Collision predictor pushed fresh coefficients.",
    "Orbit visualizer shader bundle rebuilt for WebGL2.",
    "Diagnostics bus validated JWT rotation sequence.",
    "Mission planner microservice redeployed with hotfix.",
  ];

  function renderMetrics() {
    metricGrid.innerHTML = systems
      .map(
        (sys) => `
        <div class="tile">
          <div class="label">${sys.name}</div>
          <div class="value">${sys.value}</div>
          <div class="status-chip ${sys.status}">${sys.detail}</div>
        </div>`
      )
      .join("");
  }

  function pushFeed(text) {
    const time = new Date().toLocaleTimeString([], { hour12: false });
    const item = document.createElement("li");
    item.innerHTML = `<span class="event-time">${time}</span>${text}`;
    activityFeed.prepend(item);
    while (activityFeed.children.length > 6) {
      activityFeed.removeChild(activityFeed.lastElementChild);
    }
    appendLog("DevOps", text);
  }

  function randomizeSystem() {
    const idx = Math.floor(Math.random() * systems.length);
    const sys = systems[idx];
    const delta = (Math.random() * 0.5 + 0.2).toFixed(1);
    if (sys.name === "Collision Predictor") {
      sys.value = `Job queue: ${(Math.random() * 4).toFixed(0)}`;
      sys.status = Math.random() > 0.7 ? "warn" : "good";
      sys.detail = sys.status === "warn" ? `Lag ${delta}s` : "Nominal";
    } else if (sys.name === "Mission Planner API") {
      sys.value = `Latency ${(90 + Math.random() * 40).toFixed(0)}ms`;
      sys.status = "good";
      sys.detail = "Nominal";
    } else if (sys.name === "Orbit Visualizer Core") {
      sys.value = `GPU mesh ${(55 + Math.random() * 15).toFixed(0)}%`;
      sys.detail = "Nominal";
    } else if (sys.name === "Diagnostics Stream") {
      sys.value = `WS ${(4 + Math.random() * 2).toFixed(1)} kb/s`;
    } else if (sys.name === "Mission Log Writer") {
      sys.value = "Mongo sync";
      sys.detail = Math.random() > 0.8 ? "Indexing" : "Nominal";
    } else {
      sys.value = `v1.${(Math.random() * 9 + 1).toFixed(1)}`;
      sys.detail = "Nominal";
    }
    renderMetrics();
    pushFeed(feedMessages[Math.floor(Math.random() * feedMessages.length)]);
  }

  renderMetrics();
  pushFeed("Ops dashboard initialized with secure Node.js + MongoDB pipeline placeholder.");
  setInterval(randomizeSystem, 4500);
}

// ========== TRACK DEBRIS ==========
function initTrackDebris() {
  const btn = document.getElementById("btn-track-object");
  const telemetryGrid = document.getElementById("telemetry-grid");
  const input = document.getElementById("track-id");
  if (!btn || !telemetryGrid) return;

  btn.addEventListener("click", () => {
    const id = (input && input.value.trim()) || `SIM-${Math.floor(Math.random() * 9999)}`;
    const alt = (350 + Math.random() * 1200).toFixed(0);
    const inc = (20 + Math.random() * 80).toFixed(1);
    const period = (85 + Math.random() * 50).toFixed(1);
    const raan = (Math.random() * 360).toFixed(1);

    telemetryGrid.innerHTML = `
      <div class="tile">
        <div class="label">Object</div>
        <div class="value">${id}</div>
      </div>
      <div class="tile">
        <div class="label">Altitude</div>
        <div class="value">${alt} km</div>
      </div>
      <div class="tile">
        <div class="label">Inclination</div>
        <div class="value">${inc}°</div>
      </div>
      <div class="tile">
        <div class="label">Period</div>
        <div class="value">${period} min</div>
      </div>
      <div class="tile">
        <div class="label">RAAN</div>
        <div class="value">${raan}°</div>
      </div>
      <div class="tile">
        <div class="label">Tracking State</div>
        <div class="value accent">Locked</div>
      </div>
    `;

    appendLog("Track Debris", `Started simulated tracking for object ${id}.`);
    triggerTrackSimulation(id);
  });
}

// ========== ORBIT VISUALIZER ==========
 function initOrbitVisualizer() {
   const canvas = document.getElementById("orbit-visualizer-canvas");
   if (!canvas) return;
   const ctx = canvas.getContext("2d");

   const altInput = document.getElementById("orbit-altitude");
   const incInput = document.getElementById("orbit-inclination");
   const typeSelect = document.getElementById("orbit-type");
   const eccInput = document.getElementById("orbit-eccentricity");
   const btnUpdate = document.getElementById("btn-update-orbit");
   const orbitTitle = document.getElementById("orbit-title");

   let params = {
     altitude: altInput ? Number(altInput.value) : 500,
     inclination: incInput ? Number(incInput.value) : 51.6,
     eccentricity: eccInput ? Number(eccInput.value) : 0.01,
     type: typeSelect ? typeSelect.value : "LEO",
   };

  function resize() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    drawOrbit();
  }

  function drawOrbit() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;
    const earthRadius = Math.min(w, h) * 0.18;

    // Enhanced Earth with more realistic representation
    const grad = ctx.createRadialGradient(
      cx - earthRadius / 3,
      cy - earthRadius / 3,
      earthRadius * 0.1,
      cx,
      cy,
      earthRadius
    );
    grad.addColorStop(0, "#37c4ff");
    grad.addColorStop(0.35, "#2152ff");
    grad.addColorStop(1, "#020617");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, earthRadius, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw latitude lines for research-oriented visualization
    ctx.strokeStyle = "#ffffff22";
    ctx.lineWidth = 0.5;
    for (let lat = -80; lat <= 80; lat += 20) {
      const latRadius = earthRadius * Math.cos((lat * Math.PI) / 180);
      ctx.beginPath();
      ctx.arc(cx, cy, latRadius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Common LEO shells
    const shells = [
      { alt: 300, color: "#33b5ff44", label: "VLEO" },
      { alt: 400, color: "#33b5ff66", label: "ISS" },
      { alt: 550, color: "#4ce3b266", label: "Starlink" },
      { alt: 800, color: "#4ce3b244", label: "SLEO" },
    ];

    shells.forEach((shell) => {
      const factor = 1 + Math.log10(shell.alt / 20 + 1) * 0.4;
      const r = earthRadius * factor;
      ctx.strokeStyle = shell.color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
      
      // Add orbital shell labels for research purposes
      ctx.fillStyle = shell.color;
      ctx.font = "8px 'Inter', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(shell.label, cx, cy - r - 8);
    });

    // Draw debris in various orbits for research visualization
    const debrisCount = 50;
    for (let i = 0; i < debrisCount; i++) {
      // Generate random orbit parameters for debris
      const debrisAltitude = 300 + Math.random() * 700; // Between 300-1000 km
      const debrisFactor = 1 + Math.log10(debrisAltitude / 20 + 1) * 0.4;
      const debrisRadius = earthRadius * debrisFactor;
      const debrisAngle = Math.random() * Math.PI * 2;
      const debrisInclination = (Math.random() * 180 - 90) * Math.PI / 180; // -90 to +90 degrees in radians
      
      // Calculate position with inclination
      let debrisX = Math.cos(debrisAngle) * debrisRadius;
      let debrisY = Math.sin(debrisAngle) * debrisRadius * Math.cos(debrisInclination);
      
      // Random size for debris (smaller than satellite)
      const debrisSize = 0.8 + Math.random() * 1.2;
      
      // Different colors for different types of debris
      const debrisColors = ["#ff5c7a", "#ffb35c", "#4ce3b2", "#33b5ff"];
      const debrisColor = debrisColors[Math.floor(Math.random() * debrisColors.length)];
      
      ctx.fillStyle = debrisColor;
      ctx.beginPath();
      ctx.arc(cx + debrisX, cy + debrisY, debrisSize, 0, Math.PI * 2);
      ctx.fill();
    }

    // Highlighted orbit with eccentricity
    const factor = 1 + Math.log10(params.altitude / 200 + 1) * 0.5;
    const rOrbit = earthRadius * factor;
    const inclinationRad = (params.inclination * Math.PI) / 180;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-inclinationRad);

    // Create enhanced gradient for the orbit
    const orbitGrad = ctx.createLinearGradient(-rOrbit, 0, rOrbit, 0);
    orbitGrad.addColorStop(0, "#33b5ff");
    orbitGrad.addColorStop(0.5, "#4ce3b2");
    orbitGrad.addColorStop(1, "#ffb35c");
    ctx.strokeStyle = orbitGrad;
    ctx.lineWidth = 2;
    
    // Draw elliptical orbit based on eccentricity
    ctx.beginPath();
    const e = params.eccentricity;
    const ry = rOrbit * Math.sqrt(1 - e * e); // Calculate semi-minor axis
    ctx.ellipse(0, 0, rOrbit, ry, 0, 0, Math.PI * 2);
    ctx.stroke();

    // Satellite marker with enhanced visualization
    const satAngle = Date.now() * 0.00002; // Very slow rotation for realistic movement
    const satX = Math.cos(satAngle) * rOrbit;
    const satY = Math.sin(satAngle) * ry;
    
    // Draw satellite with enhanced graphics
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(satX, satY, 5, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw satellite trail
    ctx.strokeStyle = "#ffffff44";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const trailAngle = satAngle - (i * 0.002); // Adjusted for slower movement
      const trailX = Math.cos(trailAngle) * rOrbit;
      const trailY = Math.sin(trailAngle) * ry;
      if (i === 0) {
        ctx.moveTo(trailX, trailY);
      } else {
        ctx.lineTo(trailX, trailY);
      }
    }
    ctx.stroke();
    
    // Draw velocity vector
    const velocityX = -Math.sin(satAngle) * 1; // Reduced for more realistic movement
    const velocityY = Math.cos(satAngle) * 1; // Reduced for more realistic movement
    ctx.strokeStyle = "#4ce3b2";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(satX, satY);
    ctx.lineTo(satX + velocityX, satY + velocityY);
    ctx.stroke();
    
    // Draw velocity vector arrowhead
    const angle = Math.atan2(velocityY, velocityX);
    const arrowSize = 4;
    ctx.beginPath();
    ctx.moveTo(satX + velocityX, satY + velocityY);
    ctx.lineTo(
      satX + velocityX - arrowSize * Math.cos(angle - Math.PI/6),
      satY + velocityY - arrowSize * Math.sin(angle - Math.PI/6)
    );
    ctx.lineTo(
      satX + velocityX - arrowSize * Math.cos(angle + Math.PI/6),
      satY + velocityY - arrowSize * Math.sin(angle + Math.PI/6)
    );
    ctx.closePath();
    ctx.fillStyle = "#4ce3b2";
    ctx.fill();

    ctx.restore();
  }

  resize();
  window.addEventListener("resize", resize);

  btnUpdate &&
     btnUpdate.addEventListener("click", () => {
       // Ensure orbit type is restricted to LEO
       const selectedType = typeSelect ? typeSelect.value : "LEO";
       const isLEOType = ["LEO", "VLEO", "SLEO", "PO", "SSO"].includes(selectedType);
       
       if (!isLEOType) {
         // Force to LEO if not a valid LEO type
         params = {
           altitude: altInput ? Number(altInput.value) : 500,
           inclination: incInput ? Number(incInput.value) : 51.6,
           eccentricity: eccInput ? Number(eccInput.value) : 0.01,
           type: "LEO",
         };
         typeSelect.value = "LEO";
         alert("Orbit type has been restricted to LEO. Only LEO orbits are supported in this section.");
       } else {
         params = {
           altitude: altInput ? Number(altInput.value) : 500,
           inclination: incInput ? Number(incInput.value) : 51.6,
           eccentricity: eccInput ? Number(eccInput.value) : 0.01,
           type: selectedType,
         };
       }
       
       // Update the orbit title dynamically
       updateOrbitTitle();
       
       drawOrbit();
       appendLog(
         "Orbit Visualizer",
         `Updated orbit to ${params.type} at ${params.altitude} km, inc=${params.inclination}°.`
       );
     });
       
   // Function to update the orbit title based on user inputs
   function updateOrbitTitle() {
     if (orbitTitle) {
       const altitude = params.altitude;
       const inclination = params.inclination;
       const orbitType = params.type;
       
       // Format the title based on the orbit type
       let orbitDescription = "";
       switch(orbitType) {
         case "VLEO":
           orbitDescription = "Very Low Earth Orbit";
           break;
         case "SLEO":
           orbitDescription = "Standard Low Earth Orbit";
           break;
         case "PO":
           orbitDescription = "Polar Orbit";
           break;
         case "SSO":
           orbitDescription = "Sun-Synchronous Orbit";
           break;
         default:
           orbitDescription = "Low Earth Orbit";
       }
       
       // Calculate orbital period for research-oriented information
       const earthRadius = 6371; // km
       const semiMajorAxis = earthRadius + altitude; // km
       // Orbital period in minutes using Kepler's third law (simplified)
       const orbitalPeriod = 2 * Math.PI * Math.sqrt(Math.pow(semiMajorAxis, 3) / 398600); // 398600 = GM for Earth
       const periodMinutes = (orbitalPeriod / 60).toFixed(2);
       
       orbitTitle.innerHTML = `${orbitDescription} | Alt: ${altitude}km | Inc: ${inclination}° | Period: ${periodMinutes}min`;
     }
   }
   
   // Add event listeners to update the title and visualization in real-time as users change values
   if (altInput) {
     altInput.addEventListener('input', () => {
       params.altitude = Number(altInput.value);
       updateOrbitTitle();
       drawOrbit(); // Update the orbit visualization immediately
     });
   }
   
   if (incInput) {
     incInput.addEventListener('input', () => {
       params.inclination = Number(incInput.value);
       updateOrbitTitle();
       drawOrbit(); // Update the orbit visualization immediately
     });
   }
   
   if (typeSelect) {
     typeSelect.addEventListener('change', () => {
       const selectedType = typeSelect.value;
       const isLEOType = ["LEO", "VLEO", "SLEO", "PO", "SSO"].includes(selectedType);
       
       if (!isLEOType) {
         params.type = "LEO";
         typeSelect.value = "LEO";
         alert("Orbit type has been restricted to LEO. Only LEO orbits are supported in this section.");
       } else {
         params.type = selectedType;
       }
       updateOrbitTitle();
       drawOrbit(); // Update the orbit visualization immediately
     });
   }
   
   if (eccInput) {
     eccInput.addEventListener('input', () => {
       params.eccentricity = Number(eccInput.value);
       drawOrbit(); // Update the orbit visualization immediately
     });
   }

  // Simple animation loop to keep satellite moving
  (function animate() {
    drawOrbit();
    requestAnimationFrame(animate);
  })();
}

// ========== COLLISION PREDICTION ==========
function initCollisionPrediction() {
  const btn = document.getElementById("btn-run-cp");
  const list = document.getElementById("cp-event-list");
  const primary = document.getElementById("cp-primary");
  const debris = document.getElementById("cp-debris");
  const horizon = document.getElementById("cp-horizon");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const primaryName = (primary && primary.value.trim()) || "MissionSat-01";
    const debrisCloud = debris ? debris.value : "LEO Fragmentation Event";
    const hours = horizon ? Number(horizon.value) : 72;

    const events = [];
    const count = 3 + Math.floor(Math.random() * 3);
    for (let i = 0; i < count; i++) {
      const t = (Math.random() * hours).toFixed(1);
      const miss = (0.1 + Math.random() * 4).toFixed(2);
      const pc = (Math.random() * 1e-3).toExponential(2);
      events.push(
        `<li><span class="event-time">T+${t} h</span>${primaryName} vs ${debrisCloud} — miss distance ${miss} km, Pc=${pc}</li>`
      );
    }
    list.innerHTML = events.join("");
    appendLog(
      "Collision Prediction",
      `Computed ${events.length} conjunction candidates for ${primaryName}.`
    );
  });
}

// ========== MISSION PLANNER ==========
function initMissionPlanner() {
  const btn = document.getElementById("btn-generate-plan");
  const list = document.getElementById("mission-timeline");
  const nameInput = document.getElementById("mp-mission-name");
  const targetCount = document.getElementById("mp-target-count");
  const timeframe = document.getElementById("mp-timeframe");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const name = (nameInput && nameInput.value.trim()) || "Orbital Cleanup Campaign";
    const targets = targetCount ? Number(targetCount.value) : 3;
    const days = timeframe ? Number(timeframe.value) : 7;

    const phases = [
      "Launch & Orbit Raise",
      "Phasing & First Rendezvous",
      "Debris Capture & Characterization",
      "Secondary Rendezvous & Operations",
      "Deorbit & Disposal",
    ];

    list.innerHTML = phases
      .map(
        (phase, idx) => `
      <li>
        <span class="timeline-step">P${idx + 1}</span>
        <span class="timeline-desc">${phase} · targeting ${targets} objects over ~${days} days.</span>
      </li>
    `
      )
      .join("");

    appendLog("Mission Planner", `Generated demo mission plan "${name}".`);
  });
}

// ========== RENDEZVOUS MODE ==========
function initRendezvous() {
  const btn = document.getElementById("btn-sim-rv");
  const list = document.getElementById("rv-event-list");
  const rangeInput = document.getElementById("rv-range");
  const relVelInput = document.getElementById("rv-rel-velocity");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const range = rangeInput ? Number(rangeInput.value) : 10;
    const relVel = relVelInput ? Number(relVelInput.value) : 5;

    list.innerHTML = `
      <li><span class="event-time">T-2 orbits</span> Phasing burns initialized to sync with target orbital plane.</li>
      <li><span class="event-time">T-1 orbit</span> Relative range reduced from ${range.toFixed(
        1
      )} km to 2 km with in-plane maneuvers.</li>
      <li><span class="event-time">T-20 min</span> R-bar approach initiated, relative velocity trimmed to ${relVel.toFixed(
        1
      )} m/s.</li>
      <li><span class="event-time">T-0</span> Final braking and station-keeping at 20 m stand-off.</li>
    `;

    appendLog(
      "Rendezvous Mode",
      `Simulated approach profile from ~${range.toFixed(1)} km and ${relVel.toFixed(
        1
      )} m/s relative velocity.`
    );
  });
}

// ========== LASER ABLATION ==========
function initLaserAblation() {
  const btn = document.getElementById("btn-la-sim");
  const grid = document.getElementById("la-output-grid");
  const power = document.getElementById("la-power");
  const duration = document.getElementById("la-duration");
  const incidence = document.getElementById("la-incidence");
  if (!btn || !grid) return;

  btn.addEventListener("click", () => {
    const p = power ? Number(power.value) : 50;
    const t = duration ? Number(duration.value) : 120;
    const ang = incidence ? Number(incidence.value) : 30;

    const energy = (p * t / 1000).toFixed(2); // MJ
    const efficiency = Math.max(0.1, (90 - ang) / 100);
    const deltaV = (0.02 * p * efficiency).toFixed(3); // m/s, purely illustrative
    const perigeeDrop = (deltaV * 8).toFixed(1); // km, illustrative

    grid.innerHTML = `
      <div class="tile">
        <div class="label">Deposited Energy</div>
        <div class="value">${energy} MJ</div>
      </div>
      <div class="tile">
        <div class="label">Coupling Efficiency</div>
        <div class="value">${(efficiency * 100).toFixed(0)}%</div>
      </div>
      <div class="tile">
        <div class="label">Δv Estimate</div>
        <div class="value accent">${deltaV} m/s</div>
      </div>
      <div class="tile">
        <div class="label">Perigee Shift</div>
        <div class="value">${perigeeDrop} km (approx.)</div>
      </div>
    `;

    appendLog(
      "Laser Ablation",
      `Estimated demo Δv=${deltaV} m/s for ${p} kW, ${t} s, ${ang}° incidence.`
    );
  });
}

// ========== DEORBIT SIMULATION ==========
function initDeorbitSimulation() {
  const btn = document.getElementById("btn-do-sim");
  const list = document.getElementById("do-event-list");
  const altInput = document.getElementById("do-altitude");
  const massInput = document.getElementById("do-mass");
  const cdInput = document.getElementById("do-cd");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const alt = altInput ? Number(altInput.value) : 800;
    const mass = massInput ? Number(massInput.value) : 500;
    const cd = cdInput ? Number(cdInput.value) : 2.2;

    const lifetimeYears = Math.max(0.1, (alt - 200) / (50 * cd));
    const lifetime = lifetimeYears > 1 ? `${lifetimeYears.toFixed(1)} years` : `${(
      lifetimeYears * 365
    ).toFixed(0)} days`;

    list.innerHTML = `
      <li><span class="event-time">T+0</span> Deorbit burn lowers perigee to ~220 km.</li>
      <li><span class="event-time">T+${(lifetimeYears * 0.4).toFixed(
        1
      )} yr</span> Peak drag and heating as object repeatedly dips into denser atmosphere.</li>
      <li><span class="event-time">T+${lifetime}</span> Breakup and burn-up; surviving fragments targeted to oceanic corridor.</li>
      <li><span class="event-time">Summary</span> Mass=${mass.toFixed(
        0
      )} kg, Cd=${cd.toFixed(2)}, initial altitude=${alt.toFixed(0)} km.</li>
    `;

    appendLog("Deorbit Simulation", `Ran deorbit demo from ${alt.toFixed(0)} km.`);
    triggerDeorbitSimulation(alt, mass, cd);
  });
}

// ========== ROCKET LAUNCH SIMULATION ==========
function initRocketSimulation() {
  const playBtn = document.getElementById("btn-rocket-play");
  const plume = document.getElementById("rocket-plume");
  const diagram = document.querySelector(".rocket-diagram");
  const telemetryGrid = document.getElementById("rocket-telemetry-grid");
  const timelineButtons = document.querySelectorAll("[data-rocket-step]");
  if (!playBtn || !plume || !diagram || !telemetryGrid) return;

  const steps = [
    {
      name: "Pre-launch",
      thrust: "0 kN",
      fuel: "100%",
      altitude: "0 km",
      velocity: "0 m/s",
    },
    {
      name: "Max-Q",
      thrust: "7,000 kN",
      fuel: "78%",
      altitude: "15 km",
      velocity: "750 m/s",
    },
    {
      name: "Stage Separation",
      thrust: "1,200 kN",
      fuel: "42%",
      altitude: "75 km",
      velocity: "3.4 km/s",
    },
    {
      name: "Orbital Insertion",
      thrust: "0 kN (coasting)",
      fuel: "8%",
      altitude: "520 km",
      velocity: "7.6 km/s",
    },
  ];

  function renderStep(index) {
    const step = steps[index];
    telemetryGrid.innerHTML = `
      <div class="tile">
        <div class="label">Phase</div>
        <div class="value">${step.name}</div>
      </div>
      <div class="tile">
        <div class="label">Thrust</div>
        <div class="value">${step.thrust}</div>
      </div>
      <div class="tile">
        <div class="label">Fuel Remaining</div>
        <div class="value">${step.fuel}</div>
      </div>
      <div class="tile">
        <div class="label">Altitude</div>
        <div class="value">${step.altitude}</div>
      </div>
      <div class="tile">
        <div class="label">Velocity</div>
        <div class="value accent">${step.velocity}</div>
      </div>
    `;

    const firing = index === 1 || index === 2;
    diagram.classList.toggle("is-firing", firing);
  }

  // Manual step selection
  timelineButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.getAttribute("data-rocket-step") || "0");
      timelineButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderStep(idx);
    });
  });

  // Auto play
  playBtn.addEventListener("click", () => {
    let idx = 0;
    renderStep(idx);
    timelineButtons.forEach((b) => b.classList.remove("active"));
    timelineButtons[0]?.classList.add("active");

    appendLog("Rocket Simulation", "Playing conceptual launch sequence.");

    const interval = setInterval(() => {
      idx += 1;
      if (idx >= steps.length) {
        clearInterval(interval);
        diagram.classList.remove("is-firing");
        return;
      }
      renderStep(idx);
      timelineButtons.forEach((b) => b.classList.remove("active"));
      const activeBtn = document.querySelector(`[data-rocket-step="${idx}"]`);
      activeBtn && activeBtn.classList.add("active");
    }, 1700);

    // Fire the backend-powered mission simulation
    //triggerMissionSimulation();
  });

  // Initial state
  renderStep(0);
}

async function triggerMissionSimulation() {
  try {
    console.log("Successfully entered the triggerMissionSimulation() function.");
    console.log("Sending request to the backend API to launch mission simulation.");
    const response = await fetch("http://localhost:5000/api/run-sih7");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    appendLog(
      "Mission Launcher",
      payload?.message || "Triggered SIH_Seventh mission simulation."
    );
  } catch (error) {
    appendLog(
      "Mission Launcher",
      `Failed to trigger SIH_Seventh simulation: ${error.message}`
    );
    console.error("Mission simulation trigger failed:", error);
  }
}

async function triggerDebrisScanSimulation() {
  try {
    const response = await fetch("http://localhost:5000/api/run-sih12");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    appendLog(
      "Debris Scan",
      payload?.message || "Triggered SIH_Twelfth debris scan simulation."
    );
  } catch (error) {
    appendLog(
      "Debris Scan",
      `Failed to trigger SIH_Twelfth simulation: ${error.message}`
    );
    console.error("Debris scan simulation trigger failed:", error);
  }
}

async function triggerTrackSimulation(objectId) {
  try {
    const response = await fetch("http://localhost:5000/api/run-sih5");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    appendLog(
      "Track Debris",
      payload?.message || `Triggered SIH_Fifth tracking simulation for ${objectId}.`
    );
  } catch (error) {
    appendLog(
      "Track Debris",
      `Failed to trigger SIH_Fifth simulation: ${error.message}`
    );
    console.error("Track simulation trigger failed:", error);
  }
}

async function triggerDeorbitSimulation(altitude, mass, cd) {
  try {
    const response = await fetch("http://localhost:5000/api/run-sih10");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    
    // Update the Orbital Safety Index based on the simulation results from SIH_Tenth.py
    const safetyIndexElement = document.querySelector('.panel-row .panel-card:nth-child(2) .panel-value');
    if (safetyIndexElement && payload.output) {
        // Parse the output from SIH_Tenth.py to extract safety metrics
        try {
            // The payload.output contains the JSON string printed by SIH_Tenth.py
            const outputLines = payload.output.split('\n');
            let safetyData = null;
            
            // Find the JSON line in the output
            for (const line of outputLines) {
                if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
                    safetyData = JSON.parse(line.trim());
                    break;
                }
            }
            
            if (safetyData && safetyData.debris_count !== undefined) {
                const debrisCount = safetyData.debris_count;
                
                if (debrisCount >= 15) {
                    safetyIndexElement.textContent = 'High Risk';
                    safetyIndexElement.className = 'panel-value value-bad'; // Red text
                } else if (debrisCount >= 8) {
                    safetyIndexElement.textContent = 'Moderate Risk';
                    safetyIndexElement.className = 'panel-value value-warn'; // Yellow/orange text
                } else if (debrisCount >= 3) {
                    safetyIndexElement.textContent = 'Low Risk';
                    safetyIndexElement.className = 'panel-value value-medium'; // Amber text
                } else {
                    safetyIndexElement.textContent = 'All Green';
                    safetyIndexElement.className = 'panel-value value-good'; // Green text
                }
            }
        } catch (parseError) {
            console.error('Error parsing safety data from SIH_Tenth.py output:', parseError);
        }
    }
    
    appendLog(
      "Deorbit Simulation",
      payload?.message ||
        `Triggered SIH_Tenth deorbit simulation for ${altitude.toFixed(0)} km.`
    );
  } catch (error) {
    appendLog(
      "Deorbit Simulation",
      `Failed to trigger SIH_Tenth simulation: ${error.message}`
    );
    console.error("Deorbit simulation trigger failed:", error);
  }
}

async function triggerDashboardSimulation() {
  try {
    const response = await fetch("http://localhost:5000/api/run-sih8");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    appendLog(
      "Dashboard",
      payload?.message || "Triggered SIH_Eighth rocket simulation."
    );
  } catch (error) {
    appendLog(
      "Dashboard",
      `Failed to trigger SIH_Eighth simulation: ${error.message}`
    );
    console.error("Dashboard simulation trigger failed:", error);
  }
}

// ========== MISSION LOG ==========
let missionLogStream;
function initMissionLog() {
  missionLogStream = document.getElementById("mission-log-stream");
  const clearBtn = document.getElementById("btn-clear-log");
  if (!missionLogStream) return;

  clearBtn &&
    clearBtn.addEventListener("click", () => {
      missionLogStream.innerHTML = "";
    });

  // Seed with a few demo messages
  appendLog("System", "Mission control prototype initialized.");
  appendLog("Telemetry", "All simulated subsystems nominal.");
}

function appendLog(source, message) {
  if (!missionLogStream) return;
  const entry = document.createElement("div");
  entry.className = "mission-log-entry";
  const time = new Date().toISOString().substring(11, 19);
  entry.innerHTML = `<span class="time">${time}</span>[${source}] ${message}`;
  missionLogStream.appendChild(entry);
  missionLogStream.scrollTop = missionLogStream.scrollHeight;
}

// ========== SYSTEM DIAGNOSTICS ==========
function initDiagnostics() {
  const core = document.getElementById("core-systems-list");
  const sensor = document.getElementById("sensor-systems-list");
  const pipeline = document.getElementById("pipeline-systems-list");
  if (!core || !sensor || !pipeline) return;

  const coreItems = [
    { name: "Orbit Propagator Cluster", status: "good" },
    { name: "Conjunction Engine", status: "good" },
    { name: "Mission Database", status: "good" },
    { name: "Auth & Access Control", status: "good" },
  ];

  const sensorItems = [
    { name: "Ground Radar Network", status: "good" },
    { name: "Space-based Optical", status: "warn" },
    { name: "Laser Ranging Stations", status: "good" },
    { name: "GNSS Receivers", status: "good" },
  ];

  const pipelineItems = [
    { name: "TLE Ingest", status: "good" },
    { name: "Telemetry Stream", status: "warn" },
    { name: "Analytics & ML Models", status: "good" },
    { name: "External APIs", status: "bad" },
  ];

  function renderStatus(listEl, items) {
    listEl.innerHTML = items
      .map(
        (item) => `
      <li>
        <span class="status-label">${item.name}</span>
        <span class="status-indicator ${item.status}"></span>
      </li>`
      )
      .join("");
  }

  renderStatus(core, coreItems);
  renderStatus(sensor, sensorItems);
  renderStatus(pipeline, pipelineItems);
}