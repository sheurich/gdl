import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from parser import _extract_ds6


def test_extract_ds6():
    html = "<script>AF_initDataCallback({key: 'ds:6', isError: false, data:[[\"x\"]], sideChannel:{}});</script>"
    assert _extract_ds6(html) == [["x"]]
