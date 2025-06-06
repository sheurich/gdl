# Google Groups Scraper CLI

This project provides an experimental command line tool for exporting the
conversation history of a public Google Group to an mbox file. The approach is
based on the development plan in `PLAN.md` and relies on web scraping using
Playwright and BeautifulSoup.

```
Usage: python -m cli [OPTIONS] GROUP_URL
```

Common options include (defaults in parentheses):

- `--output PATH` – where to write the resulting mbox file *(default: `group_archive.mbox`)*.
- `--limit N` – maximum number of threads to fetch *(default: unlimited)*.
- `--delay SECONDS` – polite delay between requests *(default: 1.0)*.
- `--load-wait SECONDS` – extra wait after each page load *(default: 2.0)*.
- `--text-format {html,markdown,plaintext}` – format of message bodies *(default: `html`)*.
- `--user-agent STRING` – custom User-Agent header *(default: built‑in Chrome user agent)*.
- `--max-retries N` – retry a failed request up to N times *(default: 3)*.
- `--headless/--no-headless` – toggle headless browser mode *(default: headless)*.
- `--concurrency N` – number of threads to fetch concurrently *(default: 1)*.
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

**Disclaimer:** Google’s robots.txt disallows automated access to `/groups` and
scraping may violate Google’s Terms of Service. This tool is provided for
educational purposes only.

### Running Tests

Install the dependencies from `requirements.txt` and run `pytest`:

```bash
pip install -r requirements.txt
pytest
```
