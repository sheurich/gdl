# Google Groups Scraper CLI

This project provides an experimental command line tool for exporting messages
from a public Google Group (by providing `GROUP_URL`) or a specific Google
Group thread (by using the `--thread-url` option) to an mbox file. The approach
is based on the development plan in `PLAN.md` and relies on web scraping using
Playwright and BeautifulSoup.

```
Usage: python -m cli [OPTIONS] GROUP_URL
```
The tool can be run by specifying a `GROUP_URL` (the URL of the main group page)
as a positional argument, or by using the `--thread-url` option to target a
single thread.

Common options include (defaults in parentheses):

- `--output PATH` – where to write the resulting mbox file *(default: `group_archive.mbox`)*.
- `--thread-url THREAD_URL` – URL of a single Google Groups thread to scrape. If this option is used, the `GROUP_URL` positional argument should be omitted.
- `--limit N` – maximum number of threads to fetch when processing a `GROUP_URL` *(default: unlimited)*.
- `--delay SECONDS` – polite delay between requests *(default: 1.0)*.
- `--load-wait SECONDS` – extra wait after each page load *(default: 2.0)*.
- `--text-format {html,markdown,plaintext}` – format of message bodies *(default: `html`)*.
- `--user-agent STRING` – custom User-Agent header *(default: built‑in Chrome user agent)*.
- `--max-retries N` – retry a failed request up to N times *(default: 3)*.
- `--headless/--no-headless` – toggle headless browser mode *(default: headless)*.
- `--concurrency N` – number of threads to fetch concurrently when processing a `GROUP_URL` *(default: 1)*.
- `--log-level LEVEL` – logging verbosity, e.g. INFO or DEBUG *(default: `INFO`)*.

### Setup

Install the Python packages using [`uv`](https://github.com/astral-sh/uv):

```bash
# install uv if not already present
pip install uv

# install playwright and browser binaries
uv tool install playwright
playwright install
```

Run the scraper with uv so dependencies are resolved from `requirements.txt`:

```bash
uv run --with-requirements=requirements.txt cli.py <GROUP_URL>
```
To scrape a single thread:
```bash
uv run --with-requirements=requirements.txt cli.py --thread-url <THREAD_URL>
```

**Disclaimer:** Google’s robots.txt disallows automated access to `/groups` and
scraping may violate Google’s Terms of Service. This tool is provided for
educational purposes only.

### Running Tests

Run the unit tests without modifying your environment using
[`uv`](https://github.com/astral-sh/uv):

```bash
uv run --with-requirements=requirements.txt pytest
```

Tests run automatically on every push via the GitHub Actions workflow in
`.github/workflows/tests.yml`.

Alternatively, install the dependencies and run `pytest` directly:

```bash
pip install -r requirements.txt
pytest
```

### Development Notes

- The parser extracts the last `ds:6` script block found in each page to ensure all messages are captured.
- When extending functionality, update this README, `AGENTS.md`, and `PLAN.md` so future contributors understand recent changes.
