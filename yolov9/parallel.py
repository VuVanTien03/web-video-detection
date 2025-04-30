import cv2
from models.common import DetectMultiBackend, AutoShape
import torch
from deep_sort_realtime.deepsort_tracker import DeepSort
import queue
import threading
import numpy as np
import time 

weights_path = r"D:\code\python\DataMining\yolov9\owncode\data\gelan_t.pt"
class_file = r"D:\code\python\DataMining\yolov9\owncode\data\classes.names"
weight_onnx = r"D:\code\python\DataMining\yolov9\owncode\data\weight.onnx"

device = torch.device("cpu")

model_backend = DetectMultiBackend(weights=weights_path, device=device)
model = AutoShape(model_backend)
model.eval()

tracker = DeepSort(
    max_age=40,           # Cho phép track sống lâu hơn dù mất detection
    n_init=5,             # Track cần 5 detection liên tiếp mới confirm (giảm nhầm ID)
    max_iou_distance=0.4, # Giảm IOU threshold để matching chặt hơn
    nn_budget=100         # Số lượng feature vector giữ lại
)


result = queue.Queue()
image_stack = queue.LifoQueue()
# xử lý ở một luồng riêng 
def yolo_worker():
    while True:
        image = image_stack.get()
        if image is None : 
            break 
        else : 
            with torch.no_grad():
                pre = model(image)
                result.put(pre)
# mở video chiếu kết quả . 
def show_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay_time = 1/fps
    while cap.isOpened():
        ret ,frame = cap.read()
        image_stack.put(frame)
        if not result.empty():
            pre = result.get().pred[0]
            for det in pre:
                x1 , y1 , x2 , y2 , conf , class_id = det[:6]
                x1 , y1 , x2 , y2 = map(int , [x1 , y1 , x2 , y2])
                if conf < 0.8 : 
                    continue
                label = "violence"
                conf = str(conf.item())
                cv2.rectangle(frame , (x1 , y1) , (x2,y2) , (0, 255, 0) , 2)
                cv2.putText(frame , label , (x1 , y1-10) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame , conf , (x1 , y1-25) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imshow("YOLOv9 Inference", frame)
        if cv2.waitKey(int(1000*delay_time)) & 0xFF == ord('q'):
            break

    # Gửi tín hiệu dừng cho worker và chờ nó kết thúc
    image_stack.put(None)
    cap.release()
    cv2.destroyAllWindows()
def track(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = 1/fps 
    while cap.isOpened():
        ret , frame = cap.read()
        image_stack.put(frame)
        if not result.empty():
            pre = result.get().pred[0]
            detections = []
            for det in pre : 
                x1 , y1 , x2 , y2 , conf , class_id = det[:6]
                x1 , y1 , x2 , y2 = map(int , [x1 , y1 , x2 , y2 ])
                if conf > 0.8 : 
                    detections.append([[x1, y1, x2, y2], conf.item(), int(class_id)])
            tracks = tracker.update_tracks(detections, frame=frame)
            for track in tracks: 
                if not track.is_confirmed(): 
                    continue 
                track_id = track.track_id 
                ltrb = track.to_ltrb()
                label = "violence"
                x1 , y1 , x2 , y2 = map(int , ltrb )
                cv2.rectangle(frame , (x1 , y1) , (x2,y2) , (0, 255, 0) , 2)
                cv2.putText(frame , label , (x1 , y1-10) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    # cv2.putText(frame , str(conf) , (x1 , y1-25) , cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imshow("YOLOv9 Inference", frame)
        if cv2.waitKey(int(1000*delay)) & 0xFF == ord('q'):
            break
def get_fps(path): 
    cap = cv2.VideoCapture(path)
    return cap.get(cv2.CAP_PROP_FPS)
if __name__=="__main__":
    threading.Thread(target=yolo_worker, daemon=True).start()
    video_path = r"D:\Downloads\Gym Fight over a Cable Machine 🤔 💪🏼 Let’s see who Wins 🏆 #fighting #gym #fighter #shorts #viral.mp4"
    video_path3 = r"D:\Downloads\10 Fastest Finishes in UFC History 🏆.mp4"
    video4 = r"D:\Downloads\videoplayback (1).mp4"
    show_video(video4)
    # print(get_fps(video_path3))
    # track(video_path3)