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
    thread_id = "unknown_thread_id"
    thread_subject = "Unknown Subject"

    try:
        # Attempt to get metadata from the head of the first message pair,
        # assuming data[2][0][0] is a list of [head, body] message pairs.
        if (isinstance(data, list) and len(data) > 2 and
            isinstance(data[2], list) and len(data[2]) > 0 and
            isinstance(data[2][0], list) and len(data[2][0]) > 0 and
            isinstance(data[2][0][0], list) and len(data[2][0][0]) >= 2 and # data[2][0][0] is the first message pair [head, body]
            isinstance(data[2][0][0][0], list) and len(data[2][0][0][0]) > 5): # data[2][0][0][0] is head of first message

            first_message_head = data[2][0][0][0] # Path to head of the first message
            thread_id = str(first_message_head[1])
            thread_subject = str(first_message_head[5])
            logger.info("Extracted thread metadata from first message head.")
        else:
            # Fallback to a previously assumed path if the above structure isn't met
            logger.warning("Primary metadata path not found or incomplete, trying legacy path.")
            # This legacy path assumes data[2][0][0][0] is the first head element of a flat list of messages.
            # This was the original assumption before differentiating message list structures.
            legacy_thread_metadata_source = data[2][0][0][0]
            if isinstance(legacy_thread_metadata_source, list) and len(legacy_thread_metadata_source) > 5:
                 thread_id = str(legacy_thread_metadata_source[1])
                 thread_subject = str(legacy_thread_metadata_source[5])
                 logger.info("Extracted thread metadata from legacy path (e.g. flat list's first head).")
            else:
                logger.warning("Legacy metadata path also not viable. Using defaults.")
                # Defaults already set

    except (IndexError, TypeError) as e:
        logger.warning(f"Could not extract thread metadata: {e}. Using defaults.")
        # Defaults already set

    messages: List[MessageData] = []
    candidate_list = None

    # Populate potential_paths_to_try in a specific order of preference
    raw_potential_paths = []
    try:
        if isinstance(data, list) and len(data) > 2 and isinstance(data[2], list) and len(data[2]) > 0:
            path_2_0 = data[2][0]
            if isinstance(path_2_0, list):
                if len(path_2_0) > 1 and isinstance(path_2_0[1], list):
                    raw_potential_paths.append(path_2_0[1]) # data[2][0][1]
                raw_potential_paths.append(path_2_0)         # data[2][0]
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            raw_potential_paths.append(data[1])
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            raw_potential_paths.append(data[0])
        if isinstance(data, list) and len(data) > 2 and isinstance(data[2], list):
            raw_potential_paths.append(data[2])
    except (IndexError, TypeError):
        logger.warning("Error while populating potential paths for message list.", exc_info=True)

    # Deduplicate potential paths (list of lists is not hashable, so simple object ID check)
    seen_ids = set()
    potential_paths_to_try = []
    for p_list in raw_potential_paths:
        if id(p_list) not in seen_ids: # Check if this exact list object has been seen
             if isinstance(p_list, list): # Ensure it's actually a list before adding
                potential_paths_to_try.append(p_list)
                seen_ids.add(id(p_list))

    # Attempt 1: Find a list of [head,body] pairs.
    for path_candidate in potential_paths_to_try:
        if (path_candidate and isinstance(path_candidate, list) and len(path_candidate) > 0 and
            isinstance(path_candidate[0], list) and len(path_candidate[0]) >= 2 and # First item is a pair
            isinstance(path_candidate[0][0], list)): # And the head of that first pair is a list
            logger.info(f"Prioritized: Identified candidate message list (list of pairs) with {len(path_candidate)} pairs at path.")
            candidate_list = path_candidate
            break

    if not candidate_list: # If no list of pairs was found, try the broader check (original heuristic)
        for path_candidate in potential_paths_to_try:
            if path_candidate and isinstance(path_candidate, list) and len(path_candidate) > 0:
                if isinstance(path_candidate[0], (list, tuple)): # Original check: first element is a list/tuple
                    logger.info(f"Fallback: Identified candidate message list (broader check) with {len(path_candidate)} items at path.")
                    candidate_list = path_candidate
                    break
                elif all(isinstance(item, (list,tuple)) for item in path_candidate): # Original list of lists check
                     logger.info(f"Fallback: Identified candidate message list source (list of lists) with {len(path_candidate)} items at path.")
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
