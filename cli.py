"""Command line interface for scraping Google Groups."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List

import click

from fetcher import Fetcher, FetcherConfig
from formatter import write_mbox
from parser import parse_thread, parse_thread_list, ThreadData
from urllib.parse import urlparse, urljoin


# make_full_url is only used when group_url is provided.
def make_full_url(base_url: str, thread_path: str) -> str:
    """Join a thread path to the group URL."""
    if thread_path.startswith("http://") or thread_path.startswith("https://"):
        return thread_path
    parsed = urlparse(base_url)
    if thread_path.startswith("/"):
        return f"{parsed.scheme}://{parsed.netloc}{thread_path}"
    base = base_url if base_url.endswith("/") else base_url + "/"
    return urljoin(base, thread_path)


@click.command()
@click.argument("group_url", required=False, default=None) # Now optional
@click.option("--output", "output_file", default="group_archive.mbox", type=click.Path(), help="Output mbox file path")
@click.option(
    "--limit",
    "limit_option", # Renamed to avoid conflict with builtin
    type=int,
    default=None,
    show_default="unlimited",
    help="Limit number of threads (only applies when GROUP_URL is used).",
)
@click.option("--delay", type=float, default=1.0, show_default=True, help="Delay between requests in seconds")
@click.option("--load-wait", type=float, default=2.0, show_default=True, help="Extra wait after page load in seconds")
@click.option("--user-agent", default=None, help="Custom User-Agent string")
@click.option("--max-retries", type=int, default=3, show_default=True, help="Max retries on request failures")
@click.option("--headless/--no-headless", default=True, show_default=True, help="Run browser in headless mode")
@click.option("--text-format", type=click.Choice(["html", "markdown", "plaintext"]), default="html", show_default=True, help="Format for message bodies")
@click.option("--concurrency", "concurrency_option", type=int, default=1, show_default=True, help="Number of threads to fetch concurrently (only applies when GROUP_URL is used).")
@click.option("--log-level", default="INFO", show_default=True, help="Logging level")
@click.option("--thread-url", "thread_url_option", default=None, type=str, help="URL of a single Google Groups thread to scrape.")
def cli(group_url: str | None, output_file: str, limit_option: int | None, delay: float, load_wait: float, user_agent: str | None, max_retries: int, headless: bool, text_format: str, concurrency_option: int, log_level: str, thread_url_option: str | None) -> None:
    """Scrape a public Google Group or a single thread and output an mbox file."""
    if not group_url and not thread_url_option:
        raise click.UsageError("Either GROUP_URL argument or --thread-url option must be provided.")
    if group_url and thread_url_option:
        # Or, could define precedence, e.g. thread_url takes over. For now, mutual exclusivity.
        raise click.UsageError("GROUP_URL argument and --thread-url option are mutually exclusive.")

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s:%(name)s:%(message)s", # Added logger name
    )
    fetch_config = FetcherConfig(
        delay=delay,
        load_wait=load_wait,
        user_agent=user_agent or FetcherConfig.user_agent,
        max_retries=max_retries,
        headless=headless,
    )
    output_file_path = Path(output_file)

    asyncio.run(run(
        group_url_arg=group_url,
        output_file_path=output_file_path,
        limit_arg=limit_option,
        fetch_config=fetch_config,
        text_format_arg=text_format,
        concurrency_arg=concurrency_option,
        thread_url_arg=thread_url_option
    ))


async def run(
    group_url_arg: str | None,
    output_file_path: Path,
    limit_arg: int | None,
    fetch_config: FetcherConfig,
    text_format_arg: str,
    concurrency_arg: int,
    thread_url_arg: str | None,
) -> None:
    """Core asynchronous scraping logic."""
    final_threads_data: List[ThreadData] = []
    group_email_for_mbox = "unknown@example.com" # Default

    async with Fetcher(fetch_config) as fetcher:
        # fetch_and_parse can use 'fetcher' from this outer scope
        async def fetch_and_parse(url: str) -> ThreadData | None: # Allow None return for error cases
            logging.info("Fetching thread %s", url)
            try:
                thread_html = await fetcher.fetch_playwright(url)
                return parse_thread(thread_html)
            except Exception as e:
                logging.error(f"Failed to fetch or parse thread {url}: {e}")
                return None

        if thread_url_arg:
            logging.info(f"Processing single thread: {thread_url_arg}")
            thread_data = await fetch_and_parse(thread_url_arg)
            if thread_data:
                final_threads_data.append(thread_data)
            group_email_for_mbox = "thread@example.com" # Placeholder for single thread

        elif group_url_arg:
            # Logic for processing a group
            group_name = urlparse(group_url_arg).path.split('/g/')[-1].split('/')[0] if '/g/' in group_url_arg else 'group'
            group_email_for_mbox = f"{group_name}@example.com"

            semaphore = asyncio.Semaphore(concurrency_arg)
            async def fetch_and_parse_with_semaphore(url: str) -> ThreadData | None:
                async with semaphore:
                    return await fetch_and_parse(url)

            page_token: str | None = None
            threads_processed_count = 0
            while True:
                current_page_url = group_url_arg
                if page_token:
                    # Ensure pageToken is appended correctly, handling existing query params
                    if "?" in current_page_url:
                        current_page_url += f"&pageToken={page_token}"
                    else:
                        current_page_url += f"?pageToken={page_token}"

                logging.info(f"Fetching thread list from: {current_page_url}")
                try:
                    list_html = await fetcher.fetch_playwright(current_page_url)
                    listed_thread_relative_urls, page_token = parse_thread_list(list_html)
                except ValueError as e: # ds:6 block not found or other parsing error
                    logging.error(f"Failed to parse thread list from {current_page_url}: {e}. Is it a valid group page URL?")
                    break # Stop processing if list page is invalid

                if not listed_thread_relative_urls:
                    logging.info(f"No threads found on page {current_page_url}.")
                    # This might be the end, or just an empty page. Let page_token decide.

                tasks = []
                for rel_url in listed_thread_relative_urls:
                    if limit_arg and threads_processed_count + len(tasks) >= limit_arg:
                        break
                    full_url = make_full_url(group_url_arg, rel_url)
                    tasks.append(asyncio.create_task(fetch_and_parse_with_semaphore(full_url)))

                if tasks:
                    results = await asyncio.gather(*tasks)
                    for res in results:
                        if res: # Ensure only valid ThreadData objects are added
                            final_threads_data.append(res)
                            threads_processed_count +=1 # Count successfully processed threads

                if limit_arg and threads_processed_count >= limit_arg:
                    logging.info(f"Reached thread limit of {limit_arg}.")
                    break
                if not page_token:
                    logging.info("No more pages of threads.")
                    break

        else:
            # This case should be prevented by click validation
            logging.error("Neither group_url nor thread_url was provided to run(). This should not happen.")
            return

    write_mbox(final_threads_data, output_file_path, group_email=group_email_for_mbox, text_format=text_format_arg)
    logging.info("Saved %d threads to %s", len(final_threads_data), output_file_path)


if __name__ == "__main__":
    cli()
