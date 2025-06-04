import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from formatter import _make_msg
from parser import MessageData, ThreadData


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

