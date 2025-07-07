import requests
from app.services import http_utils

class DummyResponse:
    def __init__(self):
        self.called = False
    def raise_for_status(self):
        pass
    def json(self):
        return {"ok": True}


def test_request_with_retry(monkeypatch):
    session = requests.Session()
    attempts = {"count": 0}

    def fail_then_succeed(method, url, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise requests.RequestException("fail")
        return DummyResponse()

    monkeypatch.setattr(session, "request", fail_then_succeed)
    resp = http_utils.request_with_retry(session, "get", "http://test", retries=2, backoff_factor=0)
    assert isinstance(resp, DummyResponse)
    assert attempts["count"] == 2


def test_request_with_retry_failure(monkeypatch):
    session = requests.Session()
    def always_fail(method, url, **kwargs):
        raise requests.RequestException("fail")
    monkeypatch.setattr(session, "request", always_fail)
    try:
        http_utils.request_with_retry(session, "get", "http://test", retries=1, backoff_factor=0)
    except requests.RequestException:
        pass
    else:
        assert False, "expected exception"
