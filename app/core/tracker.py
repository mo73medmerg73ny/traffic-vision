from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

class VehicleTracker():
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = DeepSort(max_age=30)

    def process_frame(self, frame):
        detections = []

        results = self.model(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].to_list()
                cls = int(box.cls[0])
                class_name = self.model.names[cls]
                conf = float(box.conf[0])

                w = x2 - x1
                h = y2 - y1
                detections.append(
                    ([x1, y1, w, h], conf, class_name)
                )

        tracks = self.tracker.update_tracks(
            detections,
            frame= frame
        )

        output = []

        for track in tracks:
            if not track.is_confirmed():
                continue

            x1, y1, x2, y2 = track.to_ltrb()
            track_id = track.track_id

            output.append(
                (
                    x1,
                    y1,
                    x2,
                    y2,
                    track.get_det_class(),
                    track.det_conf,
                    track_id 
                )
            )

        return output

        

        