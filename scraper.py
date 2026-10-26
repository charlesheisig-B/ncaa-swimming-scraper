#!/usr/bin/env python3

import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from statistics import median
from time import perf_counter
from typing import Callable

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


def scrape_sequential(event_pages: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Fetch and parse event pages one at a time."""
    return [
        result
        for event, url in event_pages
        for result in parse_results(fetch_results(url), event)
    ]


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
    """Filter, format, and sort results using functional transformations."""
    valid_results = filter(
        lambda result: all(result.get(field, "").strip() for field in ("event", "name", "time")),
        results,
    )
    formatted_results = map(
        lambda result: {**result, "name": _format_name(result["name"])},
        valid_results,
    )
    return sorted(formatted_results, key=lambda result: (result["event"], result["name"]))


def transform_results_imperative(
    results: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Perform the same filtering, formatting, and sorting with loops."""
    formatted_results = []
    for result in results:
        if not all(result.get(field, "").strip() for field in ("event", "name", "time")):
            continue
        formatted_results.append({**result, "name": _format_name(result["name"])})

    formatted_results.sort(key=lambda result: (result["event"], result["name"]))
    return formatted_results


def benchmark_scraper(
    scraper: Callable[[list[tuple[str, str]]], list[dict[str, str]]],
    event_pages: list[tuple[str, str]],
    repetitions: int = 3,
) -> tuple[float, list[dict[str, str]]]:
    """Return a scraper's median runtime and results from its final trial."""
    runtimes = []
    results = []
    for _ in range(repetitions):
        start_time = perf_counter()
        results = scraper(event_pages)
        runtimes.append(perf_counter() - start_time)
    return median(runtimes), results


def benchmark_transformation(
    transform: Callable[[list[dict[str, str]]], list[dict[str, str]]],
    results: list[dict[str, str]],
    repetitions: int = 3,
) -> tuple[float, list[dict[str, str]]]:
    """Return a transformation's median runtime on already-fetched data."""
    runtimes = []
    transformed_results = []
    for _ in range(repetitions):
        start_time = perf_counter()
        transformed_results = transform(results)
        runtimes.append(perf_counter() - start_time)
    return median(runtimes), transformed_results


def main() -> None:
    sequential_time, sequential_results = benchmark_scraper(
        scrape_sequential, EVENT_PAGES
    )
    concurrent_time, concurrent_results = benchmark_scraper(
        scrape_concurrent, EVENT_PAGES
    )
    if sequential_results != concurrent_results:
        raise RuntimeError("Sequential and concurrent results do not match.")

    functional_time, functional_results = benchmark_transformation(
        transform_results_functional, sequential_results
    )
    imperative_time, imperative_results = benchmark_transformation(
        transform_results_imperative, sequential_results
    )
    if functional_results != imperative_results:
        raise RuntimeError("Functional and imperative results do not match.")

    print("2026 NCAA Men's Swimming Championships")
    print(f"\nScraped Events: {len(EVENT_PAGES)}")
    print("\nSample Results:")
    for result in functional_results[:5]:
        print(
            f"\nEvent: {result['event']}\n"
            f"Swimmer: {result['name']}\n"
            f"Time: {result['time']}"
        )

    print("\nScraping Performance (median of 3 runs):")
    print(f"Sequential: {sequential_time:.3f} seconds")
    print(f"Concurrent: {concurrent_time:.3f} seconds")
    print(f"Speedup: {sequential_time / concurrent_time:.2f}x")

    print("\nTransformation Performance (median of 3 runs):")
    print(f"Functional: {functional_time:.6f} seconds")
    print(f"Imperative: {imperative_time:.6f} seconds")
    print("Both transformations produced equivalent results.")


if __name__ == "__main__":
    main()