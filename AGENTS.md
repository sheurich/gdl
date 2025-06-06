---
name: "Google Groups Scraper CLI"
description: "Command-line tool for archiving public Google Group discussions to an mbox file via Playwright-driven scraping."
category: "Web Scraping Tools"
author: "Shiloh Heurich"
authorUrl: ""
tags: ["python", "scraper", "cli", "playwright"]
lastUpdated: "2025-06-06"
---

# Google Groups Scraper CLI

## Project Overview

This project provides a Python-based command line application that exports the conversation history of a public Google Group to an mbox file. It relies on Playwright to load pages, uses custom parsers to extract thread data, and can output message bodies as HTML, Markdown, or plaintext. The tool is meant for archiving or analysis when no official API is available.

Scraping Google Groups is discouraged by Google's robots.txt and Terms of Service. Use this repository for educational exploration only and expect that selectors will break as Google updates the interface.

## Tech Stack

- **Frontend**: N/A (terminal based)
- **Backend**: Python 3 with Playwright, Requests, and BeautifulSoup
- **Database**: None
- **Deployment**: Run locally with Python
- **Other Tools**: Click for CLI, pytest for tests, [`uv`](https://github.com/astral-sh/uv) for dependency management

## Project Structure

```
project-root/
├── cli.py
├── fetcher.py
├── parser.py
├── formatter.py
├── tests/
├── PLAN.md
├── README.md
└── requirements.txt
```

## Development Guidelines

### Project Policies

- Run `pytest` before every commit to ensure parsing helpers and the formatter work correctly. Install packages from `requirements.txt` if needed.
- Use [`uv`](https://github.com/astral-sh/uv) to run tests: `uv run --with-requirements=requirements.txt pytest`.
- Keep `README.md` aligned with the CLI options in `cli.py`. Document any new flags or behaviour changes.
- Update selectors in `parser.py` carefully if Google Groups markup changes.
- Whenever features change, update `README.md`, `PLAN.md`, and this file.
- Scraping Google Groups may violate Google's Terms of Service and robots.txt. Proceed only on groups you control or for personal experimentation.

### Code Style

- Use consistent code formatting tools
- Follow language-specific best practices
- Keep code clean and readable

### Naming Conventions

- File naming:
- Variable naming:
- Function naming:
- Class naming:

### Git Workflow

- Branch naming conventions
- Commit message format
- Pull Request process

## Environment Setup

### Development Requirements

- Python version: 3.11 or later
- Package manager: `pip` or [`uv`](https://github.com/astral-sh/uv)
- Other dependencies: see `requirements.txt`

### Installation Steps

```bash
# 1. Clone the project
git clone [repository-url]

# 2. Install uv and Playwright
pip install uv
uv tool install playwright
playwright install

# 3. Run tests to verify setup
uv run --with-requirements=requirements.txt pytest

# 4. Execute the scraper
uv run --with-requirements=requirements.txt cli.py <GROUP_URL>
```

## Core Feature Implementation

### Fetching Pages

`fetcher.py` wraps Playwright and handles polite retry logic. The `FetcherConfig`
object controls request delays, load wait time, custom User-Agent, and retry
counts.

### Parsing Threads

`parser.py` extracts Google Group thread data from the `ds:6` script blocks on
each page. It consolidates multiple blocks when present so no messages are lost.

### Writing Mbox Files

`formatter.py` converts parsed threads to standard mbox format using
`mailbox.mbox`. The CLI invokes `write_mbox()` after scraping is complete.

## Testing Strategy

### Unit Testing

- Testing framework: `pytest`
- Test coverage requirements: none enforced, but contributions should include tests where feasible.
- Test file organization: tests live in the `tests/` directory alongside helper modules.

### Integration Testing

- Test scenarios: limited smoke tests using the CLI on a small group
- Testing tools: Playwright driven by the `Fetcher` class

### End-to-End Testing

- Test workflow: manual invocation of `cli.py` with real group URLs to verify scraping works end to end
- Automation tools: none

## Deployment Guide

### Build Process

No build step is required. The CLI runs directly with Python.

### Deployment Steps

1. Prepare production environment
2. Configure environment variables
3. Execute deployment scripts
4. Verify deployment results

### Environment Variables

This project does not require environment variables by default.

## Performance Optimization

### Frontend Optimization

N/A – the tool is a command line interface.

### Backend Optimization

- Configurable request delays and retry limits to reduce load on Google servers
- Optional concurrency setting for faster scraping with caution
- Minimal caching to avoid hitting the same page repeatedly

## Security Considerations

### Data Security

- Input validation
- SQL injection protection
- XSS protection

Scraped data may include personal information. Handle archives responsibly and respect privacy.

### Authentication & Authorization

- User authentication flow
- Permission control
- Token management

No authentication is required for scraping public groups, but confirm you have permission to access the data. Review Google's Terms of Service and robots.txt before running the scraper.

## Monitoring and Logging

### Application Monitoring

- Performance metrics
- Error tracking
- User behavior analytics

### Log Management

- Log levels
- Log format
- Log storage

## Common Issues

### Issue 1: Selectors no longer match Google Groups markup

**Solution**: Inspect the live page with browser dev tools and update `parser.py`
selectors accordingly. Run the tests before committing.

### Issue 2: Playwright fails to launch or times out

**Solution**: Ensure browsers are installed with `playwright install` and check
network connectivity. Increase the `--load-wait` option if pages load slowly.

## Reference Resources

- [Playwright Python](https://playwright.dev/python/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Python mailbox module](https://docs.python.org/3/library/mailbox.html)
- [Google Groups Help](https://support.google.com/groups)

## Changelog

### v1.0.0 (YYYY-MM-DD)

- Initial release
- Implemented basic features

---

**Note**: Please adjust and improve the above content according to the specific project type, remove inapplicable sections, and add project-specific content.
