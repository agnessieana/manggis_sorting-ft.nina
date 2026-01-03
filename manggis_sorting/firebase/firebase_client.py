import requests
import time

class FirebaseClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def update_last_grade(self, grade):
        data = {
            "last_grade": int(grade),
            "timestamp": int(time.time())
        }
        requests.put(f"{self.base_url}/grading.json", json=data)

    def update_summary(self, grade):
        url = f"{self.base_url}/summary/grade_{grade}.json"
        r = requests.get(url)
        count = r.json() if r.ok and r.json() else 0
        requests.put(url, json=count + 1)

    def add_grading_result(
        self,
        device_id,
        grade,
        grade_label,
        features,
        roi,
        purple_ratio
    ):
        data = {
            "device_id": device_id,
            "grade": int(grade),
            "grade_label": grade_label,
            "purple_ratio": float(purple_ratio),
            "roi_area": int(roi[2] * roi[3]),
            "roi": {
                "x": roi[0], "y": roi[1],
                "w": roi[2], "h": roi[3]
            },
            "features": features,
            "timestamp": int(time.time())
        }

        requests.post(
            f"{self.base_url}/grading_results.json",
            json=data
        )
