

API_KEY = "3012e40ac1e94ac6bd271a3baa140c5b"
import logging
import os

import requests

logger = logging.getLogger(__name__)

# Load from environment variable — never hardcode secrets
# API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_URL = "https://newsapi.org/v2/everything"
MAX_ARTICLES = 10


def get_news(stock_name: str) -> list[str]:
    """
    Fetch recent news article titles for a given stock name.

    Args:
        stock_name: The stock or company name to search for.

    Returns:
        A list of unique article titles (up to MAX_ARTICLES).
        Returns an empty list on error or if no articles are found.
    """
    if not API_KEY:
        raise EnvironmentError("NEWS_API_KEY environment variable is not set.")

    if not stock_name or not stock_name.strip():
        logger.warning("get_news() called with empty stock_name.")
        return []

    params = {
        "q": stock_name.strip(),
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": API_KEY,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(
                "News API returned status %d: %s",
                response.status_code,
                response.text,
            )
            return []

        data = response.json()

        if "articles" not in data:
            logger.warning("Unexpected API response structure: %s", data)
            return []

        seen = set()
        articles = []

        for article in data["articles"][:MAX_ARTICLES]:
            title = article.get("title", "").strip()
            if title and title not in seen:
                seen.add(title)
                articles.append(title)

        if not articles:
            logger.info("No articles found for query: %s", stock_name)

        return articles

    except requests.exceptions.Timeout:
        logger.error("Request timed out for stock: %s", stock_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.error("Network error fetching news for %s: %s", stock_name, e)
        return []
    except Exception as e:
        logger.exception("Unexpected error in get_news() for %s: %s", stock_name, e)
        return []