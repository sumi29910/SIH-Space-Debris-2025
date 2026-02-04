"""
Real-time Space Debris Detection + Tracking (Python)
Uses: ultralytics YOLOv8 (fast), OpenCV, numpy, pandas
Author: ChatGPT (example)
Notes:
 - Provide a video source (0 for webcam, or path/RTSP).
 - Configure thresholds for alerts, frame_skip for speed.
 - Replace model file with your trained debris detector for best results.
"""

import time
import cv2
import numpy as np
from ultralytics import YOLO
import pandas as pd
from scipy.spatial import distance

# ---------------------------
# Config
# ---------------------------
VIDEO_SOURCE = 0  # 0 = webcam, or "video.mp4", or "rtsp://..."
MODEL_PATH = "yolov8n.pt"  # use a custom trained model for debris if available
CONF_THRESHOLD = 0.35
IOU_TRACK_THRESHOLD = 0.3
MAX_MISSES = 8  # how many frames a track can miss before deletion
FRAME_SKIP = 0  # detect on every FRAME_SKIP+1 frame (0 = every frame)
ALERT_SIZE_PIXELS = 1500  # arbitrary area threshold to alert
ALERT_SPEED_PIXELS_PER_SEC = 100  # pixels / sec -> alert if faster than this
OUTPUT_CSV = "detections_log.csv"

# Camera / optic info (optional) to convert pixels->angle
H_FOV_DEG = 1.0  # horizontal field of view of sensor in degrees (set correctly for your telescope/camera)
IMAGE_WIDTH_PX = None  # will be set from frames at runtime

# ---------------------------
# Simple Tracker Implementation
# ---------------------------
class Track:
    _id_iter = 0

    def __init__(self, bbox, score, frame_idx, centroid=None):
        self.id = Track._id_iter
        Track._id_iter += 1
        self.bbox = bbox  # [x1,y1,x2,y2]
        self.score = score
        self.last_frame = frame_idx
        self.misses = 0
        self.history = [(frame_idx, bbox)]
        self.centroid = centroid if centroid is not None else bbox_centroid(bbox)
        self.vel = (0.0, 0.0)  # pixels/frame
        self.created_time = time.time()

    def update(self, bbox, score, frame_idx):
        prev_centroid = self.centroid
        self.bbox = bbox
        self.score = score
        self.last_frame = frame_idx
        self.misses = 0
        self.centroid = bbox_centroid(bbox)
        # update velocity estimate (simple)
        dt = 1.0  # frames difference = 1 when called per frame; if skipping frames, callers must account
        self.vel = ((self.centroid[0] - prev_centroid[0]) / dt, (self.centroid[1] - prev_centroid[1]) / dt)
        self.history.append((frame_idx, bbox))

    def mark_missed(self):
        self.misses += 1

    def is_dead(self):
        return self.misses > MAX_MISSES

def bbox_centroid(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

def bbox_area(bbox):
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)

def iou(b1, b2):
    x1, y1, x2, y2 = b1
    x1p, y1p, x2p, y2p = b2
    xi1 = max(x1, x1p)
    yi1 = max(y1, y1p)
    xi2 = min(x2, x2p)
    yi2 = min(y2, y2p)
    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter = inter_w * inter_h
    union = bbox_area(b1) + bbox_area(b2) - inter
    return inter / union if union > 0 else 0.0

# ---------------------------
# Detector wrapper
# ---------------------------
class Detector:
    def __init__(self, model_path, conf=0.25):
        print("Loading model:", model_path)
        self.model = YOLO(model_path)
        self.conf = conf

    def predict(self, frame):
        """
        Run model inference on an image (BGR numpy array).
        Returns list of detections: each is dict {'bbox':[x1,y1,x2,y2], 'score':, 'class':}
        Coordinates are in pixels (int).
        """
        # YOLO expects RGB input
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Set stream=True to get generator? We'll use .predict.
        res = self.model.predict(rgb, imgsz=640, conf=self.conf, verbose=False)  # returns list (per batch)
        # res is a list with one element for the frame
        dets = []
        if len(res) == 0:
            return dets
        r = res[0]
        # r.boxes contains xyxy, conf, cls
        boxes = r.boxes
        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy()  # [x1,y1,x2,y2]
            conf = float(box.conf[0].cpu().numpy())
            cls = int(box.cls[0].cpu().numpy())
            # Filter by conf: model already did
            x1, y1, x2, y2 = map(int, xyxy.tolist())
            dets.append({'bbox': [x1, y1, x2, y2], 'score': conf, 'class': cls})
        return dets

