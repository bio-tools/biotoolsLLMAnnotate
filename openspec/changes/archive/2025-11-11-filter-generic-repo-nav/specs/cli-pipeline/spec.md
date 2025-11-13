## MODIFIED Requirements

### Requirement: Homepage Metadata Extraction
The enrichment stage SHALL fetch homepage content with configurable timeouts, byte-size guardrails, and iframe limits, reject publication-only URLs, and merge documentation, repository, and keyword metadata from both the root document and a bounded crawl of nested frames; it SHALL emit homepage status and error labels when fetching fails. Before recording any anchor as a documentation link, the scraper SHALL exclude generic repository navigation paths (issues, pulls, releases, tags, commits, branches, contributors, stargazers, watchers, forks, milestones, labels, and platform-specific variants) and platform global navigation links (features, about, blog, changelog, pricing, support, docs subdomains) that do not provide tool-specific information.

#### Scenario: Publication homepage is filtered
- **WHEN** the primary homepage candidate resolves to a publication URL and an alternative non-publication URL exists
- **THEN** the enrichment stage selects the non-publication URL and updates the candidate homepage accordingly

#### Scenario: Non-HTML content is reported
- **WHEN** the fetched homepage advertises a non-text content type or exceeds the byte limit
- **THEN** the enrichment stage marks `homepage_scraped=False`, records a descriptive `homepage_error`, and keeps the candidate available for scoring

#### Scenario: Frame crawl extends metadata
- **WHEN** nested frames yield additional documentation links or repository URLs before the frame fetch and depth limits are exhausted
- **THEN** the enrichment stage merges the new metadata into the candidate without duplicating existing documentation entries

#### Scenario: Generic repo navigation is excluded
- **WHEN** a repository homepage anchor points to /releases, /tags, /commits, /issues, /pulls, or any path matching generic navigation patterns
- **THEN** the scraper does NOT add that link to `candidate["documentation"]` regardless of keyword matches

#### Scenario: Platform global navigation is excluded
- **WHEN** an anchor resolves to a platform-wide support/docs/blog/features subdomain or path (e.g., docs.github.com, /features, /about, /pricing)
- **THEN** the scraper does NOT add that link to `candidate["documentation"]` even if it matches documentation keywords

#### Scenario: Layout ancestor filtering still applies
- **WHEN** an anchor sits within a detected layout container (nav, header, footer, sidebar) and has no matching documentation keywords
- **THEN** the scraper skips that anchor to avoid capturing site chrome unrelated to tool docs
