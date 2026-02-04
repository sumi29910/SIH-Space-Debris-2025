"""
Flask web server to run SIH_Seventh.py and serve visualizations
"""
from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
from pathlib import Path

app = Flask(__name__)

import sys
PYTHON_EXE = Path(sys.executable)
PROJECT_ROOT = Path(__file__).parent


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def execute_script(script_name, timeout=60):
    if not PYTHON_EXE.exists():
        return False, f"Python interpreter not found at {PYTHON_EXE}"

    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        return False, f"Script not found at {script_path}"

    # Set environment variable to indicate this is from the web server
    env = os.environ.copy()
    env['FROM_WEB_SERVER'] = '1'
    
    result = subprocess.run(
        [str(PYTHON_EXE), str(script_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env
    )

    if result.returncode != 0:
        return False, result.stderr or "Script exited with non-zero status."

    return True, result.stdout

@app.route('/')
def index():
    return "Space Debris Mission Control Server Running"

@app.route('/mission-simulation')
def mission_simulation():
    """
    Serve the ISRO Mission Simulation (SIH_Seventh.py)
    This will run the visualization and embed it in a web page
    """
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ISRO Mission Simulation - SIH_Seventh</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background-color: #0a0e27;
                color: #fff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .container {
                max-width: 100%;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #00c2ff;
            }
            .info {
                background-color: #142a4c;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                border: 1px solid #00c2ff;
            }
            .status {
                text-align: center;
                padding: 20px;
                background-color: #1a3a52;
                border-radius: 8px;
                margin: 20px 0;
            }
            .button-group {
                text-align: center;
                margin: 20px 0;
            }
            button {
                background-color: #00c2ff;
                color: #081931;
                border: none;
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 4px;
                cursor: pointer;
                margin: 0 10px;
                font-weight: 600;
            }
            button:hover {
                background-color: #00d9ff;
                transform: translateY(-2px);
            }
            .output {
                background-color: #0a0e27;
                border: 1px solid #00c2ff;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                min-height: 400px;
            }
            iframe {
                width: 100%;
                height: 600px;
                border: 1px solid #00c2ff;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 ISRO Mission Simulation</h1>
            <div class="info">
                <h3>Smooth Gravity Turn Launch Simulation</h3>
                <p>This is the output of SIH_Seventh.py - A realistic ISRO rocket launch simulation with:</p>
                <ul>
                    <li>Stage 1 vertical takeoff with fast ascent rate</li>
                    <li>Gravity turn maneuver for efficient orbital insertion</li>
                    <li>Stage 2 operation and orbital velocity achievement</li>
                    <li>Real-time telemetry and HUD display</li>
                </ul>
            </div>
            
            <div class="status">
                <h2>Simulation Status: ACTIVE</h2>
                <p id="status-message">Loading simulation... Please wait.</p>
            </div>
            
            <div class="button-group">
                <button onclick="startSimulation()">Start Simulation</button>
                <button onclick="window.close()">Close Window</button>
            </div>
            
            <div class="output">
                <h3>Live Simulation Viewer</h3>
                <p>Matplotlib visualization would render here. Running SIH_Seventh.py...</p>
                <iframe id="simulation-frame" src="about:blank"></iframe>
                <div id="simulation-log" style="margin-top: 20px; font-family: monospace; color: #00c2ff;">
                    Waiting for simulation to start...
                </div>
            </div>
        </div>
        
        <script>
            function startSimulation() {
                const logDiv = document.getElementById('simulation-log');
                const statusMsg = document.getElementById('status-message');
                
                logDiv.innerHTML = '[' + new Date().toLocaleTimeString() + '] Launching ISRO Mission Simulation...\\n';
                logDiv.innerHTML += '[' + new Date().toLocaleTimeString() + '] Loading rocket physics engine...\\n';
                logDiv.innerHTML += '[' + new Date().toLocaleTimeString() + '] Initializing visualization...\\n';
                logDiv.innerHTML += '[' + new Date().toLocaleTimeString() + '] LIFTOFF!\\n';
                
                statusMsg.textContent = 'Simulation in progress - Watch the visualization on the left';
                
                // Fetch the actual simulation data
                fetch('/api/run-sih7')
                    .then(response => response.json())
                    .then(data => {
                        logDiv.innerHTML += '[' + new Date().toLocaleTimeString() + '] Simulation completed\\n';
                        if (data.success) {
                            logDiv.innerHTML += 'Output: ' + data.message + '\\n';
                        }
                    })
                    .catch(err => {
                        logDiv.innerHTML += 'Error: ' + err.message + '\\n';
                    });
            }
            
            // Auto-start simulation on page load
            window.addEventListener('load', () => {
                setTimeout(startSimulation, 500);
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/run-sih7', methods=['GET', 'OPTIONS'])
def run_sih7():
    """
    API endpoint to run SIH_Seventh.py using the specified interpreter
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Seventh.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Seventh.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/run-sih12', methods=['GET', 'OPTIONS'])
def run_sih12():
    """
    API endpoint to run SIH_Twelfth.py
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Twelfth.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Twelfth.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/run-sih5', methods=['GET', 'OPTIONS'])
def run_sih5():
    """
    API endpoint to run SIH_Fifth.py
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Fifth.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Fifth.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/run-sih10', methods=['GET', 'OPTIONS'])
def run_sih10():
    """
    API endpoint to run SIH_Tenth.py
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Tenth.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Tenth.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/run-sih11', methods=['GET', 'OPTIONS'])
def run_sih11():
    """
    API endpoint to run SIH_Eleventh.py (Space Debris Dashboard)
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Eleventh.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Eleventh.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Dashboard launch timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 50

@app.route('/api/run-sih8', methods=['GET', 'OPTIONS'])
def run_sih8():
    """
    API endpoint to run SIH_Eighth.py (Rocket Launch Simulation)
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Eighth.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Eighth.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/run-sih6', methods=['GET', 'OPTIONS'])
def run_sih6():
    """
    API endpoint to run SIH_Sixth.py (Orbit Visualizer)
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        success, output = execute_script("SIH_Sixth.py")
        if not success:
            return jsonify({"success": False, "error": output}), 500

        return jsonify({
            "success": True,
            "message": "SIH_Sixth.py executed successfully",
            "output": output
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Simulation timeout"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/calculate-orbit', methods=['POST', 'OPTIONS'])
def calculate_orbit():
    """
    API endpoint to calculate orbit parameters based on given inputs
    """
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        # Get parameters from request
        data = request.get_json()
        altitude = data.get('altitude', 500)  # km
        inclination = data.get('inclination', 51.6)  # degrees
        eccentricity = data.get('eccentricity', 0.01)
        num_points = data.get('num_points', 360)

        # Import the orbit calculation functions from SIH_Sixth.py
        import sys
        import importlib.util

        # Load the SIH_Sixth module
        spec = importlib.util.spec_from_file_location("SIH_Sixth", "SIH_Sixth.py")
        sih6_module = importlib.util.module_from_spec(spec)
        sys.modules["SIH_Sixth"] = sih6_module
        spec.loader.exec_module(sih6_module)

        # Calculate orbit points
        orbit_points = sih6_module.calculate_orbit_points(altitude, inclination, eccentricity, num_points)

        # Calculate orbital information
        velocity = sih6_module.calculate_orbital_velocity(altitude, eccentricity)
        period = sih6_module.calculate_orbital_period(altitude, eccentricity)

        return jsonify({
            "success": True,
            "orbit_points": orbit_points,
            "velocity": velocity,
            "period": period,
            "perigee": (sih6_module.R_EARTH + altitude * 1000 * (1 - eccentricity))/1000,
            "apogee": (sih6_module.R_EARTH + altitude * 1000 * (1 + eccentricity))/1000
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Run on port 5000
    print("Starting Space Debris Mission Control Web Server...")
    print("Access at http://localhost:5000")
    print("Mission Simulation at http://localhost:5000/mission-simulation")
    app.run(debug=True, port=5000)
