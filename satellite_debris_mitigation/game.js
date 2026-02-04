// ========== GAME SYSTEM ==========
class GameSystem {
  constructor() {
    this.score = 0;
    this.level = 1;
    this.debrisDestroyed = 0;
    this.scansCompleted = 0;
    this.trackedObjects = 0;
    this.successCount = 0;
    this.totalAttempts = 0;
    this.achievements = new Set();
    this.particles = [];
    this.debrisList = [];
    this.scanning = false;
    this.selectedTarget = null;
  }

  addScore(points, reason = "") {
    this.score += points;
    this.updateScoreDisplay();
    this.createParticle(`+${points}`, reason);
    this.checkLevelUp();
    this.checkAchievements();
  }

  updateScoreDisplay() {
    const scoreEl = document.getElementById("game-score");
    if (scoreEl) {
      scoreEl.textContent = this.score.toLocaleString();
      scoreEl.style.transform = "scale(1.15)";
      scoreEl.style.color = "#00ff88";
      setTimeout(() => {
        scoreEl.style.transform = "scale(1)";
        scoreEl.style.color = "#00ff88";
      }, 300);
    }
  }

  createParticle(text, reason = "") {
    this.particles.push({
      x: Math.random() * window.innerWidth * 0.5 + window.innerWidth * 0.25,
      y: Math.random() * window.innerHeight * 0.3 + 100,
      text: text,
      reason: reason,
      life: 120,
      vy: -3,
      vx: (Math.random() - 0.5) * 4,
      size: 24,
    });
  }

  checkLevelUp() {
    const newLevel = Math.floor(this.score / 5000) + 1;
    if (newLevel > this.level) {
      this.level = newLevel;
      this.updateLevelDisplay();
      appendLog("System", `Mission level upgraded to ${this.level}`);
    }
  }

  updateLevelDisplay() {
    const levelEl = document.getElementById("game-level");
    if (levelEl) {
      levelEl.textContent = this.level;
      levelEl.style.animation = "pulse 0.5s ease";
      setTimeout(() => {
        levelEl.style.animation = "";
      }, 500);
    }
  }

  checkAchievements() {
    // Achievements are tracked silently without notifications
    // They can be checked for mission milestones but no UI display
  }

  updateParticles() {
    this.particles = this.particles.filter(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.life--;
      p.vx *= 0.98;
      return p.life > 0;
    });
  }

  updateAccuracy() {
    const accuracy = this.totalAttempts > 0 
      ? Math.round((this.successCount / this.totalAttempts) * 100)
      : 100;
    
    const accuracyEl = document.getElementById("game-accuracy");
    if (accuracyEl) {
      accuracyEl.textContent = `${accuracy}%`;
      accuracyEl.style.color = accuracy >= 80 ? "#00ff88" : accuracy >= 60 ? "#ff6b35" : "#ff3366";
    }
  }
}

// Initialize Game System
const game = new GameSystem();

// ========== DMSAT SATELLITE SYSTEM ==========
class DMSATSatellite {
  constructor() {
    this.altitude = 550; // km - LEO operational altitude
    this.inclination = 97.6; // degrees - sun-synchronous orbit
    this.velocity = 7.58; // km/s
    this.missionStartTime = Date.now();
    this.powerLevel = 85; // percentage
    this.operational = true;
    this.currentMode = "standby"; // standby, scanning, tracking, engaging
    this.position = { x: 0, y: 0, angle: 0 };
  }

  update() {
    // Update satellite telemetry with realistic variations
    this.altitude = 550 + Math.sin(Date.now() * 0.0001) * 0.5; // Small altitude variations
    this.velocity = 7.58 + Math.sin(Date.now() * 0.00015) * 0.01; // Velocity variations
    this.powerLevel = Math.max(75, Math.min(95, this.powerLevel + (Math.random() - 0.5) * 0.5));
    
    // Update orbital position
    this.position.angle += 0.0002; // Slow rotation for orbital motion
    this.position.x = Math.cos(this.position.angle) * 150;
    this.position.y = Math.sin(this.position.angle) * 100;
    
    this.updateDisplay();
  }

