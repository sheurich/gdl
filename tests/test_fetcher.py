import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fetcher
import requests


def test_fetch_requests_retries(monkeypatch):
    calls = []

    class DummyExc(requests.RequestException):
        pass

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        if len(calls) == 1:
            raise DummyExc("fail")
        class Resp:
            text = "ok"
            def raise_for_status(self):
                pass
        return Resp()

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    monkeypatch.setattr(fetcher.time, "sleep", lambda x: None)
    f = fetcher.Fetcher(fetcher.FetcherConfig(max_retries=2, delay=0))
    assert f.fetch_requests("http://example.com") == "ok"
    assert len(calls) == 2
