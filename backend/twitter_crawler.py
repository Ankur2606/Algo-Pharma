import os
import sys
from pathlib import Path

# Insert backend directory to python path to resolve absolute imports
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import json
import urllib.request
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable UTF-8 printing for emojis on Windows (only when run directly, not when imported by MCP)
if __name__ == "__main__" and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG ────────────────────────────────────────────────────────────────────
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
SEARCH_QUERY    = "dolo 365 medicine side effects"
QUERY_TYPE      = "Top"      # "Top" or "Latest"
OUTPUT_FILE     = "data/twitter_dolo365_results.json"
# ─────────────────────────────────────────────────────────────────────────────

def scrape_twitter(query: str, query_type: str = "Top") -> list[dict]:
    print(f"🔗 Connecting to twitterapi.io...", file=sys.stderr)
    
    if not TWITTER_API_KEY:
        print("❌ Error: TWITTER_API_KEY not found in .env", file=sys.stderr)
        return []

    # Construct the URL
    safe_query = urllib.parse.quote(query)
    url = f"https://api.twitterapi.io/twitter/tweet/advanced_search?query={safe_query}&queryType={query_type}"
    
    print(f"🚀 Fetching search results for: '{query}'", file=sys.stderr)
    print(f"   Query Type: {query_type}", file=sys.stderr)
    print(f"{'─'*55}", file=sys.stderr)

    req = urllib.request.Request(
        url, 
        headers={'X-API-Key': TWITTER_API_KEY}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error fetching from Twitter: {e}", file=sys.stderr)
        return []

    print(f"✅ Fetched results successfully.", file=sys.stderr)
    print(f"{'─'*55}", file=sys.stderr)

    tweets_data = data.get("tweets", [])
    posts = []
    
    for item in tweets_data:
        # Normalize fields
        author = item.get("author", {})
        # Twitter does not have a native "title" field.
        # Fallback to hashtags if present, otherwise use the search query.
        hashtags = [h.get("text") for h in item.get("entities", {}).get("hashtags", [])]
        if hashtags:
            synthetic_title = f"Tweet about #{', #'.join(hashtags)}"
        else:
            synthetic_title = f"Topic: {query}"

        full_text = item.get("text", "")
        post = {
            "id":           item.get("id", ""),
            "title":        synthetic_title,
            "description":  full_text,
            "url":          item.get("url", ""),
            "permalink":    item.get("url", ""),
            "author":       author.get("userName", ""),
            "author_name":  author.get("name", ""),
            "score":        item.get("likeCount", 0),
            "num_comments": item.get("replyCount", 0),
            "retweets":     item.get("retweetCount", 0),
            "views":        item.get("viewCount", 0),
            "created_utc":  item.get("createdAt", ""),
        }
        posts.append(post)

    return posts

def main():
    start = datetime.now()

    posts = scrape_twitter(SEARCH_QUERY, QUERY_TYPE)

    if not posts:
        print("⚠️  No posts returned. Check your API token or search query.")
        return

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2, default=str)

    elapsed = (datetime.now() - start).seconds
    print(f"\n✅ Saved {len(posts)} tweets → '{OUTPUT_FILE}'  ({elapsed}s)")
    print(f"{'─'*55}")

    # Preview first result
    p = posts[0]
    print(f"\n📌 Sample tweet #1:")
    print(f"  Author     : @{p['author']} ({p['author_name']})")
    print(f"  Likes      : {p['score']} | Replies: {p['num_comments']} | Retweets: {p['retweets']}")
    desc = str(p['description'])[:200].replace('\n', ' ')
    print(f"  Text       : {desc}..." if len(desc) == 200 else f"  Text       : {desc}")
    print(f"  URL        : {p['url']}")

if __name__ == "__main__":
    main()
