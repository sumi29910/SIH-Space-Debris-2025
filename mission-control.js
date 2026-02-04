// Advanced interactive behavior for Orbital Nexus Mission Control
// Enhanced with real-time data visualization, API integration, and game-like dynamics

// ========== GAME SYSTEM ==========
class MissionControlGame {
  constructor() {
    this.score = 0;
    this.missionsCompleted = 0;
    this.debrisNeutralized = 0;
    this.particles = [];
    this.lastUpdate = Date.now();
  }

  addScore(points, reason = "") {
    this.score += points;
    this.updateScoreDisplay();
    this.createParticle(`+${points}`, reason);
  }

  updateScoreDisplay() {
    const scoreEl = document.getElementById("mc-score");
    if (scoreEl) {
      scoreEl.textContent = this.score.toLocaleString();
      scoreEl.style.transform = "scale(1.15)";
      setTimeout(() => {
        scoreEl.style.transform = "scale(1)";
      }, 200);
    }
  }

  createParticle(text, reason = "") {
    this.particles.push({
      x: Math.random() * window.innerWidth,
      y: 100 + Math.random() * 200,
      text: text,
      reason: reason,
      life: 100,
      vy: -2,
      vx: (Math.random() - 0.5) * 2,
    });
  }

  updateParticles() {
    this.particles = this.particles.filter(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.life--;
      return p.life > 0;
    });
  }
}

// Function to handle SIH_Sixth.py execution
async function runOrbitVisualizer() {
  try {
    const response = await fetch('/api/run-sih6');
    const data = await response.json();
    
    if (data.success) {
      appendLog("Orbit visualizer launched successfully.");
      mcGame.addScore(300, "Orbit Visualizer Launched");
    } else {
      appendLog(`Orbit visualizer failed: ${data.error}`);
    }
  } catch (error) {
    appendLog(`Orbit visualizer error: ${error.message}`);
  }
}

const mcGame = new MissionControlGame();

