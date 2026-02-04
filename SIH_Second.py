"""
Real-time Space Debris Monitoring Prototype
- Detector: Ultralytics YOLOv8 (yolov8n.pt by default). Replace MODEL_PATH with your trained model.
- Modes: "camera" (or video file) or "simulate" for synthetic debris generation.
- Tracks objects, computes simple risk score and suggests avoidance direction.
Author: ChatGPT (example)
"""

import argparse
import time
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from collections import deque, defaultdict
import math
import random

# -----------------------
# Configuration
# -----------------------
MODEL_PATH = "yolov8n.pt"  # replace with domain-trained model for real use
CONF_THRESHOLD = 0.35
FRAME_SKIP = 0  # detect every FRAME_SKIP+1 frames
IOU_TRACK_THRESHOLD = 0.3
MAX_MISSES = 8
LOG_CSV = "space_debris_log.csv"

# Camera / optical meta (needed to convert px->deg)
H_FOV_DEG = 1.0   # horizontal field of view in degrees (set for your optics)
IMAGE_WIDTH_PX = None  # set at runtime from first frame

# Risk scoring weights (tunable)
WEIGHT_SIZE = 0.4
WEIGHT_SPEED = 0.4
WEIGHT_PROXIMITY = 0.2

# thresholds for alerting
RISK_ALERT_THRESHOLD = 0.6  # [0,1]
SPEED_ALERT_PX_PER_S = 200  # fallback px/s threshold
AREA_ALERT_PX = 1000

# -----------------------
# Utilities
# -----------------------
def bbox_area(b):
    x1,y1,x2,y2 = b
    return max(0, x2-x1) * max(0, y2-y1)

def bbox_centroid(b):
    x1,y1,x2,y2 = b
    return ((x1+x2)/2, (y1+y2)/2)

def iou(b1, b2):
    x1,y1,x2,y2 = b1
    X1,Y1,X2,Y2 = b2
    xi1 = max(x1,X1); yi1 = max(y1,Y1)
    xi2 = min(x2,X2); yi2 = min(y2,Y2)
    iw = max(0, xi2-xi1); ih = max(0, yi2-yi1)
    inter = iw*ih
    union = bbox_area(b1)+bbox_area(b2)-inter
    return inter/union if union>0 else 0.0

# -----------------------
# Detector wrapper
# -----------------------
class Detector:
    def __init__(self, model_path=MODEL_PATH, conf=CONF_THRESHOLD, use_model=True):
        self.use_model = use_model
        self.conf = conf
        if use_model:
            print("Loading YOLO model:", model_path)
            self.model = YOLO(model_path)

    def predict(self, frame):
        """
        Return list of detections: dicts {'bbox':[x1,y1,x2,y2], 'score':float}
        If use_model False, should be replaced by simulation externally.
        """
        if not self.use_model:
            return []
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.model.predict(rgb, imgsz=640, conf=self.conf, verbose=False)
        dets = []
        if len(res)==0:
            return dets
        r = res[0]
        for box in r.boxes:
            xyxy = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            x1,y1,x2,y2 = map(int, xyxy.tolist())
            dets.append({'bbox':[x1,y1,x2,y2], 'score':conf})
        return dets

# -----------------------
# Simple Tracker
# -----------------------
class Track:
    _id_iter = 0
    def __init__(self, bbox, score, frame_idx):
        self.id = Track._id_iter; Track._id_iter += 1
        self.bbox = bbox
        self.score = score
        self.last_frame = frame_idx
        self.misses = 0
        self.centroid = bbox_centroid(bbox)
        self.vel_px_per_frame = (0.0, 0.0)
        self.age = 0
        # maintain short history to smooth velocity
        self.history = deque(maxlen=5)  # (frame_idx, centroid)
        self.history.append((frame_idx, self.centroid))
        self.created_time = time.time()

    def update(self, bbox, score, frame_idx):
        prev_cent = self.centroid
        self.bbox = bbox
        self.score = score
        self.last_frame = frame_idx
        self.misses = 0
        self.centroid = bbox_centroid(bbox)
        self.history.append((frame_idx, self.centroid))
        self.age += 1
        # compute smoothed velocity (pixels/frame)
        if len(self.history) >= 2:
            (f0, c0) = self.history[0]
            (f1, c1) = self.history[-1]
            dt = max(1, f1 - f0)
            vx = (c1[0]-c0[0]) / dt
            vy = (c1[1]-c0[1]) / dt
            # exponential smoothing
            alpha = 0.6
            self.vel_px_per_frame = (alpha*vx + (1-alpha)*self.vel_px_per_frame[0],
                                     alpha*vy + (1-alpha)*self.vel_px_per_frame[1])

    def mark_missed(self):
        self.misses += 1

    def is_dead(self):
        return self.misses > MAX_MISSES

