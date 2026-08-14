"""VOZ (voz.vn) forum source for last30days.

Keyless XenForo scrape for Vietnam's largest tech forum. voz.vn blocks
guest search, forum listings, per-forum RSS, and sitemaps behind
Cloudflare (HTTP 403), but two endpoints stay open (probed 2026-06-12):

- ``https://voz.vn/forums/-/index.rss`` - sitewide RSS of the latest
  active threads (title, link, pubDate, author, forum, body, replies).
- ``https://voz.vn/t/<slug>.<id>/`` - thread page 1 HTML.

Discovery is therefore tiered:

1. Web-search backend (Brave/Exa/Serper/Parallel) restricted to
   ``site:voz.vn`` - best coverage, key-gated, reuses ``grounding``.
2. Sitewide RSS filtered by token overlap with the query - keyless but
   thin (the feed holds only the ~18 most recently active threads).

Every discovered thread URL is then fetched (page 1 only) to extract
dates, reply counts, reaction counts, and the top posts used as inline
quotes. All tiers degrade silently to an empty result - a Cloudflare
policy change must never fail the run.

Activation gate: opt-in. ``pipeline.available_sources`` only includes
``voz`` when ``INCLUDE_SOURCES`` contains ``voz`` or the plan requests
it explicitly.
"""

from __future__ import annotations

import html as htmllib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from . import grounding, http, log
from .relevance import token_overlap_relevance

BASE_URL = "https://voz.vn"
RSS_URL = f"{BASE_URL}/forums/-/index.rss"

# Threads scraped (page 1) per search, by depth.
DEPTH_CONFIG = {
    "quick": 5,
    "default": 10,
    "deep": 20,
}

# Replies kept per thread as inline quotes. Matches the 5-comment cap
# used by Reddit/HN/YouTube/TikTok/GitHub enrichment.
POSTS_PER_THREAD = 5

# Minimum token-overlap score for an RSS item to count as on-topic.
RSS_RELEVANCE_FLOOR = 0.1

# Minimum token-overlap score for a SINGLE post inside an off-topic thread
# to surface as its own item. VOZ chatter about a niche topic often lives in
# random replies of general threads ("Chuyện trò linh tinh", gold clubs),
# so search also scans page-1 posts of recently-active threads whose TITLE
# does not match. Slightly stricter than the thread floor - a lone reply
# must stand on its own words.
POST_RELEVANCE_FLOOR = 0.2

# Cap of post-level items emitted per search, across all scanned threads.
MAX_POST_ITEMS = 10

THREAD_TIMEOUT = 10
RSS_TIMEOUT = 10

_THREAD_URL_RE = re.compile(r"https://voz\.vn/t/[^\s\"'<>]+?\.(\d+)/?")


def _log(msg: str) -> None:
    log.source_log("VOZ", msg)


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return htmllib.unescape(re.sub(r"\s+", " ", text)).strip()


def _to_utc_date(value: Optional[str]) -> Optional[str]:
    """Parse an RFC-2822 or ISO-8601 timestamp (VOZ posts are GMT+7) into
    a UTC YYYY-MM-DD string. Returns None when unparseable."""
    if not value:
        return None
    value = value.strip()
    dt: Optional[datetime] = None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


def _canonical_thread_url(url: str) -> Optional[str]:
    """Normalize any voz.vn thread URL (utm params, page suffix, post
    anchors) to ``https://voz.vn/t/<slug>.<id>/``."""
    match = re.search(r"(https://voz\.vn/t/[^\s\"'<>?#]+?\.\d+)", url)
    if not match:
        return None
    return match.group(1) + "/"


def _thread_id(url: str) -> Optional[str]:
    match = _THREAD_URL_RE.search(url)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Tier 1: web-search backend discovery (key-gated)
# ---------------------------------------------------------------------------

def _discover_via_backend(
    query: str, from_date: str, to_date: str, config: Dict[str, Any],
) -> List[str]:
    try:
        items, _ = grounding.web_search(
            f"site:voz.vn {query}", (from_date, to_date), config
        )
    except Exception as exc:  # backend errors must not kill the run
        _log(f"backend discovery failed: {exc}")
        return []
    urls: List[str] = []
    for item in items or []:
        url = _canonical_thread_url(str(item.get("url") or ""))
        if url and url not in urls:
            urls.append(url)
    if urls:
        _log(f"backend discovery: {len(urls)} thread urls")
    return urls


