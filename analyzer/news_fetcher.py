API_KEY = "3012e40ac1e94ac6bd271a3baa140c5b"
import os
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# API_KEY      = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"
MAX_ARTICLES = 10
FETCH_TIMEOUT = 5     # seconds per article fetch (reduced from 8)
MAX_WORKERS   = 5     # parallel article fetches


def _fetch_article_text(url: str) -> str:
    """
    Fetch and extract the main text from a single article URL.
    Returns empty string on any failure.
    """
    if not url:
        return ""
    try:
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        body = (
            soup.find("article") or
            soup.find("div", class_=lambda c: c and any(
                k in c.lower() for k in ["article", "content", "story", "body", "post"]
            )) or
            soup.find("main")
        )

        text = body.get_text(separator=" ", strip=True) if body else \
               " ".join(p.get_text(strip=True) for p in soup.find_all("p"))

        return " ".join(text.split())[:3000]

    except Exception:
        return ""


def _process_article(article: dict) -> dict:
    """
    Given a raw NewsAPI article dict, fetch its full content and return
    a clean {title, content} dict.
    """
    title       = article.get("title", "").strip()
    url         = article.get("url", "")
    description = article.get("description", "") or ""

    full_text = _fetch_article_text(url)

    if not full_text:
        full_text = description

    return {
        "title":   title,
        "content": full_text.strip(),
    }


def get_news(stock_name: str) -> list[dict]:
    """
    Fetch recent news for a stock.
    Article content is fetched in parallel for speed.
    Returns list of {title, content} dicts.
    """
    if not API_KEY:
        raise EnvironmentError("NEWS_API_KEY environment variable is not set.")

    if not stock_name or not stock_name.strip():
        return []

    params = {
        "q":        stock_name.strip(),
        "language": "en",
        "sortBy":   "publishedAt",
        "apiKey":   API_KEY,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)

        if response.status_code != 200:
            logger.error("News API %d: %s", response.status_code, response.text)
            return []

        data = response.json()

        if "articles" not in data:
            return []

        # Deduplicate by title
        seen     = set()
        raw_list = []

        for art in data["articles"][:MAX_ARTICLES]:
            title = art.get("title", "").strip()
            if title and title not in seen:
                seen.add(title)
                raw_list.append(art)

        if not raw_list:
            return []

        # ── Fetch article content IN PARALLEL ────────────────────
        results  = [None] * len(raw_list)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(_process_article, art): i
                for i, art in enumerate(raw_list)
            }
            for future in as_completed(future_to_idx):
                idx         = future_to_idx[future]
                results[idx] = future.result()

        # Filter out any None results
        return [r for r in results if r and r["title"]]

    except requests.exceptions.Timeout:
        logger.error("NewsAPI timeout for: %s", stock_name)
        return []
    except Exception as e:
        logger.exception("Error in get_news() for %s: %s", stock_name, e)
        return []