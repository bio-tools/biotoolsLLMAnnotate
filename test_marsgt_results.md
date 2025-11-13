# marsgt Scraper Results - Before and After

## Before Fixes

### Documentation Links: 16 (5 should be filtered)
- ❌ https://maintainers.github.com (platform nav)
- ❌ https://github.com/premium-support (platform nav)
- ❌ https://github.com/OSU-BMBL/marsgt/activity (repo nav)
- ✅ https://github.com/OSU-BMBL/marsgt/tree/main/Tutorial
- ✅ https://github.com/OSU-BMBL/marsgt/blob/main/requirements.txt
- ✅ https://zenodo.org/record/8163160/files/Tutorial_example.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/Mouse_retina.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/B_lymphoma.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/PBMCs.zip?download=1
- ✅ https://zenodo.org/records/14207730/files/hg38_lisa_500.qsave?download=1
- ✅ https://zenodo.org/records/14207730/files/mm10.qsave?download=1
- ✅ https://github.com/mtduan/marsgt/blob/main/Tutorial/Tutorial_for_example_data.ipynb
- ✅ https://github.com/mtduan/marsgt/tree/main/Tutorial/Tutorial_local_version
- ✅ https://github.com/mtduan/marsgt/tree/main/Tutorial/Turtorial_server_version
- ❌ https://github.com/contact/report-content?... (platform nav)
- ❌ https://github.community/ (platform nav)

### Keywords: 9 (4 should be filtered)
- ❌ activity (from repo nav)
- ❌ community (from platform nav)
- ❌ contact (from platform nav)
- ✅ example
- ✅ requirements.txt
- ❌ support (from platform nav)
- ✅ tutorial
- ✅ version
- ✅ zenodo

**Quality: 11/16 legitimate doc links (69%), 5/9 legitimate keywords (56%)**

---

## After Fixes

### Documentation Links: 11 (all legitimate)
- ✅ https://github.com/OSU-BMBL/marsgt/tree/main/Tutorial
- ✅ https://github.com/OSU-BMBL/marsgt/blob/main/requirements.txt
- ✅ https://zenodo.org/record/8163160/files/Tutorial_example.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/Mouse_retina.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/B_lymphoma.zip?download=1
- ✅ https://zenodo.org/record/8163160/files/PBMCs.zip?download=1
- ✅ https://zenodo.org/records/14207730/files/hg38_lisa_500.qsave?download=1
- ✅ https://zenodo.org/records/14207730/files/mm10.qsave?download=1
- ✅ https://github.com/mtduan/marsgt/blob/main/Tutorial/Tutorial_for_example_data.ipynb
- ✅ https://github.com/mtduan/marsgt/tree/main/Tutorial/Tutorial_local_version
- ✅ https://github.com/mtduan/marsgt/tree/main/Tutorial/Turtorial_server_version

### Keywords: 5 (all legitimate)
- ✅ example
- ✅ requirements.txt
- ✅ tutorial
- ✅ version
- ✅ zenodo

**Quality: 11/11 legitimate doc links (100%), 5/5 legitimate keywords (100%)**

---

## Changes Made

### 1. Added Missing Platform Domains
In `_is_github_global_nav_link()`:
- `maintainers.github.com`
- `github.community`

### 2. Added Missing Platform Paths
In `_is_github_global_nav_link()`:
- `/premium-support`
- `/contact`

### 3. Added Missing Repo Navigation
In `_REPO_NAV_PATH_PREFIXES`:
- `/activity`

In `_REPO_NAV_TEXT`:
- `activity`

---

## Impact

- **Links improved**: 69% → 100% legitimate (5 noisy links removed)
- **Keywords improved**: 56% → 100% legitimate (4 noisy keywords removed)
- **LLM context cleaner**: 31% reduction in noise (9 items removed out of 25 total)