document.addEventListener("DOMContentLoaded", () => {
  const yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  // Create game HUD
  createMCHUD();
  
  // Start game loop
  gameLoop();

  // Mobile nav toggle
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });

    navLinks.addEventListener("click", (e) => {
      if (e.target.tagName === "A") {
        navLinks.classList.remove("open");
      }
    });
  }

  // Debris Scan - Enhanced with API integration
  const btnStartScan = document.getElementById("btnStartScan");
  const scanOutput = document.getElementById("scanOutput");
  if (btnStartScan && scanOutput) {
    btnStartScan.addEventListener("click", async () => {
      btnStartScan.style.transform = "scale(0.95)";
      setTimeout(() => {
        btnStartScan.style.transform = "scale(1)";
      }, 150);
      
      scanOutput.innerHTML = "<p>Initiating orbital debris scan...</p>";
      mcGame.addScore(50, "Scan Initiated");
      
      try {
        const response = await fetch('/api/run-sih12'); // Run SIH_Twelfth.py orbital debris scan
        const data = await response.json();
        if (data.success) {
          scanOutput.innerHTML = `
            <p><strong>Orbital debris scan complete.</strong></p>
            <p>Detected debris objects in real-time.</p>
            <p>Processing results from radar simulation...</p>
          `;
          mcGame.addScore(200, "Scan Complete");
          appendLog("Debris scan completed successfully.");
        } else {
          scanOutput.innerHTML = `<p><strong>Scan failed:</strong> ${data.error}</p>`;
          appendLog(`Debris scan failed: ${data.error}`);
        }
      } catch (error) {
        scanOutput.innerHTML = `<p><strong>Scan error:</strong> ${error.message}</p>`;
        appendLog(`Debris scan error: ${error.message}`);
      }
    });
  }

  // Track Debris table - Enhanced with API integration
  const debrisTableBody = document.getElementById("debrisTableBody");
  if (debrisTableBody) {
    // Function to update debris table with real data
    const updateDebrisTable = async () => {
      try {
        // Simulate fetching real data from backend
        const sample = [
          { id: "DEB-1124A", alt: 575, inc: 97.6, vel: 7.4, risk: "High" },
          { id: "DEB-2199C", alt: 810, inc: 52.1, vel: 7.2, risk: "Medium" },
          { id: "DEB-3301F", alt: 420, inc: 41.3, vel: 7.7, risk: "Low" },
          { id: "DEB-4478K", alt: 640, inc: 63.2, vel: 7.5, risk: "Medium" },
          { id: "DEB-5582L", alt: 720, inc: 65.4, vel: 7.3, risk: "High" },
          { id: "DEB-6693M", alt: 380, inc: 51.7, vel: 7.6, risk: "Low" }
        ];
        debrisTableBody.innerHTML = sample
          .map(
            (d) => `
            <tr class="${d.risk.toLowerCase()}">
              <td>${d.id}</td>
              <td>${d.alt}</td>
              <td>${d.inc}</td>
              <td>${d.vel.toFixed(2)}</td>
              <td><span class="risk-${d.risk.toLowerCase()}">${d.risk}</span></td>
            </tr>`
          )
          .join("");
      } catch (error) {
        console.error('Error updating debris table:', error);
      }
    };
    
    updateDebrisTable();
    // Update every 30 seconds
    setInterval(updateDebrisTable, 30000);
  }

  // Orbit visualizer controls - Enhanced with real-time visualization
  const altitudeRange = document.getElementById("altitudeRange");
  const altitudeValue = document.getElementById("altitudeValue");
  const inclinationRange = document.getElementById("inclinationRange");
  const inclinationValue = document.getElementById("inclinationValue");
  const orbitSummary = document.getElementById("orbitSummary");
  const liveOrbitScene = document.getElementById("liveOrbitScene");
  if (
    altitudeRange &&
    altitudeValue &&
    inclinationRange &&
    inclinationValue &&
    orbitSummary &&
    liveOrbitScene
  ) {
    const updateOrbitVisualizer = () => {
      const alt = Number(altitudeRange.value);
      const inc = Number(inclinationRange.value);
      altitudeValue.textContent = `${alt} km`;
      inclinationValue.textContent = `${inc}°`;

      let regime = "LEO";
      if (alt > 200) regime = "HEO";
      else if (alt > 1400) regime = "MEO";

      orbitSummary.textContent = `Circular ${regime} preview — altitude ${alt} km, inclination ${inc}°.`;
      
      // Update orbit visualization based on parameters
      const orbitElement = liveOrbitScene.querySelector('.orbit-visual');
      if (orbitElement) {
        // Update orbit inclination visual effect
        orbitElement.style.transform = `rotateX(${inc}deg)`;
        // Update orbit size based on altitude
        orbitElement.style.width = `${80 + (alt/25)}%`;
        orbitElement.style.height = `${60 + (alt/35)}%`;
      }
    };
    altitudeRange.addEventListener("input", updateOrbitVisualizer);
    inclinationRange.addEventListener("input", updateOrbitVisualizer);
    updateOrbitVisualizer();
  }

  // Collision list - Enhanced with API integration
 const collisionList = document.getElementById("collisionList");
  if (collisionList) {
    const updateCollisionList = async () => {
      try {
        // In a real system, this would fetch from a collision prediction API
        const items = [
          "T+03:12: Object DEB-219C miss distance 430 m (Medium).",
          "T+09:47: Object DEB-1124A miss distance 190 m (High).",
          "T+18:22: Object DEB-3301F miss distance 2.3 km (Low).",
          "T+24:15: Object DEB-5582L miss distance 650 m (Medium)."
        ];
        collisionList.innerHTML = items
          .map((t) => `<li>${t}</li>`)
          .join("");
      } catch (error) {
        console.error('Error updating collision list:', error);
      }
    };
    
    updateCollisionList();
    // Update every 45 seconds
    setInterval(updateCollisionList, 45000);
  }

  // Launch simulation - Enhanced with API integration
 const btnLaunch = document.getElementById("btnLaunch");
  const rocket = document.querySelector(".rocket");
  const launchTelemetry = document.getElementById("launchTelemetry");
  if (btnLaunch && rocket && launchTelemetry) {
    btnLaunch.addEventListener("click", async () => {
      if (rocket.classList.contains("launching")) return;
      rocket.classList.add("launching");
      launchTelemetry.innerHTML = "<p>T-0: Main engine ignition. Thrust at 10% rated.</p>";
      appendLog("Launch simulation initiated.");
      
      try {
        // Call the launch simulation API
        const response = await fetch('/api/run-sih7'); // ISRO rocket simulation
        const data = await response.json();
        if (data.success) {
          appendLog("Launch simulation completed successfully.");
        } else {
          appendLog(`Launch simulation failed: ${data.error}`);
        }
      } catch (error) {
        appendLog(`Launch simulation error: ${error.message}`);
      }
      
      setTimeout(() => {
        launchTelemetry.innerHTML += "<p>+58 s: Max-Q passed. Thrust throttling nominal.</p>";
      }, 700);
      setTimeout(() => {
        launchTelemetry.innerHTML += "<p>+150 s: Stage 1 separation. Stage 2 ignition.</p>";
      }, 1500);
      setTimeout(() => {
        launchTelemetry.innerHTML += "<p>+540 s: Stage 3 cutoff. Payload in transfer orbit.</p>";
      }, 2600);
      setTimeout(() => {
        launchTelemetry.innerHTML += "<p>+900 s: Circularization complete. Mission in target orbit.</p>";
        rocket.classList.remove("launching");
        mcGame.missionsCompleted++;
        mcGame.addScore(500, "Launch Success");
        document.getElementById("mc-missions").textContent = mcGame.missionsCompleted;
      }, 3800);
    });
  }

  // Laser Ablation controls - Enhanced with real-time calculations
  const laserEnergy = document.getElementById("laserEnergy");
  const laserEnergyValue = document.getElementById("laserEnergyValue");
  const laserDuration = document.getElementById("laserDuration");
  const laserDurationValue = document.getElementById("laserDurationValue");
  const laserSummary = document.getElementById("laserSummary");
  if (
    laserEnergy &&
    laserEnergyValue &&
    laserDuration &&
    laserDurationValue &&
    laserSummary
 ) {
    const updateLaser = () => {
      const e = Number(laserEnergy.value);
      const t = Number(laserDuration.value);
      laserEnergyValue.textContent = `${e} kJ`;
      laserDurationValue.textContent = `${t} s`;
      const dv = (e * t) / 10000; // fake scaling
      laserSummary.textContent = `Conceptual estimate: cumulative delta‑v ≈ ${dv.toFixed(
        2
      )} m/s over the pass. Enough to gradually alter perigee over multiple engagements.`;
    };
    laserEnergy.addEventListener("input", updateLaser);
    laserDuration.addEventListener("input", updateLaser);
    updateLaser();
  }

  // Mission log stream - Enhanced with API integration
  const missionLogStream = document.getElementById("missionLogStream");
  const btnAddManualLog = document.getElementById("btnAddManualLog");

  const appendLog = (msg) => {
    if (!missionLogStream) return;
    const line = document.createElement("div");
    line.className = "mission-log-line";
    const ts = new Date().toLocaleTimeString();
    line.textContent = `[${ts}] ${msg}`;
    missionLogStream.appendChild(line);
    missionLogStream.scrollTop = missionLogStream.scrollHeight;
 };

  if (missionLogStream) {
    appendLog("Mission console initialized. Awaiting operator input.");
    // Simulate periodic system messages
    setInterval(() => {
      const messages = [
        "Debris scan scheduler heartbeat nominal.",
        "Orbit propagator cycle complete.",
        "Diagnostics sync with metrics backend.",
        "Mission log rotation checkpoint reached.",
        "Telemetry data stream active.",
        "Ground station communication nominal."
      ];
      const msg = messages[Math.floor(Math.random() * messages.length)];
      appendLog(msg);
    }, 6500);
  }

  if (btnAddManualLog) {
    btnAddManualLog.addEventListener("click", () => {
      appendLog("Operator note: Manual status check recorded.");
    });
  }

  // Diagnostics - Enhanced with real-time API data
  const diagCpu = document.getElementById("diagCpu");
  const diagLatency = document.getElementById("diagLatency");
  const diagDb = document.getElementById("diagDb");
  const diagAlert = document.getElementById("diagAlert");

  const updateDiagnostics = async () => {
    if (!diagCpu || !diagLatency || !diagDb || !diagAlert) return;
    try {
      // In a real system, this would fetch from a diagnostics API
      const cpu = 35 + Math.round(Math.random() * 30);
      const latency = 120 + Math.round(Math.random() * 120);
      const db = (10 + Math.random() * 8).toFixed(1);

      diagCpu.textContent = `${cpu}%`;
      diagLatency.textContent = `${latency} ms`;
      diagDb.textContent = `${db} k ops/s`;
      diagAlert.textContent = cpu > 60 || latency > 220 ? "Elevated" : "Nominal";
      
      // Update alert level color based on status
      diagAlert.style.color = cpu > 60 || latency > 220 ? "#f97316" : "#4ade80";
    } catch (error) {
      console.error('Error updating diagnostics:', error);
    }
 };

  updateDiagnostics();
  setInterval(updateDiagnostics, 5000);
  
  // Add risk level styling and game animations
  const style = document.createElement('style');
  style.textContent = `
    .high { background-color: rgba(249, 115, 22, 0.15) !important; }
    .medium { background-color: rgba(251, 191, 36, 0.15) !important; }
    .low { background-color: rgba(74, 222, 128, 0.15) !important; }
    .risk-high { color: #f97316; font-weight: bold; animation: pulse 2s ease-in-out infinite; }
    .risk-medium { color: #fbbf24; font-weight: bold; }
    .risk-low { color: #4ade80; font-weight: bold; }
    
    #mc-game-hud {
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 1000;
      background: rgba(11, 16, 51, 0.95);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(29, 214, 255, 0.3);
      border-radius: 12px;
      padding: 16px;
      min-width: 180px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }
    
    .mc-hud-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .mc-hud-item:last-child {
      border-bottom: none;
    }
    
    .mc-hud-label {
      font-size: 11px;
      text-transform: uppercase;
      color: #9ca3af;
    }
    
    .mc-hud-value {
      font-size: 18px;
      font-weight: 700;
      color: #1dd6ff;
      transition: transform 0.2s ease;
    }
    
    #particle-canvas {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 9999;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }
  `;
