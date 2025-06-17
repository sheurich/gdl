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
    head1 = [0, "t1", [["alice@example.com"]], None, None, "Subject1", None, [0], "p_none"] # Added parent_id
    body1 = [None, [[None, [None, "<p>m1</p>"]]]]
    head2 = [0, "m2", [["bob@example.com"]], None, None, "Subject2", None, [60], "t1"] # Added parent_id
    body2 = [None, [[None, [None, "<p>m2</p>"]]]]

    # This structure makes data[2][0] the list of message pairs.
    # The parser should identify data[2][0] as candidate_list, then iterable_messages.
    # Metadata should be extracted from head1 (via data[2][0][0][0]).
    messages_list = [[head1, body1], [head2, body2]]
    data = [None, None, [messages_list]]

    html = build_html(data)
    thread = parse_thread(html)

    assert thread.thread_id == "t1"
    assert thread.subject == "Subject1"
    assert len(thread.messages) == 2

    msg1 = thread.messages[0]
    assert msg1.message_id == "t1"
    assert msg1.sender == "alice@example.com"
    assert msg1.timestamp == 0.0
    assert msg1.subject == "Subject1"
    assert msg1.body_html == "<p>m1</p>"
    assert msg1.parent_id == "p_none"

    msg2 = thread.messages[1]
    assert msg2.message_id == "m2"
    assert msg2.sender == "bob@example.com"
    assert msg2.timestamp == 60.0
    assert msg2.subject == "Subject2"
    assert msg2.body_html == "<p>m2</p>"
    assert msg2.parent_id == "t1"
