import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from parser import parse_thread


def build_html(data):
    json_data = json.dumps(data)
    return (
        "<script>AF_initDataCallback({key: 'ds:6', isError: false, "
        "data:" + json_data + ", sideChannel:{}});</script>"
    )


def test_parse_thread_basic():
    head1 = [0, "t1", [["alice@example.com"]], None, None, "Subject1", None, [0]]
    body1 = [None, [[None, [None, "<p>m1</p>"]]]]
    head2 = [0, "m2", [["bob@example.com"]], None, None, "Subject2", None, [60]]
    body2 = [None, [[None, [None, "<p>m2</p>"]]]]
    data = [None, None, [[[head1, body1, head2, body2]]]]
    html = build_html(data)
    thread = parse_thread(html)
    assert thread.thread_id == "t1"
    assert thread.subject == "Subject1"
    assert len(thread.messages) == 2
    assert thread.messages[1].subject == "Subject2"
    assert thread.messages[1].body_html == "<p>m2</p>"
