import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

# ── MODEL CACHE ───────────────────────────────────────────
# distilbert-base-uncased-finetuned-sst-2-english
# Only ~67MB vs FinBERT's 440MB — fits in Render free tier (512MB RAM)
# Still strong sentiment accuracy for financial news
_classifier = None

def _get_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Loading sentiment model...")
        _classifier = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            framework="pt",
            device=-1,       # CPU
            truncation=True,
            max_length=512,
        )
        logger.info("Sentiment model loaded.")
    return _classifier


MIN_CONFIDENCE   = 0.6
WORDS_PER_CHUNK  = 60
MAX_CHUNKS       = 1    # 1 chunk per article — fast + low memory


def _build_chunks(content: str) -> list[str]:
    words  = content.split()
    chunks = []
    for i in range(0, len(words), 80):
        chunk = " ".join(words[i:i + WORDS_PER_CHUNK])
        if chunk.strip():
            chunks.append(chunk)
        if len(chunks) >= MAX_CHUNKS:
            break
    return chunks


def _score_from_result(result: dict) -> float:
    """Convert model result to -1.0 to +1.0 float."""
    label = result["label"].lower()
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
    Analyze all articles in a single batch call.
    Returns list of float scores, one per article.
    """
    classifier = _get_classifier()

    all_texts   = []
    article_map = []  # (article_idx, weight)

    for i, article in enumerate(articles):
        title   = article.get("title",   "") if isinstance(article, dict) else str(article)
        content = article.get("content", "") if isinstance(article, dict) else ""

        # Title — weight 2
        if title and len(title.strip()) >= 10:
            all_texts.append(title[:512])
            article_map.append((i, 2))

        # Content chunk — weight 1
        if content and len(content) > 20:
            for chunk in _build_chunks(content):
                all_texts.append(chunk[:512])
                article_map.append((i, 1))

    if not all_texts:
        return [0.0] * len(articles)

    try:
        batch_results = classifier(all_texts, batch_size=8)
    except Exception as e:
        logger.error("Batch inference failed: %s", e)
        return [0.0] * len(articles)

    weighted_sum = [0.0] * len(articles)
    total_weight = [0.0] * len(articles)

    for (art_idx, weight), result in zip(article_map, batch_results):
        score = _score_from_result(result)
        if score != 0.0:
            weighted_sum[art_idx] += score * weight
            total_weight[art_idx] += weight

    scores = []
    for i in range(len(articles)):
        if total_weight[i] > 0:
            scores.append(round(weighted_sum[i] / total_weight[i], 4))
        else:
            scores.append(0.0)

    return scores


def analyze_sentiment(article) -> float:
    """Single article wrapper for backward compatibility."""
    return analyze_sentiment_batch([article])[0]