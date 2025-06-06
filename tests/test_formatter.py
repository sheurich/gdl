import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from formatter import _make_msg, write_mbox
from parser import MessageData, ThreadData
import time


def test_make_msg_plaintext():
    msg = _make_msg(
        MessageData(
            message_id="1",
            sender="user@example.com",
            timestamp=0,
            subject="Hello",
            body_html="<p>Hello</p>",
        ),
        group_email="group@example.com",
        text_format="plaintext",
    )
    out = msg.as_string()
    assert "SGVsbG8" not in out
    assert "Hello" in out


def test_from_line_contains_sender_and_timestamp(tmp_path):
    ts1 = 0
    ts2 = 60
    threads = [
        ThreadData(
            thread_id="t",
            subject="sub",
            messages=[
                MessageData(
                    message_id="1",
                    sender="alice@example.com",
                    timestamp=ts1,
                    subject="s1",
                    body_html="<p>a</p>",
                ),
                MessageData(
                    message_id="2",
                    sender="bob@example.com",
                    timestamp=ts2,
                    subject="s2",
                    body_html="<p>b</p>",
                ),
            ],
        )
    ]
    out_file = tmp_path / "out.mbox"
    write_mbox(threads, out_file, group_email="group@example.com", text_format="plaintext")
    data = out_file.read_text()
    assert f"From alice@example.com {time.asctime(time.gmtime(ts1))}" in data
    assert f"From bob@example.com {time.asctime(time.gmtime(ts2))}" in data

