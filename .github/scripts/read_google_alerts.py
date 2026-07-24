#!/usr/bin/env python3
"""Read a Google Alerts Atom/RSS feed and emit normalized JSON."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_markup = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(without_markup).split())


def child_text(element: ET.Element, *names: str) -> str:
    for child in element:
        if local_name(child.tag) in names:
            value = clean_text(child.text)
            if value:
                return value
    return ""


def entry_link(entry: ET.Element) -> str:
    for child in entry:
        if local_name(child.tag) != "link":
            continue
        relationship = child.attrib.get("rel", "alternate")
        if relationship == "alternate":
            return child.attrib.get("href", "").strip() or clean_text(child.text)
    return child_text(entry, "link")


def entry_source(entry: ET.Element) -> str:
    for child in entry:
        if local_name(child.tag) not in {"source", "author"}:
            continue
        nested = child_text(child, "title", "name")
        if nested:
            return nested
        direct = clean_text(child.text)
        if direct:
            return direct
    return ""


def fetch_feed(feed_url: str) -> bytes:
    parsed_url = urlparse(feed_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("The Google Alerts feed URL must use HTTP or HTTPS.")

    request = urllib.request.Request(
        feed_url,
        headers={"User-Agent": "fastturtle.github.io Google Alerts monitor/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"Google Alerts returned HTTP status {error.code}."
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError("Could not reach the Google Alerts feed.") from error


def parse_entries(feed_xml: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(feed_xml)
    entries = [
        element
        for element in root.iter()
        if local_name(element.tag) in {"entry", "item"}
    ]

    normalized = []
    for entry in entries:
        title = child_text(entry, "title") or "Untitled result"
        link = entry_link(entry)
        if not link:
            continue

        identifier = child_text(entry, "id", "guid") or link
        alert_id = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:20]
        published = child_text(entry, "published", "pubDate", "updated")
        source = entry_source(entry)

        normalized.append(
            {
                "id": alert_id,
                "title": title,
                "issue_title": f"Possible website update: {title}"[:220],
                "link": link,
                "published": published,
                "source": source,
            }
        )

    return normalized


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: read_google_alerts.py GOOGLE_ALERTS_RSS_URL", file=sys.stderr)
        return 2

    try:
        results = parse_entries(fetch_feed(sys.argv[1]))
    except (ET.ParseError, RuntimeError, ValueError) as error:
        print(f"Google Alerts feed error: {error}", file=sys.stderr)
        return 1

    json.dump(results, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
