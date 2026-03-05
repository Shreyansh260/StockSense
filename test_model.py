from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    framework="pt"
)

result = classifier("Tesla reports record EV sales")

print(result)