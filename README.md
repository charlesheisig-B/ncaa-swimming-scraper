# NCAA Men's Swimming Results Scraper

This Python scraper collects finalist names and final times from five individual events at the 2026 NCAA Division I Men's Swimming and Diving Championships. I chose these results because the meet publishes separate event pages with readable result tables.

## Technologies

- Python 3.9+
- `requests` for downloading event pages
- `concurrent.futures.ThreadPoolExecutor` for concurrent network requests
- Functional transformations with `filter()`, `map()`, and `sorted()`

## Run

Install the dependency and run the scraper from this directory:

```bash
python3 -m pip install requests
python3 scraper.py
```

The program scrapes five finals pages, compares sequential and concurrent results, and prints sample results and performance measurements. Requests have a 10-second timeout; concurrent fetching is limited to four workers.

## Sample output

Example from a run of the scraper:

```text
2026 NCAA Men's Swimming Championships

Scraped Events: 5

Sample Results:

Event: 100 Backstroke
Swimmer: Adam Chaney
Time: 43.75

Event: 100 Backstroke
Swimmer: Aiden Hayes
Time: 44.49
```

## Performance

The program measures the median of three runs with `time.perf_counter()`. In one run:

| Method | Median runtime |
| --- | ---: |
| Sequential page fetching | 1.317 seconds |
| Concurrent page fetching (4 threads) | 0.467 seconds |
| Speedup (sequential / concurrent) | 2.82x |
| Functional transformation | 0.000085 seconds |
| Imperative transformation | 0.000074 seconds |

The sequential and concurrent scrapers produced identical records, as did the functional and imperative transformations. These measurements are one sample and can vary with network conditions. Threading helps here because the program spends much of its time waiting for web requests; threads overlap that waiting. This is I/O concurrency, not CPU parallelism.

The functional version uses `filter()` to discard incomplete records, `map()` to format names, and `sorted()` to order results. The comparison shows that the two approaches produce the same data; functional programming makes these transformations composable, but does not inherently make them faster.

## Screenshot

The repository includes `screenshot.png`, but it is currently an empty placeholder. Before submitting, capture the program running in a terminal and replace it with a real screenshot.

## Data source

[2026 NCAA Division I Men's Swimming and Diving Championships results](https://swimmeetresults.tech/NCAA-Division-I-Men-2026/)