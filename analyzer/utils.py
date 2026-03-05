def aggregate_sentiment(scores):
    if not scores:
        return 0

    # Filter out neutral (0) scores before averaging
    non_neutral = [s for s in scores if s != 0]

    if not non_neutral:
        return 0

    return sum(non_neutral) / len(non_neutral)