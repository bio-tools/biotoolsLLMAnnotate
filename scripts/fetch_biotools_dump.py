#!/usr/bin/env python3
"""Download the latest bio.tools dump and sanitize publication types.

The upstream Pub2Tools / EDAMmap pipeline crashes when the registry
returns publication types that are not part of its fixed enum.  This
utility fetches the entire bio.tools catalog, rewrites any unknown
publication types to "Other", and saves the sanitized JSON to the
requested output path (default: out/biotools_in/biotools.json).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, parse, request

API_ROOT = "https://bio.tools/api/tool/"
ALLOWED_PUBLICATION_TYPES = {
    "Primary",
    "Method",
    "Usage",
    "Benchmarking study",
    "Review",
    "Other",
}


def fetch_page(page: int, timeout: int) -> Dict[str, Any]:
    """Download a single page from the bio.tools API."""
    query = parse.urlencode({"format": "json", "page": page})
    url = f"{API_ROOT}?{query}"
    with request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def sanitize_publications(tool: Dict[str, Any], unknown_counter: Counter) -> None:
    """Rewrite publication types outside the allowed set to "Other"."""
    publications: List[Dict[str, Any]] = tool.get("publication") or []
    for publication in publications:
        types = publication.get("type")
        if not types:
            continue
        sanitized = []
        for pub_type in types:
            if pub_type not in ALLOWED_PUBLICATION_TYPES:
                unknown_counter[pub_type] += 1
                sanitized.append("Other")
            else:
                sanitized.append(pub_type)
        publication["type"] = sanitized


def write_json(data: Dict[str, Any], output_path: Path) -> None:
    """Safely write JSON to disk, ensuring directories exist."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False)
    tmp_path.replace(output_path)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("out/biotools_in/biotools.json"),
        help="Path where the sanitized dump will be written",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds for each page fetch",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Optional delay between page fetches to avoid throttling",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    all_tools: List[Dict[str, Any]] = []
    unknown_types: Counter = Counter()
    page = 1

    print("Fetching bio.tools catalog …", file=sys.stderr)
    while True:
        try:
            page_data = fetch_page(page, timeout=args.timeout)
        except error.HTTPError as http_err:  # pragma: no cover - network failure handling
            print(f"HTTP error on page {page}: {http_err}", file=sys.stderr)
            return 1
        except error.URLError as url_err:  # pragma: no cover
            print(f"Network error on page {page}: {url_err}", file=sys.stderr)
            return 1

        tools = page_data.get("list", [])
        if not tools:
            break

        for tool in tools:
            sanitize_publications(tool, unknown_types)
        all_tools.extend(tools)

        next_link = page_data.get("next")
        print(f"Fetched page {page}, total tools so far: {len(all_tools):,}", file=sys.stderr)
        if not next_link:
            break
        page += 1
        if args.sleep:
            time.sleep(args.sleep)

    dump = {
        "count": len(all_tools),
        "next": None,
        "previous": None,
        "list": all_tools,
    }
    write_json(dump, args.output)

    if unknown_types:
        print("Sanitized publication types:", file=sys.stderr)
        for pub_type, occurrences in unknown_types.most_common():
            print(f"  {pub_type!r}: {occurrences}", file=sys.stderr)
    else:
        print("No publication types required sanitizing.", file=sys.stderr)

    print(f"Wrote sanitized dump to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
