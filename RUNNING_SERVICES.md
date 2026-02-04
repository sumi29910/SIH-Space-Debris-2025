# 🚀 Application Running Status

## ✅ **Services Currently Running**

### 1. **Streamlit Dashboard** 
- **Status**: ✅ RUNNING
- **URL**: http://localhost:8501
- **Module**: SIH_Third.py
- **Features**: 
  - Real-time debris detection logs
  - Risk assessment charts
  - Data visualization
  - Auto-refresh every 5 seconds

### 2. **Flask Web Server**
- **Status**: ✅ RUNNING  
- **URL**: http://localhost:5000
- **Module**: web_server.py
- **Endpoints**:
  - `/` - Main page
  - `/mission-simulation` - ISRO Mission Simulation
  - `/api/run-sih7` - API to run SIH_Seventh.py

---

## 🌐 **How to Access**

### **Option 1: Streamlit Dashboard (Recommended)**
1. Open your web browser
2. Navigate to: **http://localhost:8501**
3. You'll see the Space Debris Monitor Dashboard
4. The dashboard auto-refreshes every 5 seconds

### **Option 2: Flask Web Server**
1. Open your web browser
2. Navigate to: **http://localhost:5000**
3. Click on "Mission Simulation" link
4. Or visit: **http://localhost:5000/mission-simulation**

### **Option 3: Mission Control UI (Static)**
1. Open `mission-control.html` directly in your browser
2. No server needed - it's a static HTML file
3. Features all mission control modules

---

## 🎮 **Additional Modules You Can Run**

### **Visualization Modules** (Run in separate terminals)
```bash
# Laser deflection simulation
python SIH_Fourth.py

# Advanced laser with predictive targeting
python SIH_Fifth.py

# Orbital transitions
python SIH_Sixth.py

# Rocket launch simulation
python SIH_Seventh.py
```

### **Detection Modules** (Requires webcam or video)
```bash
# Basic YOLO detection
python SIH_First.py

# Advanced tracking with risk assessment
python SIH_Second.py --mode simulate  # or --mode camera
```

---

## 📊 **What You Can Do Now**

### **In Streamlit Dashboard (http://localhost:8501)**
- View real-time detection logs
- See risk assessment charts
- Monitor debris tracking data
- Upload videos for analysis (if logs exist)

### **In Flask Server (http://localhost:5000)**
- View mission simulation interface
- Run ISRO rocket launch simulation
- Access simulation API endpoints

### **In Mission Control UI (mission-control.html)**
- Debris scanning
- Orbit visualization
- Collision prediction
- Mission planning
- Laser ablation simulation
- System diagnostics

---

## 🛑 **To Stop Services**

Press `Ctrl+C` in the terminal windows where the services are running, or close the terminal windows.

---

## 📝 **Notes**

- **Streamlit** runs on port **8501** by default
- **Flask** runs on port **5000** by default
- Both services are running in the background
- You can run visualization modules in separate terminal windows
- Detection modules require a webcam or video file to function

---

**Status**: ✅ **ALL SERVICES RUNNING**

Enjoy exploring the Space Debris Detection System!

