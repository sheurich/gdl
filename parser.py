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
import time

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
    matches = DS6_RE.findall(html)
    if not matches:
        raise ValueError("ds:6 block not found")
    # Some pages include multiple ds:6 blocks. The last block usually
    # contains the most complete data, so return that one.
    return json.loads(matches[-1])


def parse_thread_list(html: str) -> tuple[list[str], str | None]:
    """Return thread paths and a next page token from a listing page."""
    data = _extract_ds6(html)
    threads = [f"c/{pair[0][1]}" for pair in data[2]]
    next_token = data[3] if len(data) > 3 else None
    return threads, next_token



def parse_thread(html: str) -> ThreadData:
    """Parse a single thread page and return structured data."""
    data = _extract_ds6(html)

    try:
        thread_metadata_source = data[2][0][0][0]
        thread_id = str(thread_metadata_source[1])
        thread_subject = str(thread_metadata_source[5])
    except (IndexError, TypeError) as e:
        logger.warning(f"Could not extract thread metadata: {e}. Using defaults.")
        thread_id = "unknown_thread_id" # Or derive from URL if possible later
        thread_subject = "Unknown Subject"

    messages: List[MessageData] = []

    candidate_list = None # Renamed from message_list_source for clarity before determining iterable_messages
    potential_paths_to_try = []
    try:
        if len(data) > 2 and len(data[2]) > 0 and len(data[2][0]) > 1 and isinstance(data[2][0][1], list):
            potential_paths_to_try.append(data[2][0][1])
        if len(data) > 1 and isinstance(data[1], list):
            potential_paths_to_try.append(data[1])
        if len(data) > 0 and isinstance(data[0], list):
            potential_paths_to_try.append(data[0])
        if len(data) > 2 and isinstance(data[2], list) : # Could data[2] itself be the list?
            # Avoid re-adding if data[2][0][1] was from data[2]
            if not (len(data[2]) > 0 and len(data[2][0]) > 1 and data[2][0][1] is data[2]):
                 potential_paths_to_try.append(data[2])
    except (IndexError, TypeError):
        pass # Path doesn't exist in a way we can use

    for path_candidate in potential_paths_to_try: # Renamed candidate to path_candidate for clarity
        if path_candidate and isinstance(path_candidate, list) and len(path_candidate) > 0:
            # Heuristic: check if elements look like messages (are lists/tuples themselves)
            if isinstance(path_candidate[0], (list, tuple)):
                logger.info(f"Identified candidate message list source with {len(path_candidate)} items.")
                candidate_list = path_candidate
                break
            # Adding a check if path_candidate itself is a list of lists, even if its first element is not a list/tuple
            # This could happen if the list is empty but still a valid container for messages.
            elif all(isinstance(item, (list,tuple)) for item in path_candidate):
                 logger.info(f"Identified candidate message list source (list of lists) with {len(path_candidate)} items.")
                 candidate_list = path_candidate
                 break


    iterable_messages = None
    if candidate_list:
        if isinstance(candidate_list, list) and len(candidate_list) == 1 and isinstance(candidate_list[0], list):
            iterable_messages = candidate_list[0]
            logger.info(f"Using inner list from candidate (length {len(iterable_messages)}) as message source.")
        elif isinstance(candidate_list, list): # Check if candidate_list itself is a list of messages
            iterable_messages = candidate_list
            logger.info(f"Using candidate list (length {len(iterable_messages)}) directly as message source.")

    if not iterable_messages: # Check if iterable_messages is None or empty
        logger.warning(f"Could not find or process a valid message list in thread JSON for thread {thread_id}.")
        return ThreadData(thread_id=thread_id, subject=thread_subject, messages=[])

    for entry_index, message_entry in enumerate(iterable_messages):
        if not (isinstance(message_entry, (list, tuple)) and len(message_entry) >= 2):
            logger.warning(f"Skipping message entry at index {entry_index} due to unexpected structure or insufficient length: {message_entry}")
            continue

        head = message_entry[0]
        body = message_entry[1]

        if not isinstance(head, (list, tuple)) or not isinstance(body, (list, tuple)):
            logger.warning(f"Skipping message entry at index {entry_index} because head or body is not a list/tuple. Head: {type(head)}, Body: {type(body)}")
            continue

        try:
            message_id = str(head[1]) if len(head) > 1 else "unknown_msg_id"
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting message_id: {e}. Defaulting to 'unknown_msg_id'.")
            message_id = "unknown_msg_id"

        try:
            sender = str(head[2][0][0]) if isinstance(head[2], (list, tuple)) and len(head[2]) > 0 and isinstance(head[2][0], (list, tuple)) and len(head[2][0]) > 0 else "Unknown Sender"
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting sender: {e}. Defaulting to 'Unknown Sender'.")
            sender = "Unknown Sender"

        try:
            timestamp_data = head[7][0] if isinstance(head[7], (list, tuple)) and len(head[7]) > 0 else None
            timestamp = float(timestamp_data) if timestamp_data is not None else time.time()
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting timestamp: {e}. Defaulting to current time.")
            timestamp = time.time()

        try:
            message_subject = str(head[5]) if len(head) > 5 else "No Subject"
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting message_subject: {e}. Defaulting to 'No Subject'.")
            message_subject = "No Subject"

        try:
            body_html = str(body[1][0][1][1]) if isinstance(body[1], (list, tuple)) and \
                                                 len(body[1]) > 0 and \
                                                 isinstance(body[1][0], (list, tuple)) and \
                                                 len(body[1][0]) > 0 and \
                                                 isinstance(body[1][0][1], (list, tuple)) and \
                                                 len(body[1][0][1]) > 1 else "<p>Body not found</p>"
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting body_html: {e}. Defaulting to '<p>Body not found</p>'.")
            body_html = "<p>Body not found</p>"

        try:
            parent_id = str(head[8]) if len(head) > 8 and head[8] else None
        except (IndexError, TypeError, ValueError) as e:
            logger.warning(f"Error extracting parent_id: {e}. Defaulting to None.")
            parent_id = None

        messages.append(
            MessageData(
                message_id=message_id,
                sender=sender,
                timestamp=timestamp,
                subject=message_subject,
                body_html=body_html,
                parent_id=parent_id,
            )
        )
    logger.info(f"Successfully parsed {len(messages)} messages for thread {thread_id}")
    return ThreadData(thread_id=thread_id, subject=thread_subject, messages=messages)
