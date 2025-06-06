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
@click.argument("group_url")
@click.option("--output", "output_file", default="group_archive.mbox", type=click.Path(), help="Output mbox file path")
@click.option(
    "--limit",
    type=int,
    default=None,
    show_default="unlimited",
    help="Limit number of threads",
)
@click.option("--delay", type=float, default=1.0, show_default=True, help="Delay between requests in seconds")
@click.option("--load-wait", type=float, default=2.0, show_default=True, help="Extra wait after page load in seconds")
@click.option("--user-agent", default=None, help="Custom User-Agent string")
@click.option("--max-retries", type=int, default=3, show_default=True, help="Max retries on request failures")
@click.option("--headless/--no-headless", default=True, show_default=True, help="Run browser in headless mode")
@click.option("--text-format", type=click.Choice(["html", "markdown", "plaintext"]), default="html", show_default=True, help="Format for message bodies")
@click.option("--concurrency", type=int, default=1, show_default=True, help="Number of threads to fetch concurrently")
@click.option("--log-level", default="INFO", show_default=True, help="Logging level")
def cli(group_url: str, output_file: str, limit: int | None, delay: float, load_wait: float, user_agent: str | None, max_retries: int, headless: bool, text_format: str, concurrency: int, log_level: str) -> None:
    """Scrape a public Google Group and output an mbox file."""
    logging.basicConfig(level=getattr(logging, log_level.upper(
    ), logging.INFO), format="%(levelname)s: %(message)s")
    config = FetcherConfig(
        delay=delay,
        load_wait=load_wait,
        user_agent=user_agent or FetcherConfig.user_agent,
        max_retries=max_retries,
        headless=headless,
    )

    async def run() -> None:
        threads: List[ThreadData] = []
        async with Fetcher(config) as fetcher:
            semaphore = asyncio.Semaphore(concurrency)

            async def fetch_and_parse(url: str) -> ThreadData:
                async with semaphore:
                    logging.info("Fetching thread %s", url)
                    thread_html = await fetcher.fetch_playwright(url)
                    return parse_thread(thread_html)

            page_token: str | None = None
            while True:
                url = group_url
                if page_token:
                    url += ("&" if "?" in group_url else "?") + f"pageToken={page_token}"
                list_html = await fetcher.fetch_playwright(url)
                thread_urls, page_token = parse_thread_list(list_html)
                tasks = []
                for thread_url in thread_urls:
                    if limit and len(threads) + len(tasks) >= limit:
                        break
                    full_url = make_full_url(group_url, thread_url)
                    tasks.append(asyncio.create_task(fetch_and_parse(full_url)))
                if tasks:
                    threads.extend(await asyncio.gather(*tasks))
                if limit and len(threads) >= limit:
                    break
                if not page_token:
                    break
        write_mbox(threads, Path(output_file),
                   group_email="group@example.com", text_format=text_format)
        logging.info("Saved %d threads to %s", len(threads), output_file)

    asyncio.run(run())


if __name__ == "__main__":
    cli()
