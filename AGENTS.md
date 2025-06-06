Coding Guidelines for Agents
============================

- **Testing**: Run `pytest` before each commit to ensure the parsing helpers and
  formatter behave as expected. Install dependencies listed in
  `requirements.txt` if necessary.
- **CLI Options**: Keep the `README.md` in sync with the options defined in
  `cli.py`. Document new flags or behaviour changes.
- **Scraping Caution**: The tool relies on Playwright-based scraping which may
  break when Google Groups changes. Update selectors in `parser.py` with care.
- **Documentation**: Update both `README.md` and `PLAN.md` when the project
  gains features or behaviour changes.
- After each iteration, revise this file, `README.md`, and `PLAN.md` if new insights or features are added.
