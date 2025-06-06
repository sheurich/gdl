# Google Groups Scraper CLI

This project provides an experimental command line tool for exporting the
conversation history of a public Google Group to an mbox file. The approach is
based on the development plan in `PLAN.md` and relies on web scraping using
Playwright and BeautifulSoup.

```
Usage: python -m cli [OPTIONS] GROUP_URL
```

Common options include:

- `--output PATH` – where to write the resulting mbox file.
- `--limit N` – maximum number of threads to fetch (omit to fetch all).
- `--delay SECONDS` – polite delay between requests.
- `--text-format {html,markdown,plaintext}` – format of message bodies.
- `--user-agent STRING` – custom User-Agent header.
- `--max-retries N` – retry a failed request up to N times.
- `--headless/--no-headless` – toggle headless browser mode.
- `--concurrency N` – number of threads to fetch concurrently.
- `--log-level LEVEL` – logging verbosity (e.g. INFO, DEBUG).

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
