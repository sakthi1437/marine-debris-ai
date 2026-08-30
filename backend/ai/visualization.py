import cv2


def annotate(image, detections):
    output = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    for item in detections:
        x1, y1, x2, y2 = [int(value) for value in item["bbox"]]
        label = f'{item["class_name"]} | {item["final_confidence"]:.0%} | {item["priority"]}'
        cv2.rectangle(output, (x1, y1), (x2, y2), (38, 220, 180), 2)
        cv2.putText(output, label, (x1, max(18, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, .52, (38, 220, 180), 1, cv2.LINE_AA)
    return output
