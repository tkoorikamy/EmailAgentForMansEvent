import time
from datetime import datetime
from typing import Callable


class QueueManager:
    def __init__(self):
        self.paused = False
        self.stopped = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.stopped = True

    def run(self, jobs: list[dict], delay_seconds: int, max_per_run: int, send_fn: Callable[[dict], None], on_update: Callable[[dict], None]):
        sent = 0
        for job in jobs:
            if self.stopped or sent >= max_per_run:
                break
            while self.paused and not self.stopped:
                time.sleep(0.3)
            if self.stopped:
                break
            if job.get("status") in {"invalid_email", "duplicate", "skipped"}:
                job["send_status"] = "skipped"
                on_update(job)
                continue
            try:
                send_fn(job)
                job["send_status"] = "sent"
                job["sent_at"] = datetime.utcnow().isoformat()
                sent += 1
            except Exception as exc:  # noqa: BLE001
                job["send_status"] = "failed"
                job["error_message"] = str(exc)
            on_update(job)
            time.sleep(delay_seconds)
