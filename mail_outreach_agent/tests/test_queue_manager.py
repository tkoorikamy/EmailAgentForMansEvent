from app.core.queue_manager import QueueManager


def test_queue_sends_only_selected_pending():
    jobs = [
        {"email": "a@test.com", "company": "A", "selected": True, "send_status": "pending"},
        {"email": "b@test.com", "company": "B", "selected": False, "send_status": "pending"},
        {"email": "c@test.com", "company": "C", "selected": True, "send_status": "sent"},
    ]
    logs = []

    def send_fn(_):
        return True, ""

    def on_update(_):
        pass

    QueueManager().run(jobs, 0, 10, send_fn, on_update, logs.append)
    assert jobs[0]["send_status"] == "sent"
    assert jobs[1]["send_status"] == "pending"
    assert jobs[2]["send_status"] == "sent"
    assert any("Выбрано 1 писем" in m for m in logs)
