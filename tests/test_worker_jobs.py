from uuid import uuid4

from app.worker.jobs import _wait_for_lesson_request


class FakeDb:
    def __init__(self, visible_after: int) -> None:
        self.visible_after = visible_after
        self.get_calls = 0
        self.rollback_calls = 0
        self.expire_all_calls = 0

    def expire_all(self) -> None:
        self.expire_all_calls += 1

    def get(self, model, item_id):
        self.get_calls += 1
        if self.get_calls >= self.visible_after:
            return object()
        return None

    def rollback(self) -> None:
        self.rollback_calls += 1


def test_wait_for_lesson_request_retries_until_visible(monkeypatch):
    sleeps = []
    monkeypatch.setattr("app.worker.jobs.time.sleep", sleeps.append)
    db = FakeDb(visible_after=3)

    found = _wait_for_lesson_request(db, uuid4(), attempts=5, delay_seconds=0.1)

    assert found is True
    assert db.get_calls == 3
    assert db.rollback_calls == 2
    assert db.expire_all_calls == 3
    assert sleeps == [0.1, 0.1]


def test_wait_for_lesson_request_returns_false_when_missing(monkeypatch):
    sleeps = []
    monkeypatch.setattr("app.worker.jobs.time.sleep", sleeps.append)
    db = FakeDb(visible_after=99)

    found = _wait_for_lesson_request(db, uuid4(), attempts=3, delay_seconds=0.1)

    assert found is False
    assert db.get_calls == 3
    assert db.rollback_calls == 3
    assert sleeps == [0.1, 0.1]