# ---------------------------
# Association: simple greedy by IoU
# ---------------------------
def associate_detections_to_tracks(detections, tracks, iou_threshold=0.3):
    """
    detections: list of dicts with bbox
    tracks: list of Track objects
    Returns:
     matches: list of (det_idx, track_idx)
     unmatched_dets: list of det_idx
     unmatched_tracks: list of track_idx
    """
    if len(tracks) == 0:
        return [], list(range(len(detections))), []

    iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
    for d, det in enumerate(detections):
        for t, tr in enumerate(tracks):
            iou_matrix[d, t] = iou(det['bbox'], tr.bbox)

    matches = []
    unmatched_dets = list(range(len(detections)))
    unmatched_tracks = list(range(len(tracks)))

    # Greedy matching
    while True:
        if iou_matrix.size == 0:
            break
        idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
        best_val = iou_matrix[idx]
        if best_val < iou_threshold:
            break
        d, t = idx
        matches.append((d, t))
        # remove row d and col t
        iou_matrix[d, :] = -1
        iou_matrix[:, t] = -1
        if d in unmatched_dets:
            unmatched_dets.remove(d)
        if t in unmatched_tracks:
            unmatched_tracks.remove(t)

    return matches, unmatched_dets, unmatched_tracks

# ---------------------------
# Real-time pipeline
# ---------------------------
def run_pipeline(source=VIDEO_SOURCE):
    global IMAGE_WIDTH_PX
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source {source}")
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Cannot read first frame from source")

    h, w = frame.shape[:2]
    IMAGE_WIDTH_PX = w
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"Stream opened: {w}x{h} @ {fps:.1f} FPS")

    detector = Detector(MODEL_PATH, conf=CONF_THRESHOLD)
    tracks = []
    frame_idx = 0
    log_rows = []

    last_detect_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of stream or read error.")
                break
            t0 = time.time()
            do_detect = (FRAME_SKIP == 0) or (frame_idx % (FRAME_SKIP + 1) == 0)

            detections = []
            if do_detect:
                detections = detector.predict(frame)
                last_detect_time = time.time()

            # Associate and update tracks
            matches, unmatched_dets, unmatched_tracks = associate_detections_to_tracks(detections, tracks, IOU_TRACK_THRESHOLD)

            # Update matched tracks
            for det_idx, tr_idx in matches:
                det = detections[det_idx]
                tracks[tr_idx].update(det['bbox'], det['score'], frame_idx)

            # Create new tracks for unmatched detections
            for d in unmatched_dets:
                det = detections[d]
                tr = Track(det['bbox'], det['score'], frame_idx)
                tracks.append(tr)

            # Mark unmatched tracks as missed
            for t_ind in unmatched_tracks:
                tracks[t_ind].mark_missed()

            # Remove dead tracks
            tracks = [t for t in tracks if not t.is_dead()]

            # Visualization & alerts
            overlay = frame.copy()
            alerts = []
            for tr in tracks:
                x1, y1, x2, y2 = map(int, tr.bbox)
                area = bbox_area(tr.bbox)
                cx, cy = map(int, tr.centroid)
                vx, vy = tr.vel
                # convert to approximate pixels/sec speed
                # Because dt~1/fps frames -> pixels/sec = vel * fps
                px_per_sec = np.hypot(vx, vy) * fps
                label = f"ID:{tr.id} v:{px_per_sec:.1f}px/s a:{int(area)}"
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(overlay, label, (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)
                cv2.circle(overlay, (cx, cy), 3, (0,0,255), -1)

                # alert logic (customize)
                if area > ALERT_SIZE_PIXELS or px_per_sec > ALERT_SPEED_PIXELS_PER_SEC:
                    alerts.append((tr.id, area, px_per_sec))

                # log row
                log_rows.append({
                    'time': time.time(),
                    'frame': frame_idx,
                    'track_id': tr.id,
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'area': area,
                    'vx_px_frame': vx, 'vy_px_frame': vy,
                    'speed_px_per_s': px_per_sec
                })

            # Draw alerts
            if len(alerts) > 0:
                s = f"ALERT: {len(alerts)} object(s) -- "
                s += " ; ".join([f"id{a[0]} area{a[1]} spd{a[2]:.1f}" for a in alerts])
                cv2.putText(overlay, s, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

            # Show fps & frame
            t1 = time.time()
            proc_time = (t1 - t0)
            show_text = f"Frame:{frame_idx} Proc:{proc_time*1000:.0f}ms Tracks:{len(tracks)}"
            cv2.putText(overlay, show_text, (10, overlay.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

            cv2.imshow("Debris Detector", overlay)
            frame_idx += 1

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        # save logs
        if len(log_rows) > 0:
            df = pd.DataFrame(log_rows)
            df.to_csv(OUTPUT_CSV, index=False)
            print("Saved detections to", OUTPUT_CSV)
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run_pipeline()