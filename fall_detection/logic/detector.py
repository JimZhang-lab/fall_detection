import os
import platform
import subprocess
import time
from datetime import datetime, timedelta

import cv2
import torch
from ultralytics import YOLO

from logic.utils import draw_boxes_on_image, is_frame_static


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PERSON_MODEL_PATH = os.path.join("assets", "yolov8n.pt")
person_model = YOLO(PERSON_MODEL_PATH).to(DEVICE)


def get_next_file_base(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    i = 1
    while True:
        name = f"{i:04d}"
        has_existing_file = any(
            os.path.exists(os.path.join(output_dir, f"{name}.{ext}"))
            for ext in ("txt", "mp4", "jpg")
        )
        if not has_existing_file:
            return name
        i += 1


def get_video_metadata(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = frame_count / fps if fps else 0
    cap.release()
    return fps, frame_count, duration_sec


def open_result(path):
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def detect_fall(
    path,
    model_path,
    output_subdir,
    use_filter_person=False,
    use_filter_static=False,
    log_area=None,
    frame_interval=1,
):
    start_time = time.time()
    fall_model = YOLO(model_path).to(DEVICE)
    output_dir = os.path.join("outputs", output_subdir)
    base_name = get_next_file_base(output_dir)
    log_path = os.path.join(output_dir, f"{base_name}.txt")
    is_video = path.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    log_lines = []
    detected_times = []

    if is_video:
        return detect_video(
            path=path,
            fall_model=fall_model,
            output_dir=output_dir,
            base_name=base_name,
            log_path=log_path,
            log_lines=log_lines,
            detected_times=detected_times,
            start_time=start_time,
            use_filter_person=use_filter_person,
            use_filter_static=use_filter_static,
            log_area=log_area,
            frame_interval=frame_interval,
        )

    return detect_image(path, fall_model, output_dir, base_name, log_path, log_lines, start_time, log_area)


def detect_video(
    path,
    fall_model,
    output_dir,
    base_name,
    log_path,
    log_lines,
    detected_times,
    start_time,
    use_filter_person,
    use_filter_static,
    log_area,
    frame_interval,
):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None

    metadata = get_video_metadata(path)
    if metadata is None:
        cap.release()
        return None

    fps, frame_count, duration_sec = metadata
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_video_path = os.path.join(output_dir, f"{base_name}.mp4")
    writer = cv2.VideoWriter(out_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    log_lines.extend(
        [
            f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"运行设备: {DEVICE}",
            f"输入视频: {path}",
            f"输出视频: {out_video_path}",
            f"视频时长: {timedelta(seconds=int(duration_sec))}",
            f"总帧数: {frame_count}",
            f"FPS: {fps}",
            f"每隔 {frame_interval} 帧检测一次",
            f"启用无人帧筛除: {'是' if use_filter_person else '否'}",
            f"启用静态帧筛除: {'是' if use_filter_static else '否'}",
            "-" * 40,
        ]
    )

    frame_index = 0
    no_person_frames = 0
    max_no_person = int(fps * 3)
    no_person_start_frame = None
    last_person_check = -999
    prev_fall_boxes = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        current_sec = int(frame_index / fps) if fps else 0

        if use_filter_person and (frame_index - last_person_check >= fps):
            last_person_check = frame_index
            result_person = person_model(frame, verbose=False)[0]
            has_person = any(int(b.cls[0]) == 0 for b in result_person.boxes)

            if not has_person:
                no_person_frames += fps
                if no_person_start_frame is None:
                    no_person_start_frame = frame_index
            else:
                if no_person_frames >= max_no_person:
                    start_sec = no_person_start_frame / fps
                    end_sec = frame_index / fps
                    msg = f"无人警告：{timedelta(seconds=int(start_sec))} - {timedelta(seconds=int(end_sec))}"
                    log_lines.append(msg)
                    if log_area:
                        log_area.append(msg)
                no_person_frames = 0
                no_person_start_frame = None

        if use_filter_person and no_person_frames >= max_no_person:
            writer.write(frame)
            continue

        fall_boxes = []
        if frame_index % frame_interval == 0:
            result_fall = fall_model(frame, verbose=False)[0]
            for box in result_fall.boxes:
                if int(box.cls[0]) == 0:
                    fall_boxes.append((box.xyxy[0].tolist(), float(box.conf[0])))

            if fall_boxes and (not detected_times or current_sec - detected_times[-1] >= 5):
                detected_times.append(current_sec)
                msg = f"跌倒检测：{timedelta(seconds=current_sec)}"
                log_lines.append(msg)
                if log_area:
                    log_area.append(msg)

        if use_filter_static and is_frame_static(prev_fall_boxes, fall_boxes):
            continue

        writer.write(draw_boxes_on_image(frame, fall_boxes))
        prev_fall_boxes = fall_boxes

    cap.release()
    writer.release()

    elapsed = time.time() - start_time
    log_lines.append(f"检测完成：总耗时 {elapsed:.2f} 秒")
    if log_area:
        log_area.append(f"检测完成，总耗时 {elapsed:.2f} 秒")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    play_video(out_video_path)
    return out_video_path


def detect_image(path, fall_model, output_dir, base_name, log_path, log_lines, start_time, log_area):
    image = cv2.imread(path)
    if image is None:
        return None

    results = fall_model(image, verbose=False)[0]
    boxes = [
        (box.xyxy[0].tolist(), float(box.conf[0]))
        for box in results.boxes
        if int(box.cls[0]) == 0
    ]

    out_path = os.path.join(output_dir, f"{base_name}.jpg")
    cv2.imwrite(out_path, draw_boxes_on_image(image, boxes))

    elapsed = time.time() - start_time
    log_lines.extend(
        [
            f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"运行设备: {DEVICE}",
            f"图像路径: {path}",
            f"输出图像: {out_path}",
            f"图像检测完成：耗时 {elapsed:.2f} 秒",
        ]
    )
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    if log_area:
        log_area.append(f"检测完成，总耗时 {elapsed:.2f} 秒")

    open_result(out_path)
    return out_path


def play_video(path):
    cap = cv2.VideoCapture(path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("检测结果回放", frame)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
