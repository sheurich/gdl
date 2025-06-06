"""Convert parsed Google Group data into an mbox file."""
from __future__ import annotations

import mailbox
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from html2text import html2text

from parser import MessageData, ThreadData


def _make_msg(message: MessageData, group_email: str, text_format: str) -> mailbox.mboxMessage:
    msg = mailbox.mboxMessage()
    ts = message.timestamp
    ts_struct = time.gmtime(ts)
    rfc822_ts = time.strftime("%a, %d %b %Y %H:%M:%S +0000", ts_struct)
    # Set both the envelope "From " line and standard Date header
    msg.set_from(message.sender, ts_struct)
    msg.set_unixfrom(f"From {message.sender} {time.asctime(ts_struct)}")
    msg["From"] = message.sender
    msg["To"] = group_email
    msg["Subject"] = message.subject
    msg["Date"] = rfc822_ts
    msg["Message-ID"] = f"<{message.message_id}@scraped.local>"
    if message.parent_id:
        msg["In-Reply-To"] = f"<{message.parent_id}@scraped.local>"
    body = message.body_html
    if text_format == "markdown":
        body = html2text(body)
    elif text_format == "plaintext":
        body = html2text(body)
        body = body.replace("*", "")
    content_type = "text/html" if text_format == "html" else "text/plain"
    msg["Content-Type"] = f"{content_type}; charset=utf-8"
    msg["Content-Transfer-Encoding"] = "8bit"
    msg.set_payload(body.encode("utf-8"))
    return msg


def write_mbox(threads: Iterable[ThreadData], output_path: Path, group_email: str, text_format: str = "html") -> None:
    mbox = mailbox.mbox(output_path)
    for thread in threads:
        for message in thread.messages:
            mbox.add(_make_msg(message, group_email, text_format))
    mbox.flush()
    mbox.close()