# ---------------------------------------------------------------------------
# Tier 2: sitewide RSS (keyless)
# ---------------------------------------------------------------------------

def _fetch_rss() -> List[Dict[str, Any]]:
    body = http.get_text(RSS_URL, timeout=RSS_TIMEOUT, retries=1, accept="application/rss+xml")
    if not body:
        _log("rss fetch failed (Cloudflare or network)")
        return []
    entries: List[Dict[str, Any]] = []
    for chunk in re.findall(r"<item>(.*?)</item>", body, re.S):
        def _field(pattern: str) -> str:
            m = re.search(pattern, chunk, re.S)
            return m.group(1).strip() if m else ""

        link = _canonical_thread_url(htmllib.unescape(_field(r"<link>([^<]+)</link>")))
        if not link:
            continue
        content = _field(r"<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>")
        forum = _field(r"<category[^>]*><!\[CDATA\[(.*?)\]\]></category>")
        replies = _field(r"<slash:comments>(\d+)</slash:comments>")
        entries.append(
            {
                "url": link,
                "title": htmllib.unescape(_field(r"<title>([^<]*)</title>")),
                "date": _to_utc_date(_field(r"<pubDate>([^<]+)</pubDate>")),
                "author": _field(r"<dc:creator>([^<]*)</dc:creator>"),
                "forum": htmllib.unescape(forum),
                "body": _strip_tags(content)[:1200],
                "replies": int(replies) if replies.isdigit() else 0,
            }
        )
    return entries


