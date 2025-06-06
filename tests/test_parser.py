import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from parser import _extract_ds6, parse_thread_list


def test_extract_ds6():
    html = "<script>AF_initDataCallback({key: 'ds:6', isError: false, data:[[\"x\"]], sideChannel:{}});</script>"
    assert _extract_ds6(html) == [["x"]]


def test_extract_ds6_multiple_blocks():
    html = (
        "<script>AF_initDataCallback({key: 'ds:6', isError: false, data:[[\"x\"]], sideChannel:{}});</script>"
        "<script>AF_initDataCallback({key: 'ds:6', isError: false, data:[[\"y\"]], sideChannel:{}});</script>"
    )
    assert _extract_ds6(html) == [["y"]]


def test_parse_thread_list_token():
    html = (
        "<script>AF_initDataCallback({key: 'ds:6', isError: false, "
        "data:[[], 0, [[[0,\"a\"],0],[[0,\"b\"],0]], \"NEXT\"], sideChannel:{}});"\
        "</script>"
    )
    threads, token = parse_thread_list(html)
    assert threads == ["c/a", "c/b"]
    assert token == "NEXT"
