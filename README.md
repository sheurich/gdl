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
- `--limit N` – maximum number of threads to fetch.
- `--delay SECONDS` – polite delay between requests.
- `--text-format {html,markdown,plaintext}` – format of message bodies.

**Disclaimer:** Google’s robots.txt disallows automated access to `/groups` and
scraping may violate Google’s Terms of Service. This tool is provided for
educational purposes only.
