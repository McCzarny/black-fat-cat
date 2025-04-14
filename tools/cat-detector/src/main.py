#!/usr/bin/env python3

import cv2
import torch
import yaml
import os
import time
import datetime
import fcntl
from ultralytics import YOLO

def load_model(model_path):
    model = YOLO(model_path)
    return model

def process_frame(frame, model):
    results = model(frame)
    return results

def check_directory_size(frames_dir):
    total_size = sum(os.path.getsize(os.path.join(frames_dir, f)) for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f)))
    return total_size > 1 * 1024 * 1024 * 1024  # 1 GB

def save_frame(frame, frames_dir, name, confidence_percentage):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    frame_path = os.path.join(frames_dir, f"{timestamp}_{name}_{confidence_percentage:.0f}.jpeg")
    cv2.imwrite(frame_path, frame)

def save_frame_if_cat_detected(frame, results, frames_dir, stats_file, confidence_threshold):
    for result in results:
        summary = result.summary()
        for detection in summary:
            if detection['name'] == 'cat':
                print(f"Cat detected with confidence {detection['confidence']:.2f}!")
                log_statistics(stats_file, f"Cat detected with confidence {detection['confidence']:.2f}!")
                if detection['confidence'] >= confidence_threshold:
                    save_frame(frame, frames_dir, detection['name'], detection['confidence'] * 100)
                    if check_directory_size(frames_dir):
                        print("Frames directory exceeded 1 GB. Stopping script.")
                        log_statistics(stats_file, "Frames directory exceeded 1 GB. Stopping script.")
                        exit(0)
                    return True
                else:
                    print(f"Cat detected but confidence is low: {detection['confidence']}")
                break
    return False

def trigger_witch():
    GPIO = 247
    gpio_path = f"/sys/class/gpio/gpio{GPIO}"

    try:
        # Export the GPIO pin
        with open("/sys/class/gpio/export", "w") as f:
            f.write(f"{GPIO}")

        # Set the GPIO direction to output
        with open(f"{gpio_path}/direction", "w") as f:
            f.write("out")

        # Turn on the witch
        print("Turn on witch")
        with open(f"{gpio_path}/value", "w") as f:
            f.write("1")  # Turn ON

        # Sleep for 30 seconds
        time.sleep(30)

        # Turn off the witch
        print("Make witch sleep")
        with open(f"{gpio_path}/value", "w") as f:
            f.write("0")  # Turn OFF

    finally:
        # Cleanup: Unexport the GPIO pin
        with open("/sys/class/gpio/unexport", "w") as f:
            f.write(f"{GPIO}")

last_witch_trigger_time = 0
def trigger_witch_if_cat_detected(
        frame,
        results,
        frames_dir,
        stats_file,
        configuration):
    
    global last_witch_trigger_time
    current_time = time.time()
    witch_trigger_confidence_threshold = configuration['witch_trigger']['confidence_threshold']
    minimal_interval_between_triggers = configuration['witch_trigger']['min_interval_sec']
    witch_armed_start_time = configuration['witch_trigger'].get('start_time')
    witch_armed_end_time = configuration['witch_trigger'].get('end_time')
    if witch_armed_start_time and witch_armed_end_time:
        current_time = datetime.datetime.now().time()
        if not (witch_armed_start_time <= current_time <= witch_armed_end_time):
            log_statistics(stats_file, "Witch trigger time not met.")
            return False
    
    for result in results:
        summary = result.summary()
        for detection in summary:
            if detection['name'] == 'cat' and detection['confidence'] >= witch_trigger_confidence_threshold:

                if current_time - last_witch_trigger_time < minimal_interval_between_triggers:
                    log_statistics(stats_file, "Witch trigger interval not met.")
                    return False
                log_statistics(stats_file, "Witch triggered due to cat detection!")
                trigger_witch()
                save_frame(frame, frames_dir, f"witch-triggered-for-{detection['name']}", detection['confidence'] * 100)
                last_witch_trigger_time = current_time
                return True
    return False

def log_statistics(stats_file, stats):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(stats_file, 'a') as file:
        file.write(f"{timestamp} - {stats}\n")

def prevent_multiple_instances():
    lock_file = '/tmp/gathercats.lock'
    lock_fd = open(lock_file, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Another instance of the script is already running. Exiting.")
        exit(1)
    return lock_fd

def get_camera_indices():
    # For testing, if MacOS, use the first camera index
    if os.uname().sysname == 'Darwin':
        vid_indices = [0]
        return vid_indices

    devs = os.listdir('/dev')
    vid_indices = [int(dev[len('video'):]) for dev in devs 
               if dev.startswith('video')]
    vid_indices = sorted(vid_indices)
    return vid_indices

def get_camera():
    vid_indices = get_camera_indices()

    print(f"Available camera indices: {vid_indices}")
    if not vid_indices:
        print("No cameras found.")
        return None
    
    for index in vid_indices:
        try:
            cap = cv2.VideoCapture(index)
            return cap
        except:
            print(f"Error accessing camera {index}. Trying next one...")
            continue
    
    return None

def main():
    settings_path = os.path.join(os.path.dirname(__file__), './config/settings.yaml')
    with open(settings_path) as file:
        config = yaml.safe_load(file)

    model_path = os.path.join(os.path.dirname(__file__), "..", config['model']['path'])

    frames_dir = os.path.join(os.path.dirname(__file__), '../frames')
    os.makedirs(frames_dir, exist_ok=True)

    stats_file = os.path.join(os.path.dirname(__file__), '../stats/gathercats.stat.txt')
    os.makedirs(os.path.dirname(stats_file), exist_ok=True)

    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}. Downloading...")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.hub.download_url_to_file('https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt', model_path) 
        print("Model downloaded successfully.")

    model = load_model(model_path)
    model.eval()

    cap = get_camera()
    if cap is None:
        print("No camera found. Exiting.")
        exit(1)
    ret, frame = cap.read()
    if ret:
        frame_path = os.path.join(frames_dir, f"preview.jpeg")
        cv2.imwrite(frame_path, frame)
    
    start_time = time.time()
    frame_count = 0
    cat_detections = 0

    while True:
        frame = None
        ret, frame = cap.read()
    
        if not ret:
            log_statistics(stats_file, f"Error reading frame from camera. Trying again...")
            print("Error reading frame from camera. Trying again...")
            time.sleep(1)
            cap.release()
            cap = get_camera()
            if cap is None:
                print("No camera found. Exiting.")
                exit(1)
            continue

        frame_count += 1
        results = process_frame(frame, model)
        if save_frame_if_cat_detected(frame, results, frames_dir, stats_file, config['detection']['confidence_threshold']):
            cat_detections += 1
            # Assuming that cat detection threshold is lower that witch trigger
            trigger_witch_if_cat_detected(
                frame,
                results,
                frames_dir,
                stats_file,
                config
            )

        elapsed_time = time.time() - start_time
        if elapsed_time >= 600:  # 10 minutes
            fps = frame_count / elapsed_time
            stats = f"FPS: {fps:.2f}, Cat Detections: {cat_detections}"
            log_statistics(stats_file, stats)
            # Save a preview frame to know how the camera is positioned
            frame_path = os.path.join(frames_dir, f"preview.jpeg")
            cv2.imwrite(frame_path, frame)

            start_time = time.time()
            frame_count = 0
            cat_detections = 0


if __name__ == "__main__":
    lock_fd = prevent_multiple_instances()
    try:
        main()
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        cv2.destroyAllWindows()