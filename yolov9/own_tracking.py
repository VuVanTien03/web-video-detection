import cv2
from models.common import DetectMultiBackend, AutoShape
import torch
from deep_sort_realtime.deepsort_tracker import DeepSort
import queue
import threading
import numpy as np
import time 
# import onnxruntime 
# ===== Khởi tạo model =====
weights_path = r"D:\code\python\DataMining\yolov9\owncode\data\weight.pt"
class_file = r"D:\code\python\DataMining\yolov9\owncode\data\classes.names"
weight_onnx = r"D:\code\python\DataMining\yolov9\owncode\data\weight.onnx"

device = torch.device("cpu")

model_backend = DetectMultiBackend(weights=weights_path, device=device)
model = AutoShape(model_backend)
model.eval()

# ===== Biến toàn cục =====
frame_queue = queue.Queue()
result_queue = queue.Queue()
process_every_n = 5
tracker = DeepSort(max_age=5)

with open(class_file, "r") as f:
    class_names = f.read().strip().split("\n")

colors = np.random.randint(0, 255, size=(len(class_names), 3), dtype=int)


# ===== YOLO xử lý ở luồng riêng =====
def yolo_worker():
    while True:
        item = frame_queue.get()
        if item is None:
            break
        index, frame = item
        with torch.no_grad():
            result = model(frame)
        result_queue.put((index, result))


# ===== Mở và chiếu video =====
def open_video(video_path):
    cap = cv2.VideoCapture(video_path)
    result_dict = {}
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Gửi frame cho YOLO xử lý nếu cần
        if frame_index % process_every_n == 0:
            frame_queue.put((frame_index, frame.copy()))

        # Nhận kết quả YOLO
        while not result_queue.empty():
            i, result = result_queue.get()
            result_dict[i] = result

        # Vẽ kết quả nếu frame hiện tại đã có kết quả
        if frame_index in result_dict:
            predictions = result_dict[frame_index].pred[0]

            detections = []
            for det in predictions:
                x1, y1, x2, y2, conf, class_id = det[:6]
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                class_id = int(class_id)

                # DeepSort yêu cầu: [x, y, w, h], confidence, class_id
                detections.append([[x1, y1, x2 - x1, y2 - y1], conf.item(), class_id])

            # Update tracker
            tracks = tracker.update_tracks(detections, frame=frame)

            # Vẽ kết quả
            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltrb()  # [left, top, right, bottom]
                x1, y1, x2, y2 = map(int, ltrb)
                class_id = track.get_det_class()
                color = colors[class_id].tolist()
                label = f"{class_names[class_id]} ID:{track_id}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Hiển thị frame
        cv2.imshow("Object Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_index += 1

    cap.release()
    cv2.destroyAllWindows()
    frame_queue.put(None) 
def read_class_object():
    class_names = []
    with open(class_file , "rt" ) as f : 
        lines = f.readlines()
        class_names  = lines.strip().split("\n")
    return class_names

def new_process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_index = 0 
    result = None
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000/fps)
    while cap.isOpened():
        ret , frame = cap.read()
        if not ret : 
            break 
        if frame_index ==  0 or frame_index % 15 == 0 : 
            frame_queue.put((frame_index , frame.copy()))
        # lấy kết quả từ yolo worker 
        if  not result_queue.empty():
            i , result = result_queue.get()
           
        if result != None : 
            predicts = result.pred[0]
            detection = []
            for det in predicts : 
                x1 , y1 , x2 , y2 , conf , class_id = det[:6]
                x1 , y1 , x2 , y2 = map(int , [x1 , y1 , x2 , y2])
                class_id = int(class_id)
                if class_id == 3 :
                    color = colors[3].tolist()
                    label = class_names[class_id]
                    conf = str(conf.item())
                    cv2.rectangle(frame , (x1 , y1) , (x2,y2) , color , 2)
                    cv2.putText(frame , label , (x1 , y1-10) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.putText(frame , conf , (x1 , y1-25) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                # detection.append([[x1 , y1 , x2-x1 , y2-y1] , conf.item() , class_id])
            # tracks = tracker.update_tracks(detection , frame = frame)
            # # vẽ kết quả 
            # for track in tracks:
            #     if not track.is_confirmed():
            #         continue
            #     track_id = track.track_id
            #     ltrb = track.to_ltrb()  # [left, top, right, bottom]
            #     x1, y1, x2, y2 = map(int, ltrb)
            #     class_id = track.get_det_class()
            #     color = colors[class_id].tolist()
            #     label = f"{class_names[class_id]} ID:{track_id}"
            #     cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            #     cv2.putText(frame, label, (x1, y1 - 10),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        # show video 
        cv2.imshow("Object tracking" , frame) 
        if cv2.waitKey(delay) & 0xFF == ord("q"):
            break 
        frame_index +=1 
    cap.release()
    cv2.destroyAllWindows()
    frame_queue.put(None)
def show_video(video_path):
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)  # thời gian chờ giữa các frame (tính bằng ms)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Video", frame)
        if cv2.waitKey(delay) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
def time_excute(file_path):
    cap = cv2.VideoCapture(file_path)

    while cap.isOpened():
        ret , frame = cap.read()
        if not ret : 
            break
        start = time.time()
        with torch.no_grad():
            result = model(frame)
        end = time.time()
        print(f"time per frame : {end-start}")
# ===== Chạy chương trình =====
if __name__ == "__main__":
    threading.Thread(target=yolo_worker, daemon=True).start()
    video_path = r"D:\Downloads\Gym Fight over a Cable Machine 🤔 💪🏼 Let’s see who Wins 🏆 #fighting #gym #fighter #shorts #viral.mp4"
    # open_video(video_path)
    video_path2 = r"D:\Downloads\videoplayback.mp4"
    video_path3 = r"D:\Downloads\10 Fastest Finishes in UFC History 🏆.mp4"
    new_process_video(video_path3)
    # time_excute(video_path3)
    # show_video(video_path3)
    