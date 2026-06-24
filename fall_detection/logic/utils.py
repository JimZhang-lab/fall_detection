# logic/utils.py
import cv2
import numpy as np

def draw_boxes_on_image(image, boxes):
    for (xyxy, conf) in boxes:
        x1, y1, x2, y2 = map(int, xyxy)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 1)
        cv2.putText(image, f"fall {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    return image

def save_video(frames, output_path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()

def is_frame_static(prev_boxes, curr_boxes, iou_thresh=0.95):
    """
    如果前后帧的bbox几乎不变（IOU > 阈值），说明是静态帧
    """
    if not prev_boxes or not curr_boxes:
        return False  # 一方为空就不能判断为静态

    for prev_box, curr_box in zip(prev_boxes, curr_boxes):
        iou = calculate_iou(prev_box[0], curr_box[0])
        if iou < iou_thresh:
            return False
    return True

def calculate_iou(box1, box2):
    """
    计算两个xyxy框的IOU
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = max(0, (box1[2] - box1[0])) * max(0, (box1[3] - box1[1]))
    box2_area = max(0, (box2[2] - box2[0])) * max(0, (box2[3] - box2[1]))
    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0
    return inter_area / union_area
