import cv2
import torch
import yaml
import os
from ultralytics import YOLO


def load_model(model_path):
    model = YOLO(model_path)
    return model

def process_frame(frame, model):
    results = model(frame)
    return results

def main():
    with open('src/config/settings.yaml') as file:
        config = yaml.safe_load(file)

    camera_index = config['camera']['index']
    model_path = config['model']['path']

    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}. Downloading...")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.hub.download_url_to_file('https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt', model_path) 
        print("Model downloaded successfully.")

    model = load_model(model_path)
    model.eval()

    cap = cv2.VideoCapture(camera_index)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = process_frame(frame, model)
        cv2.imshow('YOLO v8 Object Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()