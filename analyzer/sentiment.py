import os
import logging
import requests

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

MIN_CONFIDENCE   = 0.6
WORDS_PER_CHUNK  = 60
MAX_CHUNKS       = 1


# ── TEXT CHUNKING ─────────────────────────────────────────
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


# ── HF API CALL ───────────────────────────────────────────
def _hf_sentiment(texts: list[str]):
    payload = {"inputs": texts}

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )
        data = response.json()

        # HF sometimes wraps results
        if isinstance(data, list) and isinstance(data[0], list):
            return [item[0] for item in data]

        return data

    except Exception as e:
        logger.error("HF API failed: %s", e)
        return []


# ── SCORE CONVERSION ─────────────────────────────────────
def _score_from_result(result):
    # If accidentally string
    if isinstance(result, str):
        result = {"label": result, "score": 1.0}

    # If nested list
    if isinstance(result, list):
        result = result[0]

    label = result.get("label", "").lower()
    score = result.get("score", 0)

    if score < MIN_CONFIDENCE:
        return 0.0
    if label == "positive":
        return score
    if label == "negative":
        return -score
    return 0.0

# ── MAIN BATCH ANALYZER ──────────────────────────────────
def analyze_sentiment_batch(articles: list[dict]) -> list[float]:
    all_texts   = []
    article_map = []  # (article_idx, weight)

    for i, article in enumerate(articles):
        title   = article.get("title",   "") if isinstance(article, dict) else str(article)
        content = article.get("content", "") if isinstance(article, dict) else ""

        # Title — weight 2
        if title and len(title.strip()) >= 10:
            all_texts.append(title[:512])
            article_map.append((i, 2))

        # Content — weight 1
        if content and len(content) > 20:
            for chunk in _build_chunks(content):
                all_texts.append(chunk[:512])
                article_map.append((i, 1))

    if not all_texts:
        return [0.0] * len(articles)

    batch_results = _hf_sentiment(all_texts)

    if not batch_results:
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


# ── SINGLE ARTICLE WRAPPER ───────────────────────────────
def analyze_sentiment(article) -> float:
    return analyze_sentiment_batch([article])[0]