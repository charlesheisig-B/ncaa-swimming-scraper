#!/usr/bin/env python3

import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import requests


EVENT_PAGES = [
    (
        "100 Butterfly",
        "https://swimmeetresults.tech/NCAA-Division-I-Men-2026/260325F004.htm",
    ),
    ("400 IM", "https://swimmeetresults.tech/NCAA-Division-I-Men-2026/260325F005.htm"),
    (
        "200 Freestyle",
        "https://swimmeetresults.tech/NCAA-Division-I-Men-2026/260325F006.htm",
    ),
    (
        "100 Breaststroke",
        "https://swimmeetresults.tech/NCAA-Division-I-Men-2026/260325F007.htm",
    ),
    (
        "100 Backstroke",
        "https://swimmeetresults.tech/NCAA-Division-I-Men-2026/260325F010.htm",
    ),
]

EVENT_LABELS = {
    "100 Butterfly": "100 Fly",
    "400 IM": "400 IM",
    "200 Freestyle": "200 Free",
    "100 Breaststroke": "100 Breast",
    "100 Backstroke": "100 Back",
}


class _PreTextParser(HTMLParser):
    """Collect text inside a page's preformatted results block."""

    def __init__(self) -> None:
        super().__init__()
        self.in_pre = False
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "pre":
            self.in_pre = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self.in_pre = False

    def handle_data(self, data: str) -> None:
        if self.in_pre:
            self.text_parts.append(data)


def fetch_results(url: str) -> str:
    """Download one results page and return its HTML."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        raise RuntimeError(f"Could not fetch {url}: {error}") from error


def parse_results(html: str, event: str) -> list[dict[str, str]]:
    """Extract swimmers who have a final time from one event page."""
    parser = _PreTextParser()
    parser.feed(html)
    rows = "".join(parser.text_parts).splitlines()

    results = []
    year_codes = {"FR", "SO", "JR", "SR", "5Y"}
    time_pattern = re.compile(r"^\d+:\d{2}\.\d{2}|^\d+\.\d{2}[A-Z]?$")

    for row in rows:
        columns = row.split()
        year_index = next(
            (index for index, column in enumerate(columns) if column in year_codes),
            None,
        )
        if year_index is None or year_index < 3 or not columns[0].isdigit():
            continue

        times = [column for column in columns[year_index + 1 :] if time_pattern.match(column)]
        if len(times) < 2:
            continue

        name = " ".join(columns[1:year_index])
        final_time = re.sub(r"[A-Z]$", "", times[-1])
        results.append({"event": event, "name": name, "time": final_time})

    return results


def scrape_concurrent(event_pages: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Fetch and parse event pages using up to four worker threads."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        pages = executor.map(lambda event_page: fetch_results(event_page[1]), event_pages)
        return [
            result
            for (event, _), html in zip(event_pages, pages)
            for result in parse_results(html, event)
        ]


def _format_name(name: str) -> str:
    """Convert a name from 'Last, First' to 'First Last'."""
    if ", " not in name:
        return name
    last_name, first_name = name.split(", ", maxsplit=1)
    return f"{first_name} {last_name}"


def transform_results_functional(
    results: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Filter incomplete records and format names with functional tools."""
    complete_results = filter(
        lambda result: all(
            result.get(field, "").strip() for field in ("event", "name", "time")
        ),
        results,
    )
    return list(
        map(
            lambda result: {**result, "name": _format_name(result["name"])},
            complete_results,
        )
    )


def main() -> None:
    results = transform_results_functional(scrape_concurrent(EVENT_PAGES))
    print("2026 NCAA Men's Swimming Championships")
    print(f"\nScraped Events: {len(EVENT_PAGES)}")
    print(f"Results: {len(results)}")
    print("\nScraped Results:")
    for event, _ in EVENT_PAGES:
        event_results = filter(lambda result: result["event"] == event, results)
        print(f"\n{EVENT_LABELS[event]}:")
        for place, result in enumerate(event_results, start=1):
            print(f"   {place}) {result['name']}, {result['time']}")


if __name__ == "__main__":
    main()