"""Parse Google Group pages to extract thread and message data.

Due to variations in Google Groups HTML, selector constants are placed in this
module for easier future updates. Currently they serve as placeholders and may
require adjustment after inspecting the live site.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional
import re

import json

logger = logging.getLogger(__name__)

# Example CSS selectors. These will likely need to be updated for real pages.
# Selectors tuned for the current Google Groups frontend.
# The ds:6 block contains JSON data embedded in a script tag. The "data:" array
# is followed by a "sideChannel:" object. We capture everything up to that
# boundary so the JSON string can be loaded reliably even when it spans many
# lines.
DS6_RE = re.compile(
    r"AF_initDataCallback\(\{key: 'ds:6',[^,]*,\s*data:(\[.*?\])\s*,\s*sideChannel",
    re.DOTALL,
)


@dataclass
class MessageData:
    message_id: str
    sender: str
    timestamp: float
    subject: str
    body_html: str
    parent_id: Optional[str] = None


@dataclass
class ThreadData:
    thread_id: str
    subject: str
    messages: List[MessageData]


def _extract_ds6(html: str) -> list:
    match = DS6_RE.search(html)
    if not match:
        raise ValueError("ds:6 block not found")
    return json.loads(match.group(1))


def parse_thread_list(html: str) -> tuple[list[str], str | None]:
    """Return thread paths and a next page token from a listing page."""
    data = _extract_ds6(html)
    threads = [f"c/{pair[0][1]}" for pair in data[2]]
    next_token = data[3] if len(data) > 3 else None
    return threads, next_token



def parse_thread(html: str) -> ThreadData:
    """Parse a single thread page and return structured data."""
    data = _extract_ds6(html)
    thread_id = data[2][0][0][0][1]
    subject = data[2][0][0][0][5]
    messages: List[MessageData] = []
    pairs = data[2][0][0]
    for i in range(0, len(pairs), 2):
        head = pairs[i]
        if i + 1 >= len(pairs):
            break
        body = pairs[i + 1]
        message_id = head[1]
        sender = head[2][0][0]
        timestamp = float(head[7][0])
        body_html = body[1][0][1][1]
        messages.append(
            MessageData(
                message_id=message_id,
                sender=sender,
                timestamp=timestamp,
                subject=head[5],
                body_html=body_html,
            )
        )
    return ThreadData(thread_id=thread_id, subject=subject, messages=messages)