# greedy association by IoU
def associate(detections, tracks, iou_thresh=IOU_TRACK_THRESHOLD):
    if len(tracks)==0:
        return [], list(range(len(detections))), []
    iou_m = np.zeros((len(detections), len(tracks)), dtype=np.float32)
    for d, det in enumerate(detections):
        for t, tr in enumerate(tracks):
            iou_m[d,t] = iou(det['bbox'], tr.bbox)
    matches=[]
    unmatched_d = list(range(len(detections)))
    unmatched_t = list(range(len(tracks)))
    while True:
        if iou_m.size==0: break
        d,t = np.unravel_index(np.argmax(iou_m), iou_m.shape)
        if iou_m[d,t] < iou_thresh:
            break
        matches.append((d,t))
        iou_m[d,:] = -1
        iou_m[:,t] = -1
        if d in unmatched_d: unmatched_d.remove(d)
        if t in unmatched_t: unmatched_t.remove(t)
    return matches, unmatched_d, unmatched_t

# -----------------------
# Risk scoring & avoidance suggestion
# -----------------------
def px_to_deg_per_s(px_per_s, img_w_px):
    """Convert pixels/sec to degrees/sec using H_FOV_DEG"""
    if img_w_px is None or img_w_px == 0:
        return px_per_s  # fallback
    deg_per_px = H_FOV_DEG / img_w_px
    return px_per_s * deg_per_px

def compute_risk_score(area_px, speed_px_per_s, est_range_km=None):
    """
    Simple normalized risk score [0,1].
    - area: larger area => bigger object => more risk
    - speed: larger angular speed => likely crossing path
    - proximity: if range known (km) smaller ranges => higher risk
    """
    # normalize using heuristic scales (tunable)
    size_norm = min(1.0, area_px / (AREA_ALERT_PX*4))  # area scaling
    speed_norm = min(1.0, speed_px_per_s / (SPEED_ALERT_PX_PER_S*2))
    if est_range_km is None:
        prox_norm = 0.5  # unknown proximity -> moderate
    else:
        # closer => higher prox_norm
        prox_norm = min(1.0, max(0.0, (50.0 - est_range_km) / 50.0))  # assume 0-50km relevance
    score = WEIGHT_SIZE*size_norm + WEIGHT_SPEED*speed_norm + WEIGHT_PROXIMITY*prox_norm
    return score

def suggest_avoidance(track, frame_w, frame_h):
    """
    Suggest a simple 2D pixel delta maneuver to shift spacecraft pointing/position.
    This is illustrative only — real maneuvers require orbital mechanics & range info.
    We'll suggest moving orthogonal to velocity to reduce likelihood of hit.
    """
    vx, vy = track.vel_px_per_frame
    # orthogonal vector (rotate 90 deg)
    ox, oy = -vy, vx
    mag = math.hypot(ox, oy)
    if mag == 0:
        return (0,0)
    # normalize and scale to small fraction of frame
    scale = 0.05 * min(frame_w, frame_h)
    dx = (ox/mag) * scale
    dy = (oy/mag) * scale
    return (int(dx), int(dy))

# -----------------------
# Simulation generator (for testing)
# -----------------------
def simulate_detections(frame_idx, w, h, num_objects=3):
    """Generate moving synthetic bounding boxes (for simulation mode)"""
    random.seed(frame_idx)  # deterministic-ish per frame for demo
    dets=[]
    for i in range(num_objects):
        # create pseudo-linear motion depending on i
        x = int(((frame_idx*5 + i*80) % w))
        y = int(((frame_idx*3 + i*60) % h))
        size = 20 + (i+1)*10
        x1 = max(0, x - size); y1 = max(0, y - size)
        x2 = min(w-1, x + size); y2 = min(h-1, y + size)
        score = 0.9 - 0.05*i
        dets.append({'bbox':[x1,y1,x2,y2], 'score':score})
    return dets

