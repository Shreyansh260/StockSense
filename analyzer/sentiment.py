import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

# ── MODEL CACHE ───────────────────────────────────────────
# Loaded once at startup, reused for every request.
# Django apps.py ready() is the right place, but module-level
# with a None guard works fine for development and production.
_classifier = None

def _get_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Loading FinBERT model...")
        _classifier = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            framework="pt",
            device=-1,          # CPU; change to 0 if you have a GPU
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT model loaded.")
    return _classifier


MIN_CONFIDENCE = 0.6
WORDS_PER_CHUNK = 100
MAX_CHUNKS_PER_ARTICLE = 4   # reduced from 6 → faster


def _build_chunks(content: str) -> list[str]:
    """Split content into word-based chunks."""
    words  = content.split()
    chunks = []
    step   = 80

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + WORDS_PER_CHUNK])
        if chunk.strip():
            chunks.append(chunk)
        if len(chunks) >= MAX_CHUNKS_PER_ARTICLE:
            break

    return chunks


def _score_from_result(result: dict) -> float:
    """Convert a single FinBERT result dict to a float score."""
    label = result["label"]
    score = result["score"]

    if score < MIN_CONFIDENCE:
        return 0.0
    if label == "positive":
        return score
    if label == "negative":
        return -score
    return 0.0


def analyze_sentiment_batch(articles: list[dict]) -> list[float]:
    """
    Analyze a list of article dicts in a SINGLE batch inference call.
    This is much faster than calling the model once per chunk.

    Each article dict has 'title' and 'content' keys.
    Returns a list of float scores (one per article).
    """
    classifier = _get_classifier()

    # ── Build all texts to score ──────────────────────────
    # Structure: list of (article_idx, weight, text)
    all_texts   = []
    article_map = []   # maps each text index → (article_idx, weight)

    for i, article in enumerate(articles):
        title   = article.get("title",   "") if isinstance(article, dict) else str(article)
        content = article.get("content", "") if isinstance(article, dict) else ""

        # Title — weight 2
        if title and len(title.strip()) >= 10:
            all_texts.append(title[:512])
            article_map.append((i, 2))

        # Content chunks — weight 1 each
        if content and len(content) > 20:
            for chunk in _build_chunks(content):
                all_texts.append(chunk[:512])
                article_map.append((i, 1))

    if not all_texts:
        return [0.0] * len(articles)

    # ── Single batch inference call ───────────────────────
    try:
        batch_results = classifier(all_texts, batch_size=16)
    except Exception as e:
        logger.error("FinBERT batch inference failed: %s", e)
        return [0.0] * len(articles)

    # ── Aggregate scores per article ─────────────────────
    weighted_sum    = [0.0] * len(articles)
    total_weight    = [0.0] * len(articles)

    for (art_idx, weight), result in zip(article_map, batch_results):
        score = _score_from_result(result)
        if score != 0.0:
            weighted_sum[art_idx]  += score * weight
            total_weight[art_idx]  += weight

    scores = []
    for i in range(len(articles)):
        if total_weight[i] > 0:
            scores.append(round(weighted_sum[i] / total_weight[i], 4))
        else:
            scores.append(0.0)

    return scores


def analyze_sentiment(article) -> float:
    """
    Single-article wrapper for backward compatibility.
    Internally uses batch processing.
    """
    return analyze_sentiment_batch([article])[0]