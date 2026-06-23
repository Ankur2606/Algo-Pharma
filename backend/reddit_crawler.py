"""
AlgoPharma — Reddit Scraper
Direct connection via Reddit Search RSS with a robust cache fallback.
Does NOT require an API token.
"""

import json
import os
import sys
from pathlib import Path

# Insert backend directory to python path to resolve absolute imports
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime, timezone

# Enable UTF-8 printing for emojis on Windows (only when run directly, not when imported by MCP)
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG ────────────────────────────────────────────────────────────────────
SEARCH_QUERY = "vioxx"     # your search term
MAX_ITEMS    = 23                     # max items to fetch
SORT         = "relevance"              # relevance | new | top | comments
TIME_FILTER  = "all"                    # all | year | month | week | day | hour
OUTPUT_FILE  = "data/reddit_dolo365_results.json"
# ─────────────────────────────────────────────────────────────────────────────


def clean_html(html_str):
    if not html_str:
        return ""
    # Try to find text between <!-- SC_OFF --> and <!-- SC_ON -->
    match = re.search(r'<!-- SC_OFF -->(.*?)<!-- SC_ON -->', html_str, re.DOTALL)
    if match:
        html_str = match.group(1)
    
    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', '', html_str)
    # Unescape HTML entities
    clean = html.unescape(clean)
    # Remove metadata lines like "submitted by ... to ... [link] [comments]"
    clean = re.sub(r'\s*submitted by\s+.*?to\s+r/\S+.*', '', clean, flags=re.DOTALL | re.IGNORECASE)
    return clean.strip()


def scrape_reddit(query: str, max_items: int = 23) -> list[dict]:
    print(f"🔗 Connecting directly to Reddit RSS search...", file=sys.stderr)
    
    safe_query = urllib.parse.quote(query)
    # We use .rss instead of .json because Reddit heavily blocks .json requests with 403
    url = f"https://www.reddit.com/search.rss?q={safe_query}&sort={SORT}&t={TIME_FILTER}&limit={max_items}"
    
    print(f"🚀 Fetching search results for: '{query}'", file=sys.stderr)
    print(f"   Max items: {max_items} | Sort: {SORT} | Time: {TIME_FILTER}", file=sys.stderr)
    print(f"{'─'*55}", file=sys.stderr)

    # Generate a unique custom User-Agent per request to prevent footprint blocks
    import random
    rand_id = random.randint(1000, 9999)
    dynamic_custom_ua = f"windows:algopharma_monitor_app_{rand_id}:v1.0.0 (by /u/algopharma_dev_{rand_id})"
    dynamic_python_ua = f"python:crawler_service_{rand_id}:v1.0 (by /u/bot_user_{rand_id})"
    
    # Standard Chrome/Firefox UA with dynamic version numbers
    chrome_ver = random.randint(118, 125)
    safari_ver = random.randint(535, 537)
    dynamic_browser_ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{safari_ver}.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/{safari_ver}.36"
    
    user_agents = [dynamic_custom_ua, dynamic_python_ua, dynamic_browser_ua]
    
    posts = []

    for ua in user_agents:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': ua}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read()
                root = ET.fromstring(content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                
                for entry in entries:
                    author_tag = entry.find('atom:author/atom:name', ns)
                    author = author_tag.text if author_tag is not None else "anonymous"
                    if author.startswith("/u/"):
                        author = author[3:]
                    elif author.startswith("u/"):
                        author = author[2:]
                    
                    cat_tag = entry.find('atom:category', ns)
                    subreddit = cat_tag.get('term') if cat_tag is not None else ""
                    if subreddit.startswith("r/"):
                        subreddit = subreddit[2:]
                    
                    content_tag = entry.find('atom:content', ns)
                    content_html = content_tag.text if content_tag is not None else ""
                    description = clean_html(content_html)
                    
                    link_tag = entry.find('atom:link', ns)
                    permalink = link_tag.get('href') if link_tag is not None else ""
                    
                    # Only keep actual posts, not community/subreddit search results
                    if "/comments/" not in permalink:
                        continue
                    
                    id_tag = entry.find('atom:id', ns)
                    post_id = id_tag.text if id_tag is not None else ""
                    if post_id.startswith("t3_"):
                        post_id = post_id[3:]
                    
                    pub_tag = entry.find('atom:published', ns)
                    created_utc = ""
                    if pub_tag is not None:
                        try:
                            dt = datetime.fromisoformat(pub_tag.text.replace("Z", "+00:00"))
                            created_utc = dt.timestamp()
                        except Exception:
                            pass
                    
                    title_tag = entry.find('atom:title', ns)
                    title = title_tag.text if title_tag is not None else ""
                    
                    post = {
                        "id":           post_id,
                        "title":        title,
                        "description":  description,
                        "url":          permalink,
                        "permalink":    permalink,
                        "subreddit":    subreddit,
                        "author":       author,
                        "score":        0,
                        "num_comments": 0,
                        "upvote_ratio": None,
                        "created_utc":  created_utc,
                        "flair":        "",
                        "is_nsfw":      False,
                    }
                    posts.append(post)
                
                if posts:
                    print(f"✅ Fetched results successfully via RSS.", file=sys.stderr)
                    print(f"{'─'*55}", file=sys.stderr)
                    return posts
        except Exception as e:
            print(f"⚠️ RSS attempt with UA '{ua}' failed: {e}", file=sys.stderr)
            import time
            time.sleep(0.5)

    print("❌ All direct RSS search requests blocked. Falling back to cached results.", file=sys.stderr)
    try:
        from config import get_settings
        settings = get_settings()
        cache_path = settings.REDDIT_JSON_PATH
    except Exception:
        cache_path = OUTPUT_FILE
        
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_posts = json.load(f)
            # Filter posts by query keyword match to make cache more relevant
            keywords = [w.lower() for w in query.split() if len(w) > 3]
            filtered = []
            if keywords:
                for p in cached_posts:
                    text_to_check = (p.get("title", "") + " " + p.get("description", "")).lower()
                    if any(k in text_to_check for k in keywords):
                        filtered.append(p)
            
            results = filtered if filtered else cached_posts
            print(f"ℹ️ Loaded {len(results)} fallback posts from local cache '{cache_path}'", file=sys.stderr)
            return results[:max_items]
        except Exception as e:
            print(f"❌ Failed to load local cache fallback: {e}", file=sys.stderr)

    return []


def main():
    start = datetime.now()

    posts = scrape_reddit(SEARCH_QUERY, MAX_ITEMS)

    if not posts:
        print("⚠️ No posts returned. The Reddit search query yielded no results, or all connection attempts failed.")
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