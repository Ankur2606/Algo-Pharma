"""
AlgoPharma — Reddit Scraper via Apify
Uses Apify's trudax/reddit-scraper actor (no Reddit API key needed).

SETUP:
  1. Create free account at https://apify.com  (free $5/month = ~1000 results)
  2. Go to https://console.apify.com/account/integrations → copy your API token
  3. pip install apify-client
  4. python apify_reddit_scraper.py

FREE TIER: $5/month credits → roughly 1,000 posts free every month.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime

# Enable UTF-8 printing for emojis on Windows (only when run directly, not when imported by MCP)
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG ────────────────────────────────────────────────────────────────────
SEARCH_QUERY = "dolo 365 medicine side effects"      # your search term
MAX_ITEMS    = 20                       # max items to fetch (max 100 per request)
SORT         = "relevance"              # relevance | new | top | comments
TIME_FILTER  = "all"                    # all | year | month | week | day | hour
OUTPUT_FILE  = "reddit_dolo365_results.json"
# ─────────────────────────────────────────────────────────────────────────────


def scrape_reddit(query: str, max_items: int = 20) -> list[dict]:
    print(f"🔗 Connecting directly to Reddit API...", file=sys.stderr)
    
    # Construct the URL
    safe_query = urllib.parse.quote(query)
    url = f"https://www.reddit.com/search.json?q={safe_query}&sort={SORT}&t={TIME_FILTER}&limit={max_items}"
    
    print(f"🚀 Fetching search results for: '{query}'", file=sys.stderr)
    print(f"   Max items: {max_items} | Sort: {SORT} | Time: {TIME_FILTER}", file=sys.stderr)
    print(f"{'─'*55}", file=sys.stderr)

    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'python:algopharma:v0.1.0 (by /u/algopharma)'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error fetching from Reddit: {e}", file=sys.stderr)
        return []

    print(f"✅ Fetched results successfully.", file=sys.stderr)
    print(f"{'─'*55}", file=sys.stderr)

    posts = []
    children = data.get("data", {}).get("children", [])
    
    for item in children:
        post_data = item.get("data", {})
        post = {
            "id":           post_data.get("id", ""),
            "title":        post_data.get("title", ""),
            "description":  post_data.get("selftext", ""),
            "url":          post_data.get("url", ""),
            "permalink":    "https://www.reddit.com" + post_data.get("permalink", ""),
            "subreddit":    post_data.get("subreddit", ""),
            "author":       post_data.get("author", ""),
            "score":        post_data.get("score", 0),
            "num_comments": post_data.get("num_comments", 0),
            "upvote_ratio": post_data.get("upvote_ratio", None),
            "created_utc":  post_data.get("created_utc", ""),
            "flair":        post_data.get("link_flair_text", ""),
            "is_nsfw":      post_data.get("over_18", False),
        }
        posts.append(post)

    return posts


def main():
    start = datetime.now()

    posts = scrape_reddit(SEARCH_QUERY, MAX_ITEMS)

    if not posts:
        print("⚠️  No posts returned. Check your API token or search query.")
        return

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2, default=str)

    elapsed = (datetime.now() - start).seconds
    print(f"\n✅ Saved {len(posts)} posts → '{OUTPUT_FILE}'  ({elapsed}s)")
    print(f"{'─'*55}")

    # Preview first result
    p = posts[0]
    print(f"\n📌 Sample post #1:")
    print(f"  Title      : {p['title']}")
    print(f"  Subreddit  : r/{p['subreddit']}")
    print(f"  Author     : u/{p['author']}")
    print(f"  Score      : {p['score']} | Comments: {p['num_comments']}")
    desc = str(p['description'])[:200].replace('\n', ' ')
    print(f"  Description: {desc}..." if desc else "  Description: [link post]")
    print(f"  URL        : {p['permalink']}")


if __name__ == "__main__":
    main()