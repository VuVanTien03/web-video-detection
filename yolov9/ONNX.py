import torch
import onnxruntime as ort 
import numpy as np
import cv2
import time 

# Đường dẫn mô hình ONNX
weight_onnx = r"D:\code\python\DataMining\yolov9\owncode\data\weight.onnx"

session_options = ort.SessionOptions()
session_options.intra_op_num_threads = 4 
session_options.inter_op_num_threads = 4 
# Load ONNX model
session = ort.InferenceSession(weight_onnx, session_options = session_options , providers=['CPUExecutionProvider'])
# session.set_session_options(intra_op_num_threads=4, inter_op_num_threads=4)  # Điều chỉnh theo số lõi CPU
input_name = session.get_inputs()[0].name

# Hàm tiền xử lý ảnh từ OpenCV frame
def pre_process_image_cv2(frame):
    # Resize về 640x640 và chuyển BGR → RGB
    image = cv2.resize(frame, (640, 640))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Chuyển sang [0,1] và transpose thành (C, H, W)
    image = image.astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))  # (3, 640, 640)
    image = np.expand_dims(image, axis=0)   # (1, 3, 640, 640)
    return image

# Chạy video + đo thời gian xử lý
def excute_time(file_path):
    cap = cv2.VideoCapture(file_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        start = time.time()

        input = pre_process_image_cv2(frame)
        outputs = session.run(None, {input_name: input})

        end = time.time()
        print(f"⏱️ Time per frame: {end - start:.3f}s")

        # (Tuỳ bạn) xử lý output: vẽ box, decode kết quả ở đây

    cap.release()
    print("✅ Done")

if __name__ == "__main__":
    video_path = r"D:\Downloads\10 Fastest Finishes in UFC History 🏆.mp4"
    excute_time(video_path)
