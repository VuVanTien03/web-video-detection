import cv2
import torch
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from models.common import DetectMultiBackend, AutoShape

# Tham số
video_path = r"D:\Downloads\Gym Fight over a Cable Machine 🤔 💪🏼 Let’s see who Wins 🏆 #fighting #gym #fighter #shorts #viral.mp4"
conf_threshold = 0.3
device = "cuda" if torch.cuda.is_available() else "cpu"
weights_path = r"D:\code\python\DataMining\yolov9\owncode\data\weight.pt"
class_file = r"D:\code\python\DataMining\yolov9\owncode\data\classes.names"

# Khởi tạo
tracker = DeepSort(max_age=5)
model = DetectMultiBackend(weights_path, device=device, fuse=True)
model = AutoShape(model)  # Đảm bảo AutoShape bao bọc mô hình

# Đọc class names
with open(class_file, "r") as f:
    class_names = f.read().strip().split("\n")
colors = np.random.randint(0, 255, size=(len(class_names), 3))

# Mở video
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Không thể mở video!")
    exit()

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"Frame {frame_count}: Không thể đọc frame từ video.")
        break

    frame_count += 1
    # Tiền xử lý frame
    frame = cv2.resize(frame, (640, 640))  # Kích thước vuông
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Chuyển sang RGB

    # Dự đoán với AutoShape
    results = model(frame_rgb, size=640)  # Chỉ định kích thước đầu vào rõ ràng
    detections = results.pred[0]  # Lấy tensor dự đoán từ results.pred

    if detections is None or len(detections) == 0:
        print(f"Frame {frame_count}: Không phát hiện được vật thể.")
        cv2.imshow("OT", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        continue

    detect = []
    for det in detections:
        x1, y1, x2, y2, confidence, class_id = det[:6]
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])  # Chuyển sang int
        
        class_id = int(class_id)  # Đảm bảo class_id là số nguyên
        print(f"Frame {frame_count}: {class_names[class_id]}, Conf: {confidence}")
        if confidence < conf_threshold:
            continue
        detect.append([[x1, y1, x2 - x1, y2 - y1], confidence, class_id])

    # Tracker
    tracks = tracker.update_tracks(detect, frame=frame)
    for track in tracks:
        if track.is_confirmed():
            track_id = track.track_id
            ltrb = track.to_ltrb()
            class_id = track.get_det_class()
            x1, y1, x2, y2 = map(int, ltrb)
            color = colors[class_id]
            B, G, R = map(int, color)
            label = f"{class_names[class_id]}-{track_id}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (B, G, R), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imshow("OT", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()