  updateDisplay() {
    const missionTime = Date.now() - this.missionStartTime;
    const hours = Math.floor(missionTime / 3600000);
    const minutes = Math.floor((missionTime % 3600000) / 60000);
    const seconds = Math.floor((missionTime % 60000) / 1000);
    
    const timeEl = document.getElementById("dmsat-time");
    if (timeEl) {
      timeEl.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    const altEl = document.getElementById("dmsat-altitude");
    if (altEl) {
      altEl.textContent = `${this.altitude.toFixed(1)} km`;
    }
    
    const incEl = document.getElementById("dmsat-inclination");
    if (incEl) {
      incEl.textContent = `${this.inclination.toFixed(1)}°`;
    }
    
    const velEl = document.getElementById("dmsat-velocity");
    if (velEl) {
      velEl.textContent = `${this.velocity.toFixed(2)} km/s`;
    }
    
    const powerEl = document.getElementById("dmsat-power");
    if (powerEl) {
      powerEl.textContent = `${Math.round(this.powerLevel)}%`;
      powerEl.style.color = this.powerLevel > 80 ? "#00ff88" : this.powerLevel > 60 ? "#ff6b35" : "#ff3366";
    }
  }

  setMode(mode) {
    this.currentMode = mode;
    appendLog("DMSAT", `Switched to ${mode} mode`);
  }
}

const dmsat = new DMSATSatellite();
setInterval(() => dmsat.update(), 1000);

// ========== CANVAS SETUP ==========
const scanCanvas = document.getElementById("scan-canvas");
const trackCanvas = document.getElementById("track-canvas");
const mitigateCanvas = document.getElementById("mitigate-canvas");
const particleCanvas = document.getElementById("particle-canvas");

const scanCtx = scanCanvas.getContext("2d");
const trackCtx = trackCanvas.getContext("2d");
const mitigateCtx = mitigateCanvas.getContext("2d");
const particleCtx = particleCanvas.getContext("2d");

function resizeCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  const ctx = canvas.getContext("2d");
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
}

function resizeAllCanvases() {
  resizeCanvas(scanCanvas);
  resizeCanvas(trackCanvas);
  resizeCanvas(mitigateCanvas);
  resizeCanvas(particleCanvas);
}

window.addEventListener("resize", resizeAllCanvases);
resizeAllCanvases();

