## Why
Repository homepages (GitHub, GitLab, Bitbucket, etc.) expose generic navigation links (Releases, Tags, Commits, Issues, Pull Requests) in their chrome regardless of whether those sections contain meaningful content. The current scraper's keyword matching treats these links as documentation even when they point to empty or irrelevant sections, polluting the `candidate["documentation"]` list with noise. Additionally, platform-wide navigation (e.g., GitHub's /features, docs.github.com, github.blog, support pages) gets captured because it matches documentation keywords but provides zero information about the actual tool.

## What Changes
- Extend the scraper's filtering logic to exclude generic repository navigation paths (releases, tags, commits, branches, contributors, milestones, etc.) and anchor text patterns that universally appear in repo UIs across GitHub/GitLab/Bitbucket/SourceForge/etc.
- Add platform-agnostic detection for global navigation links (e.g., docs subdomain, support subdomain, /features, /about, /blog, /pricing paths) that apply across hosting platforms, not just GitHub.
- Update the "Homepage Metadata Extraction" requirement in the CLI pipeline spec to mandate exclusion of generic repo navigation and platform global navigation before documentation links are recorded.
- Focus on the README rather on generic repo nav and platform global nav filtering to improve the quality of documentation links captured for LLM scoring and user review.

## Impact
- Affected specs: cli-pipeline (Homepage Metadata Extraction requirement)
- Affected code: `enrich/scraper.py` (filters already implemented; spec update documents the behavior)
- User benefit: Cleaner documentation lists focused on tool-specific docs; fewer false positives from empty repo sections; more accurate LLM prompts for scoring.
