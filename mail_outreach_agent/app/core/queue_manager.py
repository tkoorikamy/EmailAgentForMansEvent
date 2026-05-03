import logging
import time
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(self):
        self.paused = False
        self.stopped = False

    def pause(self):
        self.paused = True
        logger.info("Sending queue paused")

    def resume(self):
        self.paused = False
        logger.info("Sending queue resumed")

    def stop(self):
        self.stopped = True
        logger.info("Sending queue stop requested")

    def reset(self):
        self.paused = False
        self.stopped = False

    def run(self, jobs: list[dict], delay_seconds: int, max_per_run: int, send_fn: Callable[[dict], None], on_update: Callable[[dict], None]):
        sent = 0
        logger.info("Queue started: jobs=%s delay=%ss max_per_run=%s", len(jobs), delay_seconds, max_per_run)
        for index, job in enumerate(jobs, start=1):
            if self.stopped or sent >= max_per_run:
                logger.info("Queue finished early: stopped=%s sent=%s", self.stopped, sent)
                break
            while self.paused and not self.stopped:
                time.sleep(0.3)
            if self.stopped:
                logger.info("Queue stopped before job #%s", index)
                break
            if job.get("status") in {"invalid_email", "duplicate", "skipped"}:
                job["send_status"] = "skipped"
                job["error_message"] = ""
                on_update(job)
                logger.info("Job skipped: %s (%s)", job.get("email"), job.get("status"))
                continue
            try:
                logger.info("Sending to %s (%s/%s)", job.get("email"), index, len(jobs))
                send_fn(job)
                job["send_status"] = "sent"
                job["error_message"] = ""
                job["sent_at"] = datetime.utcnow().isoformat()
                sent += 1
                logger.info("Sent successfully: %s", job.get("email"))
            except Exception as exc:  # noqa: BLE001
                job["send_status"] = "failed"
                job["error_message"] = str(exc)
                logger.exception("Sending failed for %s", job.get("email"))
            on_update(job)
            if delay_seconds > 0:
                time.sleep(delay_seconds)
        logger.info("Queue ended: sent=%s stopped=%s", sent, self.stopped)
