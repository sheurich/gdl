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

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Example CSS selectors. These will likely need to be updated for real pages.
# Selectors tuned for the current Google Groups frontend.
THREAD_URL_RE = re.compile(r'/(?:[^/]+/)?c/[A-Za-z0-9_-]+')
MESSAGE_CONTAINER_SELECTOR = 'section[data-doc-id]'
SENDER_SELECTOR = 'h3'
TIMESTAMP_SELECTOR = 'span.zX2W9c'
BODY_SELECTOR = 'div[style*=\"word-wrap:break-word\"]'


@dataclass
class MessageData:
    message_id: str
    sender: str
    timestamp: str
    subject: str
    body_html: str
    parent_id: Optional[str]


@dataclass
class ThreadData:
    thread_id: str
    subject: str
    messages: List[MessageData]


def parse_thread_list(html: str) -> Iterable[str] :
    """Return relative paths to threads extracted from a listing page."""
    for match in THREAD_URL_RE.finditer(html):
        yield match.group(0)



def parse_thread(html: str) -> ThreadData:
    """Parse a single thread page and return structured data."""
    soup = BeautifulSoup(html, 'lxml')
    subject = soup.title.string if soup.title else ''
    canonical = soup.find('link', rel='canonical')
    thread_id = canonical['href'].rstrip('/').split('/')[-1] if canonical else 'unknown'

    messages: List[MessageData] = []
    for container in soup.select(MESSAGE_CONTAINER_SELECTOR):
        msg_id = container.get('data-message-id', '')
        sender_el = container.select_one(SENDER_SELECTOR)
        timestamp_el = container.select_one(TIMESTAMP_SELECTOR)
        body_el = container.select_one(BODY_SELECTOR)
        msg = MessageData(
            message_id=msg_id,
            sender=sender_el.get_text(strip=True) if sender_el else '' ,
            timestamp=timestamp_el.get_text(strip=True) if timestamp_el else '' ,
            subject=subject,
            body_html=str(body_el) if body_el else '' ,
            parent_id=None,
        )
        messages.append(msg)
    return ThreadData(thread_id=thread_id, subject=subject, messages=messages)
