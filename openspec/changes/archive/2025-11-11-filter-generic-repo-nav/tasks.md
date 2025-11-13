## 1. Implementation
- [x] 1.1 Expand `_REPO_NAV_PATH_PREFIXES` in `enrich/scraper.py` to include /releases, /tags, /commits, /commit, /compare, /branches, /branch, /contributors, /stargazers, /watchers, /forks, /milestones, /labels, and Bitbucket /pull-requests
- [x] 1.2 Expand `_REPO_NAV_TEXT` set to include "releases", "release", "tags", "commits", "branches", "contributors", "stargazers", "watchers", "forks", "milestones", "labels"
- [x] 1.3 Add `_is_github_global_nav_link()` helper that detects docs.github.com, support.github.com, github.blog, and GitHub.com global paths (/features, /enterprise, /about, /blog, /changelog, /pricing, /explore, /trending, /solutions, etc.)
- [x] 1.4 Integrate `_is_github_global_nav_link()` check into `extract_metadata()` before adding links to documentation list
- [x] 1.5 Fix indentation bug in `extract_metadata()` so global nav check executes independently
- [x] 1.6 Fix `_is_repo_navigation_link()` to handle repo-specific paths (e.g., `/org/repo/issues`) by checking path endings and segments, not just prefixes
- [x] 1.7 Run pytest suite to validate no regressions in scraper behavior
- [x] 1.8 Manually test scraping computproteomics/vsclust GitHub repo homepage to confirm generic nav links are excluded from documentation list

## 2. Spec Update
- [x] 2.1 Update "Homepage Metadata Extraction" requirement in `openspec/specs/cli-pipeline/spec.md` to document generic repo navigation and platform global navigation filtering
- [x] 2.2 Add scenarios covering generic repo nav exclusion, platform global nav exclusion, and layout ancestor filtering interactions

## 3. Validation
- [x] 3.1 Run `openspec validate filter-generic-repo-nav --strict` and resolve any issues
- [x] 3.2 Confirm all tests pass: `pytest -q`
- [x] 3.3 Spot-check a real GitHub repo homepage scrape to verify generic links are excluded