// ========== PARTICLE SYSTEM ==========
function renderParticles() {
  const rect = particleCanvas.getBoundingClientRect();
  particleCtx.clearRect(0, 0, rect.width, rect.height);
  particleCtx.scale(1, 1);
  
  game.particles.forEach(p => {
    const alpha = p.life / 120;
    particleCtx.globalAlpha = alpha;
    particleCtx.fillStyle = "#00ff88";
    particleCtx.font = `bold ${p.size}px Orbitron`;
    particleCtx.textAlign = "center";
    particleCtx.fillText(p.text, p.x, p.y);
    
    if (p.reason) {
      particleCtx.font = "12px Inter";
      particleCtx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.7})`;
      particleCtx.fillText(p.reason, p.x, p.y + 20);
    }
  });
  
  particleCtx.globalAlpha = 1;
  game.updateParticles();
  requestAnimationFrame(renderParticles);
}
renderParticles();

// ========== NAVIGATION ==========
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const section = btn.dataset.section;
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".game-section").forEach(s => s.classList.remove("active"));
    
    btn.classList.add("active");
    document.getElementById(`${section}-section`).classList.add("active");
  });
});

// ========== SCAN SYSTEM ==========
let scanAnimationId = null;
let scanDebris = [];

function generateDebris(count) {
  const debris = [];
  for (let i = 0; i < count; i++) {
    debris.push({
      id: `DEB-${Math.floor(Math.random() * 90000 + 10000)}`,
      x: Math.random() * scanCanvas.width / window.devicePixelRatio,
      y: Math.random() * scanCanvas.height / window.devicePixelRatio,
      size: Math.random() * 5 + 2,
      angle: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.5 + 0.2,
      color: ["#00ff88", "#00d4ff", "#ff6b35", "#ff3366"][Math.floor(Math.random() * 4)],
      detected: false,
      risk: Math.random() > 0.7 ? "High" : Math.random() > 0.5 ? "Medium" : "Low",
    });
  }
  return debris;
}

function drawScanCanvas() {
  const rect = scanCanvas.getBoundingClientRect();
  scanCtx.clearRect(0, 0, rect.width, rect.height);
  
  // Draw background grid
  scanCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  scanCtx.lineWidth = 1;
  for (let i = 0; i < rect.width; i += 50) {
    scanCtx.beginPath();
    scanCtx.moveTo(i, 0);
    scanCtx.lineTo(i, rect.height);
    scanCtx.stroke();
  }
  for (let i = 0; i < rect.height; i += 50) {
    scanCtx.beginPath();
    scanCtx.moveTo(0, i);
    scanCtx.lineTo(rect.width, i);
    scanCtx.stroke();
  }
  
  // Draw DMSAT satellite at center
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  // Draw DMSAT satellite
  scanCtx.save();
  scanCtx.translate(centerX, centerY);
  scanCtx.rotate(Date.now() * 0.0001);
  
  // Satellite body
  scanCtx.fillStyle = "#00d4ff";
  scanCtx.shadowBlur = 15;
  scanCtx.shadowColor = "#00d4ff";
  scanCtx.fillRect(-20, -8, 40, 16);
  
  // Solar panels
  scanCtx.fillStyle = "#00ff88";
  scanCtx.fillRect(-25, -12, 5, 24);
  scanCtx.fillRect(20, -12, 5, 24);
  
  // Antenna
  scanCtx.fillStyle = "#ffffff";
  scanCtx.beginPath();
  scanCtx.arc(0, -12, 3, 0, Math.PI * 2);
  scanCtx.fill();
  
  scanCtx.restore();
  
  // Draw DMSAT label
  scanCtx.fillStyle = "#00d4ff";
  scanCtx.font = "bold 14px Orbitron";
  scanCtx.textAlign = "center";
  scanCtx.fillText("DMSAT", centerX, centerY + 40);
  
  // Draw scanning beam when active
  if (game.scanning) {
    scanCtx.strokeStyle = "rgba(0, 255, 136, 0.3)";
    scanCtx.lineWidth = 2;
    const sweepAngle = (Date.now() * 0.003) % (Math.PI * 2);
    scanCtx.beginPath();
    scanCtx.moveTo(centerX, centerY);
    scanCtx.lineTo(
      centerX + Math.cos(sweepAngle) * rect.width,
      centerY + Math.sin(sweepAngle) * rect.height
    );
    scanCtx.stroke();
  }
  
  // Draw debris
  scanDebris.forEach(debris => {
    if (debris.detected) {
      scanCtx.shadowBlur = 10;
      scanCtx.shadowColor = debris.color;
      scanCtx.fillStyle = debris.color;
      scanCtx.beginPath();
      scanCtx.arc(debris.x, debris.y, debris.size, 0, Math.PI * 2);
      scanCtx.fill();
      scanCtx.shadowBlur = 0;
      
      // Draw ID label
      scanCtx.fillStyle = "#ffffff";
      scanCtx.font = "10px Orbitron";
      scanCtx.fillText(debris.id, debris.x + debris.size + 5, debris.y);
    } else {
      scanCtx.fillStyle = "rgba(255, 255, 255, 0.2)";
      scanCtx.beginPath();
      scanCtx.arc(debris.x, debris.y, debris.size * 0.5, 0, Math.PI * 2);
      scanCtx.fill();
    }
    
    // Update position
    debris.x += Math.cos(debris.angle) * debris.speed;
    debris.y += Math.sin(debris.angle) * debris.speed;
    
    // Wrap around
    if (debris.x < 0) debris.x = rect.width;
    if (debris.x > rect.width) debris.x = 0;
    if (debris.y < 0) debris.y = rect.height;
    if (debris.y > rect.height) debris.y = 0;
  });
  
  if (game.scanning) {
    scanAnimationId = requestAnimationFrame(drawScanCanvas);
  }
}

document.getElementById("btn-start-scan").addEventListener("click", () => {
  if (game.scanning) return;
  
  game.scanning = true;
  dmsat.setMode("scanning");
  scanDebris = generateDebris(20 + game.level * 5);
  
  appendLog("DMSAT", "Initiating orbital debris scan...");
  
  // Detect debris progressively
  let detectedCount = 0;
  const detectInterval = setInterval(() => {
    if (detectedCount < scanDebris.length && game.scanning) {
      scanDebris[detectedCount].detected = true;
      detectedCount++;
      if (detectedCount % 5 === 0) {
        appendLog("DMSAT", `Detected ${detectedCount} debris objects...`);
      }
    } else {
      clearInterval(detectInterval);
    }
  }, 200);
  
  drawScanCanvas();
  
  // Update results
  setTimeout(() => {
    updateScanResults();
    game.scansCompleted++;
    document.getElementById("game-scans").textContent = game.scansCompleted;
    const highRiskCount = scanDebris.filter(d => d.risk === "High").length;
    game.addScore(100 + highRiskCount * 50, "Scan Complete");
    dmsat.setMode("standby");
    appendLog("DMSAT", `Scan complete. Detected ${detectedCount} objects, ${highRiskCount} high-risk.`);
  }, scanDebris.length * 200 + 1000);
});

document.getElementById("btn-stop-scan").addEventListener("click", () => {
  game.scanning = false;
  if (scanAnimationId) {
    cancelAnimationFrame(scanAnimationId);
  }
});

document.getElementById("scan-range").addEventListener("input", (e) => {
  document.getElementById("scan-range-value").textContent = `${e.target.value} km`;
});

function updateScanResults() {
  const resultsGrid = document.getElementById("scan-results");
  resultsGrid.innerHTML = scanDebris.filter(d => d.detected).map(debris => `
    <div class="result-item ${debris.risk.toLowerCase()}-risk">
      <div class="result-id">${debris.id}</div>
      <div class="result-info">Risk: <strong>${debris.risk}</strong></div>
      <div class="result-info">Size: ${debris.size.toFixed(1)}m</div>
      <div class="result-info">Status: Detected</div>
    </div>
  `).join("");
}

// ========== TRACK SYSTEM ==========
let trackedDebris = null;
let trackAnimationId = null;

function drawTrackCanvas() {
  const rect = trackCanvas.getBoundingClientRect();
  trackCtx.clearRect(0, 0, rect.width, rect.height);
  
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  // Draw DMSAT orbit (higher orbit)
  trackCtx.strokeStyle = "rgba(0, 212, 255, 0.5)";
  trackCtx.lineWidth = 2;
  trackCtx.setLineDash([5, 5]);
  trackCtx.beginPath();
  trackCtx.ellipse(centerX, centerY, 180, 120, 0, 0, Math.PI * 2);
  trackCtx.stroke();
  trackCtx.setLineDash([]);
  
  // Draw DMSAT satellite position
  const dmsatAngle = dmsat.position.angle;
  const dmsatX = centerX + Math.cos(dmsatAngle) * 180;
  const dmsatY = centerY + Math.sin(dmsatAngle) * 120;
  
  trackCtx.save();
  trackCtx.translate(dmsatX, dmsatY);
  trackCtx.rotate(dmsatAngle + Math.PI / 2);
  
  // DMSAT satellite
  trackCtx.fillStyle = "#00d4ff";
  trackCtx.shadowBlur = 10;
  trackCtx.shadowColor = "#00d4ff";
  trackCtx.fillRect(-15, -6, 30, 12);
  trackCtx.fillStyle = "#00ff88";
  trackCtx.fillRect(-18, -9, 4, 18);
  trackCtx.fillRect(14, -9, 4, 18);
  
  trackCtx.restore();
  
  // Draw DMSAT label
  trackCtx.fillStyle = "#00d4ff";
  trackCtx.font = "bold 12px Orbitron";
  trackCtx.textAlign = "center";
  trackCtx.fillText("DMSAT", dmsatX, dmsatY - 20);
  
  if (!trackedDebris) return;
  
  // Draw debris orbit (lower orbit)
  trackCtx.strokeStyle = "rgba(255, 107, 53, 0.3)";
  trackCtx.lineWidth = 2;
  trackCtx.beginPath();
  trackCtx.ellipse(centerX, centerY, 150, 100, 0, 0, Math.PI * 2);
  trackCtx.stroke();
  
  // Draw Earth
  trackCtx.fillStyle = "#1a4d7a";
  trackCtx.beginPath();
  trackCtx.arc(centerX, centerY, 30, 0, Math.PI * 2);
  trackCtx.fill();
  
  // Draw tracked debris object
  const angle = Date.now() * 0.001;
  const x = centerX + Math.cos(angle) * 150;
  const y = centerY + Math.sin(angle) * 100;
  
  trackCtx.shadowBlur = 15;
  trackCtx.shadowColor = "#ff6b35";
  trackCtx.fillStyle = "#ff6b35";
  trackCtx.beginPath();
  trackCtx.arc(x, y, 8, 0, Math.PI * 2);
  trackCtx.fill();
  trackCtx.shadowBlur = 0;
  
  // Draw connection line from DMSAT to debris
  trackCtx.strokeStyle = "rgba(255, 255, 255, 0.2)";
  trackCtx.lineWidth = 1;
  trackCtx.setLineDash([3, 3]);
  trackCtx.beginPath();
  trackCtx.moveTo(dmsatX, dmsatY);
  trackCtx.lineTo(x, y);
  trackCtx.stroke();
  trackCtx.setLineDash([]);
  
  // Draw trail
  trackCtx.strokeStyle = "rgba(255, 107, 53, 0.3)";
  trackCtx.lineWidth = 2;
  trackCtx.beginPath();
  for (let i = 0; i < 30; i++) {
    const trailAngle = angle - i * 0.05;
    const trailX = centerX + Math.cos(trailAngle) * 150;
    const trailY = centerY + Math.sin(trailAngle) * 100;
    if (i === 0) {
      trackCtx.moveTo(trailX, trailY);
    } else {
      trackCtx.lineTo(trailX, trailY);
    }
  }
  trackCtx.stroke();
  
  trackAnimationId = requestAnimationFrame(drawTrackCanvas);
}

document.getElementById("btn-track").addEventListener("click", () => {
  const trackId = document.getElementById("track-id").value || scanDebris[0]?.id;
  if (!trackId) {
    appendLog("DMSAT", "Error: No debris ID specified");
    return;
  }
  
  dmsat.setMode("tracking");
  trackedDebris = {
    id: trackId,
    altitude: (400 + Math.random() * 800).toFixed(0),
    inclination: (51 + Math.random() * 47).toFixed(1),
    period: (90 + Math.random() * 40).toFixed(1),
    velocity: (7.2 + Math.random() * 0.8).toFixed(2),
  };
  
  updateTelemetry();
  drawTrackCanvas();
  game.trackedObjects++;
  game.addScore(75, "Object Tracked");
  appendLog("DMSAT", `Tracking object ${trackId} - Altitude: ${trackedDebris.altitude} km`);
});

document.getElementById("btn-clear-track").addEventListener("click", () => {
  trackedDebris = null;
  if (trackAnimationId) {
    cancelAnimationFrame(trackAnimationId);
  }
  const rect = trackCanvas.getBoundingClientRect();
  trackCtx.clearRect(0, 0, rect.width, rect.height);
});

function updateTelemetry() {
  if (!trackedDebris) return;
  
  const telemetryGrid = document.getElementById("telemetry-data");
  telemetryGrid.innerHTML = `
    <div class="telemetry-item">
      <div class="telemetry-label">Object ID</div>
      <div class="telemetry-value">${trackedDebris.id}</div>
    </div>
    <div class="telemetry-item">
      <div class="telemetry-label">Altitude</div>
      <div class="telemetry-value">${trackedDebris.altitude} km</div>
    </div>
    <div class="telemetry-item">
      <div class="telemetry-label">Inclination</div>
      <div class="telemetry-value">${trackedDebris.inclination}°</div>
    </div>
    <div class="telemetry-item">
      <div class="telemetry-label">Period</div>
      <div class="telemetry-value">${trackedDebris.period} min</div>
    </div>
    <div class="telemetry-item">
      <div class="telemetry-label">Velocity</div>
      <div class="telemetry-value">${trackedDebris.velocity} km/s</div>
    </div>
  `;
}

// ========== MITIGATION SYSTEM ==========
let mitigationTargets = [];
let mitigationAnimationId = null;

function drawMitigateCanvas() {
  const rect = mitigateCanvas.getBoundingClientRect();
  mitigateCtx.clearRect(0, 0, rect.width, rect.height);
  
  // Draw background
  mitigateCtx.fillStyle = "rgba(0, 0, 0, 0.3)";
  mitigateCtx.fillRect(0, 0, rect.width, rect.height);
  
  // Draw DMSAT satellite at top center
  const dmsatX = rect.width / 2;
  const dmsatY = 80;
  
  mitigateCtx.save();
  mitigateCtx.translate(dmsatX, dmsatY);
  mitigateCtx.rotate(Date.now() * 0.0001);
  
  // DMSAT satellite
  mitigateCtx.fillStyle = "#00d4ff";
  mitigateCtx.shadowBlur = 15;
  mitigateCtx.shadowColor = "#00d4ff";
  mitigateCtx.fillRect(-25, -10, 50, 20);
  
  // Solar panels
  mitigateCtx.fillStyle = "#00ff88";
  mitigateCtx.fillRect(-30, -14, 6, 28);
  mitigateCtx.fillRect(24, -14, 6, 28);
  
  // Weapon system
  mitigateCtx.fillStyle = "#ff3366";
  mitigateCtx.beginPath();
  mitigateCtx.arc(0, 15, 8, 0, Math.PI * 2);
  mitigateCtx.fill();
  
  mitigateCtx.restore();
  
  // DMSAT label
  mitigateCtx.fillStyle = "#00d4ff";
  mitigateCtx.font = "bold 14px Orbitron";
  mitigateCtx.textAlign = "center";
  mitigateCtx.fillText("DMSAT", dmsatX, dmsatY + 45);
  
  // Draw targets
  mitigationTargets.forEach((target, index) => {
    const x = (index % 5) * (rect.width / 5) + rect.width / 10;
    const y = Math.floor(index / 5) * 120 + 200;
    
    if (target === game.selectedTarget) {
      mitigateCtx.strokeStyle = "#ff3366";
      mitigateCtx.lineWidth = 3;
      mitigateCtx.beginPath();
      mitigateCtx.arc(x, y, 40, 0, Math.PI * 2);
      mitigateCtx.stroke();
      
      // Draw targeting line from DMSAT to target
      mitigateCtx.strokeStyle = "rgba(255, 51, 102, 0.5)";
      mitigateCtx.lineWidth = 2;
      mitigateCtx.setLineDash([5, 5]);
      mitigateCtx.beginPath();
      mitigateCtx.moveTo(dmsatX, dmsatY);
      mitigateCtx.lineTo(x, y);
      mitigateCtx.stroke();
      mitigateCtx.setLineDash([]);
    }
    
    mitigateCtx.shadowBlur = 10;
    mitigateCtx.shadowColor = target.color;
    mitigateCtx.fillStyle = target.color;
    mitigateCtx.beginPath();
    mitigateCtx.arc(x, y, 15, 0, Math.PI * 2);
    mitigateCtx.fill();
    mitigateCtx.shadowBlur = 0;
    
    mitigateCtx.fillStyle = "#ffffff";
    mitigateCtx.font = "12px Orbitron";
    mitigateCtx.textAlign = "center";
    mitigateCtx.fillText(target.id, x, y + 50);
  });
  
  mitigationAnimationId = requestAnimationFrame(drawMitigateCanvas);
}

function generateMitigationTargets() {
  mitigationTargets = scanDebris.filter(d => d.detected && d.risk === "High").map(debris => ({
    id: debris.id,
    color: debris.color,
    x: Math.random() * mitigateCanvas.width / window.devicePixelRatio,
    y: Math.random() * mitigateCanvas.height / window.devicePixelRatio,
  }));
  
  updateTargetList();
  drawMitigateCanvas();
}

function updateTargetList() {
  const targetList = document.getElementById("target-list");
  targetList.innerHTML = mitigationTargets.map((target, index) => `
    <div class="target-item ${target === game.selectedTarget ? 'selected' : ''}" 
         data-index="${index}">
      ${target.id}
    </div>
  `).join("");
  
  document.querySelectorAll(".target-item").forEach(item => {
    item.addEventListener("click", () => {
      const index = parseInt(item.dataset.index);
      game.selectedTarget = mitigationTargets[index];
      updateTargetList();
      drawMitigateCanvas();
    });
  });
}

document.getElementById("btn-engage").addEventListener("click", () => {
  if (!game.selectedTarget) {
    appendLog("DMSAT", "Warning: No target selected");
    return;
  }
  
  const power = parseInt(document.getElementById("weapon-power").value);
  const weaponType = document.getElementById("weapon-type").value;
  game.totalAttempts++;
  
  dmsat.setMode("engaging");
  appendLog("DMSAT", `Engaging target ${game.selectedTarget.id} with ${weaponType} at ${power}% power...`);
  
  // Success based on power and level
  const success = Math.random() < (power / 100) * (0.65 + game.level * 0.05);
  
  setTimeout(() => {
    const targetId = game.selectedTarget?.id || 'unknown';
    
    if (success) {
      game.successCount++;
      game.debrisDestroyed++;
      document.getElementById("game-debris").textContent = game.debrisDestroyed;
      game.addScore(200 + power, "Target Neutralized");
      
      // Visual effect
      createExplosion(mitigateCanvas.width / 2, mitigateCanvas.height / 2);
      appendLog("DMSAT", `Target ${targetId} successfully neutralized`);
      dmsat.powerLevel -= 5; // Power consumption
      
      // Remove target
      mitigationTargets = mitigationTargets.filter(t => t !== game.selectedTarget);
      game.selectedTarget = null;
      updateTargetList();
    } else {
      game.addScore(Math.max(10, power - 20), "Miss");
      appendLog("DMSAT", `Engagement missed target ${targetId}. Adjusting parameters...`);
      dmsat.powerLevel -= 2; // Reduced power consumption for miss
    }
    
    dmsat.setMode("standby");
    game.updateAccuracy();
  }, 1500);
});

function createExplosion(x, y) {
  for (let i = 0; i < 20; i++) {
    game.particles.push({
      x: x,
      y: y,
      text: "💥",
      reason: "",
      life: 60,
      vy: (Math.random() - 0.5) * 10,
      vx: (Math.random() - 0.5) * 10,
      size: 20,
    });
  }
}

document.getElementById("weapon-power").addEventListener("input", (e) => {
  document.getElementById("weapon-power-value").textContent = `${e.target.value}%`;
});

// Generate targets when switching to mitigate section
document.querySelector('[data-section="mitigate"]').addEventListener("click", () => {
  if (mitigationTargets.length === 0) {
    generateMitigationTargets();
  }
});

// ========== DASHBOARD UPDATES ==========
function updateDashboard() {
  document.getElementById("stat-scans").textContent = game.scansCompleted;
  document.getElementById("stat-tracked").textContent = game.trackedObjects;
  document.getElementById("stat-neutralized").textContent = game.debrisDestroyed;
  const successRate = game.totalAttempts > 0 
    ? Math.round((game.successCount / game.totalAttempts) * 100)
    : 0;
  const successEl = document.getElementById("stat-success");
  if (successEl) {
    successEl.textContent = `${successRate}%`;
    successEl.style.color = successRate >= 80 ? "#00ff88" : successRate >= 60 ? "#ff6b35" : "#ff3366";
  }
}

setInterval(updateDashboard, 1000);

// ========== INITIALIZATION ==========
document.addEventListener("DOMContentLoaded", () => {
  updateDashboard();
  
  // Initialize mission log
  appendLog("System", "Mission control initialized. DMSAT satellite operational.");
  appendLog("DMSAT", `Satellite deployed at ${dmsat.altitude.toFixed(1)} km altitude`);
  appendLog("DMSAT", "All systems nominal. Ready for debris mitigation operations.");
});

function appendLog(source, message) {
  const missionLog = document.getElementById("mission-log");
  if (!missionLog) return;
  
  const entry = document.createElement("div");
  entry.className = "log-entry";
  const time = new Date().toLocaleTimeString();
  entry.innerHTML = `<span class="log-time">${time}</span><span class="log-source">[${source}]</span>${message}`;
  missionLog.insertBefore(entry, missionLog.firstChild);
  
  // Keep only last 50 entries
  while (missionLog.children.length > 50) {
    missionLog.removeChild(missionLog.lastChild);
  }
}

// Export appendLog for use in other sections
window.appendLog = appendLog;
