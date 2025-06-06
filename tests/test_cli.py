import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from click.testing import CliRunner
import cli
from parser import ThreadData


def test_concurrency_option(monkeypatch, tmp_path):
    sem_values = []
    orig_sem = cli.asyncio.Semaphore

    def capturing_semaphore(value):
        sem_values.append(value)
        return orig_sem(value)

    class DummyFetcher:
        def __init__(self, config=None):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def fetch_playwright(self, url: str) -> str:
            return ""

    def fake_parse_list(html):
        return ["c/a", "c/b"], None

    def fake_parse_thread(html):
        return ThreadData("id", "subject", [])

    def fake_write_mbox(threads, path, group_email, text_format):
        pass

    monkeypatch.setattr(cli, "Fetcher", DummyFetcher)
    monkeypatch.setattr(cli, "parse_thread_list", fake_parse_list)
    monkeypatch.setattr(cli, "parse_thread", fake_parse_thread)
    monkeypatch.setattr(cli, "write_mbox", fake_write_mbox)
    monkeypatch.setattr(cli.asyncio, "Semaphore", capturing_semaphore)

    out_file = tmp_path / "out.mbox"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["http://example.com", "--concurrency", "2", "--output", str(out_file)])
    assert result.exit_code == 0
    assert sem_values == [2]


def test_load_wait_option(monkeypatch, tmp_path):
    configs = []

    class DummyFetcher:
        def __init__(self, config=None):
            configs.append(config)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def fetch_playwright(self, url: str) -> str:
            return ""

    def fake_parse_list(html):
        return [], None

    def fake_write_mbox(threads, path, group_email, text_format):
        pass

    monkeypatch.setattr(cli, "Fetcher", DummyFetcher)
    monkeypatch.setattr(cli, "parse_thread_list", fake_parse_list)
    monkeypatch.setattr(cli, "parse_thread", lambda html: ThreadData("id", "s", []))
    monkeypatch.setattr(cli, "write_mbox", fake_write_mbox)

    out_file = tmp_path / "out.mbox"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["http://example.com", "--load-wait", "0.5", "--output", str(out_file)])
    assert result.exit_code == 0
    assert configs and abs(configs[0].load_wait - 0.5) < 1e-6

