#!/usr/bin/env python3
"""Update a WeChat album section in the profile README."""

from __future__ import annotations

import argparse
import html
import re
import urllib.parse
import urllib.request
from pathlib import Path


ANNUAL_BOOK_LIST_URL = (
    "https://mp.weixin.qq.com/mp/appmsgalbum"
    "?__biz=MzU3NDgyNzYwNg%3D%3D"
    "&action=getalbum"
    "&album_id=2713424606111498241"
)
MEDITATIONS_URL = (
    "https://mp.weixin.qq.com/mp/appmsgalbum"
    "?__biz=MzU3NDgyNzYwNg%3D%3D"
    "&action=getalbum"
    "&album_id=1621262515634552833"
)
ARTICLE_COUNT = 5
COLLECTIONS = {
    "annual-book-list": {
        "album_url": ANNUAL_BOOK_LIST_URL,
        "start_marker": "<!-- ANNUAL_BOOK_LIST:START -->",
        "end_marker": "<!-- ANNUAL_BOOK_LIST:END -->",
    },
    "meditations": {
        "album_url": MEDITATIONS_URL,
        "start_marker": "<!-- MEDITATIONS:START -->",
        "end_marker": "<!-- MEDITATIONS:END -->",
    },
}


def fetch_album(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def extract_latest_articles(
    page: str, limit: int = ARTICLE_COUNT
) -> list[tuple[str, str]]:
    if limit < 1:
        raise ValueError("Article limit must be positive")

    article_list = re.search(
        r"articleList\s*:\s*\[(?P<body>.*?)\]\s*,\s*continue_flag",
        page,
        flags=re.DOTALL,
    )
    if article_list is None:
        raise ValueError("WeChat album page does not contain articleList")

    article_matches = re.finditer(
        r"\{\s*title\s*:\s*'(?P<title>(?:\\.|[^'])*)'"
        r".*?url\s*:\s*'(?P<url>(?:\\.|[^'])*)'",
        article_list.group("body"),
        flags=re.DOTALL,
    )
    articles: list[tuple[str, str]] = []
    for article in article_matches:
        title = html.unescape(article.group("title")).replace("\\'", "'").strip()
        raw_url = html.unescape(article.group("url")).replace("\\/", "/").strip()
        parsed_url = urllib.parse.urlsplit(raw_url)

        if not title:
            raise ValueError("WeChat article has an empty title")
        if parsed_url.hostname != "mp.weixin.qq.com":
            raise ValueError(f"Unexpected article host: {parsed_url.hostname!r}")

        article_url = urllib.parse.urlunsplit(
            ("https", parsed_url.netloc, parsed_url.path, parsed_url.query, "")
        )
        articles.append((title, article_url))
        if len(articles) == limit:
            break

    if len(articles) < limit:
        raise ValueError(
            f"WeChat album contains {len(articles)} articles; expected at least {limit}"
        )
    return articles


def render_entries(articles: list[tuple[str, str]]) -> str:
    entries = []
    for title, url in articles:
        markdown_title = (
            title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        )
        entries.append(f"- [《{markdown_title}》]({url})")
    return "\n".join(entries)


def update_readme(
    content: str, entries: str, start_marker: str, end_marker: str
) -> str:
    marker_pattern = re.compile(
        rf"{re.escape(start_marker)}\r?\n.*?\r?\n{re.escape(end_marker)}",
        flags=re.DOTALL,
    )
    replacement = f"{start_marker}\n{entries}\n{end_marker}"
    updated, replacement_count = marker_pattern.subn(replacement, content)
    if replacement_count != 1:
        raise ValueError("README must contain exactly one matching marker block")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection", choices=COLLECTIONS)
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()
    collection = COLLECTIONS[args.collection]

    articles = extract_latest_articles(fetch_album(collection["album_url"]))
    original = args.readme.read_text(encoding="utf-8")
    updated = update_readme(
        original,
        render_entries(articles),
        collection["start_marker"],
        collection["end_marker"],
    )

    if updated == original:
        print(f"README is current: {len(articles)} {args.collection} articles")
        return

    args.readme.write_text(updated, encoding="utf-8")
    print(f"Updated README with {len(articles)} {args.collection} articles")


if __name__ == "__main__":
    main()
