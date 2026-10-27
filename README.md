# NCAA Men's Swimming Results Scraper

This scraper collects finalist names and final times from five individual events at the 2026 NCAA Division I Men's Swimming and Diving Championships (https://swimmeetresults.tech/NCAA-Division-I-Men-2026/). It prints each event's results in finish order.

Here are the events:
    100 Backstroke
    400 IM
    200 Freestyle
    100 Butterfly
    100 Breastroke

## How to use

From the project directory, install the requests dependency and run the scraper (./scraper.py) The program fetches the five event pages and prints the extracted finalists and times to standard output. 

Expected Output:

2026 NCAA Men's Swimming Championships

Scraped Events: 5
Results: 40

Scraped Results:

100 Back:
   1) Hubert Kos, 42.61
   2) Ruard Van Renen, 43.54
   ...


## Functional programming and concurrent.futures

The scraper uses filter() to remove incomplete records and map() to reformat swimmer names. These functional transformation take advantage of data parallelism to operate a single task on multiple pieces of data at once.

The scraper uses concurrent.futures.ThreadPoolExecutor with five cores to request event pages concurrently. This can reduce the total waiting time for the server to respond to the request because all five requests are made at the same time.

## Screenshot
The screenshot is located in the screenshot.png file.