document.head.appendChild(style);

// Add event listener to the "Plan a Mission" button to run SIH_Sixth.py
const planMissionButtons = document.querySelectorAll('a[href="#mission-planner"].btn.ghost');
planMissionButtons.forEach(button => {
  button.addEventListener('click', async (e) => {
    // Prevent default behavior if needed
    // e.preventDefault();
    
    // Add visual feedback
    button.style.transform = "scale(0.95)";
    setTimeout(() => {
      button.style.transform = "scale(1)";
    }, 150);
    
    // Run the SIH_Sixth.py script
    await runOrbitVisualizer();
  });
});
});

// ========== GAME HUD & LOOP ==========
function createMCHUD() {
  const hud = document.createElement("div");
  hud.id = "mc-game-hud";
  hud.innerHTML = `
    <div class="mc-hud-item">
      <span class="mc-hud-label">Score</span>
      <span class="mc-hud-value" id="mc-score">0</span>
    </div>
    <div class="mc-hud-item">
      <span class="mc-hud-label">Missions</span>
      <span class="mc-hud-value" id="mc-missions">0</span>
    </div>
    <div class="mc-hud-item">
      <span class="mc-hud-label">Neutralized</span>
      <span class="mc-hud-value" id="mc-debris">0</span>
    </div>
  `;
  document.body.appendChild(hud);
}

function gameLoop() {
  mcGame.updateParticles();
  renderMCParticles();
  requestAnimationFrame(gameLoop);
}

function renderMCParticles() {
  let canvas = document.getElementById("particle-canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "particle-canvas";
    document.body.appendChild(canvas);
  }
  
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  mcGame.particles.forEach(p => {
    const alpha = p.life / 100;
    ctx.fillStyle = `rgba(29, 214, 255, ${alpha})`;
    ctx.font = "bold 20px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(p.text, p.x, p.y);
  });
}
