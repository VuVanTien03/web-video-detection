# utils/path_helper.py
import os
import sys

def add_yolov9_to_sys_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '..', '..', '..'))
    yolo_path = os.path.join(project_root, 'yolov9')
    if yolo_path not in sys.path:
        sys.path.append(yolo_path)
