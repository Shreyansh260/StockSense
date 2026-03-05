from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    framework="pt"
)

def analyze_sentiment(text):
    if not text or len(text.strip()) < 10:
        return 0

    result = classifier(text[:512])[0]  # FinBERT max 512 tokens

    label = result["label"]
    score = result["score"]

    # Only trust high-confidence predictions
    if score < 0.6:
        return 0

    if label == "positive":
        return score
    elif label == "negative":
        return -score
    else:
        return 0