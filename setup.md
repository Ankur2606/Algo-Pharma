# Algo-Pharma Data Crawlers Setup

This project contains two robust data scrapers designed to collect information about pharmaceutical queries from Reddit and Twitter.

## Prerequisites
- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://github.com/astral-sh/uv) (A fast Python package installer and resolver)

## 1. Environment Setup

The crawlers rely on environment variables for API authentication.

1. In the root of the project, create a copy of the `.env.local` file and name it `.env`.
   ```bash
   cp .env.local .env
   ```
2. Open the newly created `.env` file and insert your API keys:
   - **TWITTER_API_KEY**: Get this from [twitterapi.io](https://twitterapi.io/) to power the Twitter scraper.
   - **APIFY_TOKEN**: *(Optional)* Previously used for Apify Reddit actors; the current Reddit scraper is fully native and does not strictly require this token anymore.

## 2. Installation

Use `uv` to automatically resolve and sync the project dependencies:
```bash
uv sync
```
*(Alternatively, you can manually install the required packages: `uv add python-dotenv`)*

## 3. Usage

You can edit the `CONFIG` section at the top of either script to adjust your search term (`SEARCH_QUERY`) or limits.

### Run the Reddit Crawler
The Reddit crawler bypasses external APIs and natively fetches from Reddit's JSON search endpoint. It does not require any authentication.
```bash
uv run .\reddit_crawler.py
```
**Output:** Generates `reddit_dolo365_results.json`

### Run the Twitter Crawler
The Twitter crawler queries the `twitterapi.io` advanced search endpoints and synthesizes a title for seamless dataset integration.
```bash
uv run .\twitter_crawler.py
```
**Output:** Generates `twitter_dolo365_results.json`