def _discover_via_rss(query: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """Return ALL recently-active threads in the window, scored against the
    query. Threads whose title/body misses the topic are NOT dropped here:
    niche chatter on VOZ often hides in replies of general threads, so the
    search scans their page-1 posts too. The score just orders the scrape
    budget (likely hits first)."""
    candidates: List[Dict[str, Any]] = []
    for entry in _fetch_rss():
        date = entry.get("date")
        if date and not (from_date <= date <= to_date):
            continue
        score = token_overlap_relevance(query, f"{entry['title']} {entry['body']}")
        entry["relevance"] = round(score, 2)
        candidates.append(entry)
    candidates.sort(key=lambda e: e["relevance"], reverse=True)
    if candidates:
        on_topic = sum(1 for e in candidates if e["relevance"] >= RSS_RELEVANCE_FLOOR)
        _log(f"rss discovery: {len(candidates)} threads in window ({on_topic} title-matched)")
    return candidates


# ---------------------------------------------------------------------------
# Thread page-1 scrape
# ---------------------------------------------------------------------------

_BB_MARKER = '<div class="bbWrapper">'


def _extract_bb_wrappers(html_text: str, max_len: int = 20000) -> List[str]:
    """Extract bbWrapper post bodies with balanced div counting.

    Quoted messages nest extra ``<div>`` blocks inside bbWrapper, so a
    non-greedy ``(.*?)</div>`` regex truncates replies at the first nested
    close tag. Walk div open/close pairs instead.
    """
    out: List[str] = []
    idx = 0
    while True:
        start = html_text.find(_BB_MARKER, idx)
        if start == -1:
            break
        pos = start + len(_BB_MARKER)
        depth = 1
        end = None
        for m in re.finditer(r"<div\b|</div>", html_text[pos:pos + max_len]):
            depth += 1 if m.group(0) != "</div>" else -1
            if depth == 0:
                end = pos + m.start()
                break
        if end is None:
            end = min(pos + max_len, len(html_text))
        out.append(html_text[pos:end])
        idx = end
    return out


def _count_reactions(fragment: str) -> int:
    """Each reactionsBar line lists up to 3 names plus 'and N other(s)'."""
    total = 0
    for bar in re.findall(r"reactionsBar-link[^>]*>(.*?)</a>", fragment, re.S):
        names = len(re.findall(r"<bdi>", bar))
        other = re.search(r"and (\d+) other", bar)
        total += names + (int(other.group(1)) if other else 0)
    return total


def _parse_posts(html_text: str) -> List[Dict[str, Any]]:
    """Split page-1 HTML into per-post dicts.

    Splits on the OUTER post article only ('message message--post'); the
    nested '<article class="message-body ...">' wrapper stays inside its
    chunk. Each post carries its own author, UTC date, quote-stripped body,
    reaction count, and permalink anchor - the unit the post-level search
    scans.
    """
    chunks = re.split(r'<article class="message message--post', html_text)[1:]
    posts: List[Dict[str, Any]] = []
    for chunk in chunks:
        author_m = re.search(r'data-author="([^"]+)"', chunk)
        anchor_m = re.search(r'id="js-post-(\d+)"', chunk)
        time_m = re.search(r'<time[^>]*datetime="([^"]+)"', chunk)
        bodies = _extract_bb_wrappers(chunk)
        body = ""
        if bodies:
            # Strip quoted-message blocks so a post carries its own words,
            # not the "<author> said:" boilerplate.
            body = _strip_tags(
                re.sub(r"<blockquote.*?</blockquote>", " ", bodies[0], flags=re.S)
            )
        posts.append(
            {
                "author": author_m.group(1) if author_m else "",
                "anchor": f"post-{anchor_m.group(1)}" if anchor_m else "",
                "date": _to_utc_date(time_m.group(1)) if time_m else None,
                "body": body,
                "reactions": _count_reactions(chunk),
            }
        )
    return posts


def _parse_thread_html(url: str, html_text: str) -> Optional[Dict[str, Any]]:
    title_match = re.search(
        r'<h1[^>]*class="[^"]*p-title-value[^"]*"[^>]*>(.*?)</h1>', html_text, re.S
    )
    if not title_match:
        return None
    # Drop prefix labels ("thắc mắc", "thảo luận", ...) so the title is clean.
    title_html = re.sub(
        r'<span class="label[^"]*"[^>]*>.*?</span>', " ", title_match.group(1), flags=re.S
    )
    title = _strip_tags(title_html)

    forum_match = re.search(r'href="/f/([a-z0-9%.~_-]+)\.(\d+)/"', html_text)
    forum = forum_match.group(1).replace("-", " ") if forum_match else ""

    all_posts = _parse_posts(html_text)
    first = all_posts[0] if all_posts else {}

    top_replies: List[Dict[str, Any]] = []
    for post in all_posts[1:]:
        text = (post.get("body") or "").strip()
        if not text:
            continue
        top_replies.append({"author": post["author"], "body": text[:400]})
        if len(top_replies) >= POSTS_PER_THREAD:
            break

    return {
        "url": url,
        "title": title,
        "forum": forum,
        "author": first.get("author") or "",
        "date": first.get("date"),
        "body": (first.get("body") or "")[:1200],
        # Replies on page 1; threads longer than one page undercount, which
        # is acceptable for an engagement signal (page 2+ is blocked).
        "replies": max(0, len(all_posts) - 1),
        "reactions": sum(p["reactions"] for p in all_posts),
        "posts": top_replies,
        "all_posts": all_posts,
    }


def _scrape_thread(url: str) -> Optional[Dict[str, Any]]:
    html_text = http.get_text(url, timeout=THREAD_TIMEOUT, retries=1, accept="text/html")
    if not html_text:
        return None
    try:
        return _parse_thread_html(url, html_text)
    except Exception as exc:  # malformed page must not kill the run
        _log(f"thread parse failed ({url}): {exc}")
        return None


# ---------------------------------------------------------------------------
# Public API (pipeline contract)
# ---------------------------------------------------------------------------

def search_voz(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search voz.vn threads. Returns ``{"results": [...]}``; never raises."""
    config = config or {}
    if not topic or not topic.strip():
        return {"results": []}
    limit = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])

    # Backend-discovered URLs are explicit search hits - treat as on-topic.
    # RSS candidates are ordered likely-hits-first by _discover_via_rss.
    seeds: Dict[str, Dict[str, Any]] = {}
    for url in _discover_via_backend(topic, from_date, to_date, config):
        seeds[url] = {"url": url, "from_backend": True}
    for entry in _discover_via_rss(topic, from_date, to_date):
        seeds.setdefault(entry["url"], {}).update(entry)

    results: List[Dict[str, Any]] = []
    post_items = 0
    for url, seed in list(seeds.items())[:limit]:
        scraped = _scrape_thread(url)
        merged = {**seed, **{k: v for k, v in (scraped or {}).items() if v}}
        if not merged.get("title"):
            continue
        all_posts = merged.pop("all_posts", [])
        thread_rel = round(
            token_overlap_relevance(topic, f"{merged['title']} {merged.get('body', '')}"), 2
        )

        if merged.get("from_backend") or thread_rel >= RSS_RELEVANCE_FLOOR:
            # Thread-level hit: one item for the whole thread (as before).
            merged.pop("from_backend", None)
            if not merged.get("date"):
                # Undated threads can't satisfy the last-30-days contract.
                continue
            if not (from_date <= merged["date"] <= to_date):
                continue
            merged["relevance"] = max(thread_rel, float(merged.get("relevance") or 0.0))
            results.append(merged)
            continue

        # Off-topic thread title: scan its page-1 posts for on-topic replies.
        # A vozer mentioning the topic in a random thread ("Chuyện trò linh
        # tinh", gold clubs) is still signal - emit each such post as its own
        # item with a permalink anchor.
        for post in all_posts:
            if post_items >= MAX_POST_ITEMS:
                break
            body = (post.get("body") or "").strip()
            date = post.get("date")
            if not body or not date or not (from_date <= date <= to_date):
                continue
            score = token_overlap_relevance(topic, body)
            if score < POST_RELEVANCE_FLOOR:
                continue
            anchor = post.get("anchor") or ""
            results.append(
                {
                    "kind": "post",
                    "url": f"{url}{anchor}" if anchor else url,
                    "title": f"{post.get('author') or 'vozer'} trong: {merged['title']}",
                    "forum": merged.get("forum") or "",
                    "author": post.get("author") or "",
                    "date": date,
                    "body": body[:1200],
                    "replies": 0,
                    "reactions": int(post.get("reactions") or 0),
                    "posts": [],
                    "relevance": round(score, 2),
                }
            )
            post_items += 1

    _log(
        f"search '{topic}' -> {len(results)} items "
        f"({len(results) - post_items} threads, {post_items} posts, depth={depth})"
    )
    return {"results": results}


def parse_voz_response(response: Dict[str, Any], query: str = "") -> List[Dict[str, Any]]:
    """Parse a ``search_voz`` envelope into dicts for ``_normalize_voz``."""
    raw = response.get("results") if isinstance(response, dict) else None
    if not isinstance(raw, list):
        return []
    items: List[Dict[str, Any]] = []
    for i, thread in enumerate(raw):
        if not isinstance(thread, dict):
            continue
        url = str(thread.get("url") or "")
        thread_id = _thread_id(url)
        if not thread_id:
            continue
        is_post = thread.get("kind") == "post"
        item_id = thread_id
        if is_post:
            anchor_m = re.search(r"post-(\d+)", url)
            item_id = f"{thread_id}-{anchor_m.group(1)}" if anchor_m else f"{thread_id}-p{i + 1}"
        title = str(thread.get("title") or "").strip()
        body = str(thread.get("body") or "").strip()
        relevance = thread.get("relevance")
        if relevance is None:
            relevance = token_overlap_relevance(query, f"{title} {body}") if query else 0.5
        forum = str(thread.get("forum") or "").strip()
        kind_label = "VOZ reply" if is_post else "VOZ thread"
        items.append(
            {
                "id": item_id,
                "title": title or f"VOZ thread {i + 1}",
                "url": url,
                "forum": forum,
                "author": str(thread.get("author") or ""),
                "date": thread.get("date"),
                "body": body,
                "engagement": {
                    "replies": int(thread.get("replies") or 0),
                    "reactions": int(thread.get("reactions") or 0),
                },
                "posts": thread.get("posts") or [],
                "relevance": round(float(relevance), 2),
                "why_relevant": (
                    f"{kind_label} in {forum}" if forum else kind_label
                ),
            }
        )
    return items