# -----------------------
# Main pipeline
# -----------------------
def run_pipeline(source=0, mode="camera"):
    global IMAGE_WIDTH_PX
    if mode == "camera":
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open source {source}")
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Cannot read frame from source")
        h, w = frame.shape[:2]
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    else:
        # simulate a frame size
        w, h = 1280, 720
        fps = 30.0
        cap = None

    IMAGE_WIDTH_PX = w
    detector = Detector(MODEL_PATH, conf=CONF_THRESHOLD, use_model=(mode=="camera" and source is not None))
    tracks = []
    logs = []
    frame_idx = 0
    try:
        while True:
            t0 = time.time()
            if mode == "camera":
                ret, frame = cap.read()
                if not ret:
                    print("Stream ended.")
                    break
            else:
                # create blank synthetic frame
                frame = np.zeros((h,w,3), dtype=np.uint8)

            do_detect = (FRAME_SKIP == 0) or (frame_idx % (FRAME_SKIP+1) == 0)
            detections = []
            if mode == "simulate":
                detections = simulate_detections(frame_idx, w, h, num_objects=4)
            elif do_detect:
                detections = detector.predict(frame)

            # Associate and update/create tracks
            matches, unmatched_dets, unmatched_tracks = associate(detections, tracks)
            for d,t in matches:
                tr = tracks[t]
                det = detections[d]
                tr.update(det['bbox'], det['score'], frame_idx)
            # create new tracks
            for d in unmatched_dets:
                det = detections[d]
                tracks.append(Track(det['bbox'], det['score'], frame_idx))
            # mark unmatched tracks missed
            for t in unmatched_tracks:
                tracks[t].mark_missed()
            # remove dead tracks
            tracks = [tr for tr in tracks if not tr.is_dead()]

            # visualization and risk evaluation
            overlay = frame.copy()
            alerts = []
            for tr in tracks:
                x1,y1,x2,y2 = map(int, tr.bbox)
                area = bbox_area(tr.bbox)
                cx,cy = map(int, tr.centroid)
                vx,vy = tr.vel_px_per_frame
                speed_px_per_s = math.hypot(vx,vy) * fps
                speed_deg_s = px_to_deg_per_s(speed_px_per_s, IMAGE_WIDTH_PX)
                # estimated range - unknown in optical-only; set None or use other sensor fusion
                est_range_km = None
                risk = compute_risk_score(area, speed_px_per_s, est_range_km)
                if risk >= RISK_ALERT_THRESHOLD or area >= AREA_ALERT_PX or speed_px_per_s >= SPEED_ALERT_PX_PER_S:
                    maneuver = suggest_avoidance(tr, w, h)
                    alerts.append({
                        'track_id': tr.id,
                        'frame': frame_idx,
                        'risk': risk,
                        'area': area,
                        'speed_px_s': speed_px_per_s,
                        'speed_deg_s': speed_deg_s,
                        'suggested_delta_px': maneuver
                    })
                    # draw alert visuals
                    cv2.rectangle(overlay, (x1,y1), (x2,y2), (0,0,255), 2)
                    cv2.putText(overlay, f"ALERT ID{tr.id} R={risk:.2f}", (x1, y1-6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,255), 1)
                    # draw suggested vector
                    dx,dy = maneuver
                    cv2.arrowedLine(overlay, (cx,cy), (int(cx+dx), int(cy+dy)), (0,0,255), 2, tipLength=0.3)
                else:
                    cv2.rectangle(overlay, (x1,y1),(x2,y2), (0,255,0), 1)
                    cv2.putText(overlay, f"ID{tr.id} R={risk:.2f}", (x1, y1-6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)
                # log entry for each track at this frame
                logs.append({
                    'time': time.time(),
                    'frame': frame_idx,
                    'track_id': tr.id,
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'area': area,
                    'vx_px_frame': vx, 'vy_px_frame': vy,
                    'speed_px_per_s': speed_px_per_s,
                    'risk': risk
                })

            # Display overlay (if not headless)
            # Only attempt to show if using opencv with GUI
            try:
                cv2.imshow("Space Debris Monitor", overlay)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quit key pressed.")
                    break
            except Exception:
                # running headless (e.g., server) - skip GUI
                pass

            # Print alerts to console
            for a in alerts:
                print(f"[ALERT] frame {a['frame']} id{a['track_id']} risk={a['risk']:.2f} area={a['area']} "
                      f"spd={a['speed_px_s']:.1f}px/s suggested_delta_px={a['suggested_delta_px']}")

            frame_idx += 1
            # sleep to emulate real-time if in simulate mode
            if mode == "simulate":
                time.sleep(1.0 / fps)

    finally:
        # save logs
        if len(logs) > 0:
            df = pd.DataFrame(logs)
            df.to_csv(LOG_CSV, index=False)
            print("Saved logs to", LOG_CSV)
        if mode == "camera" and cap is not None:
            cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=0, help="camera index or video file path")
    parser.add_argument("--mode", default="camera", choices=["camera","simulate"], help="camera or simulate")
    args = parser.parse_args()
    run_pipeline(source=args.source, mode=args.mode)