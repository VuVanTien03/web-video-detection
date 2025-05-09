import sys

# YOLOV9_PATH = r"D:\code\python\DataMining\yolov9"
# if YOLOV9_PATH not in sys.path:
#     sys.path.append(YOLOV9_PATH)
import os 
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir , '..' , '..' , '..'))
# print(project_root)
yolo_path = os.path.join(project_root , 'yolov9')
if yolo_path not in  sys.path : 
    sys.path.append(yolo_path)