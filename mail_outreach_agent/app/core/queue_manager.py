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

    def run(self, jobs: list[dict], delay_seconds: int, max_per_run: int, send_fn: Callable[[dict], tuple[bool, str]], on_update: Callable[[dict], None], log_fn: Callable[[str], None]):
        self.stopped = False
        sent_count = 0
        pending_jobs = [j for j in jobs if j.get("selected", True) and j.get("send_status", "pending") == "pending"]
        log_fn(f"Выбрано {len(pending_jobs)} писем")
        for job in pending_jobs:
            if self.stopped or sent_count >= max_per_run:
                break
            while self.paused and not self.stopped:
                time.sleep(0.3)
            if self.stopped:
                break
            log_fn(f"Отправляю письмо: {job.get('company', '')} / {job.get('email', '')}")
            ok, err = send_fn(job)
            if ok:
                job["send_status"] = "sent"
                job["error_message"] = ""
                job["sent_at"] = datetime.utcnow().isoformat()
                sent_count += 1
                log_fn("Успешно отправлено")
            else:
                job["send_status"] = "failed"
                job["error_message"] = err
                log_fn(f"Ошибка отправки: {err}")
            on_update(job)
            time.sleep(delay_seconds)
        log_fn("Очередь завершена")
