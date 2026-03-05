from django.db import models

# Create your models here.
from django.db import models

class Stock(models.Model):
    name = models.CharField(max_length=100)
    ticker = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class News(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    title = models.TextField()
    sentiment = models.FloatField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()


class SentimentResult(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    score = models.FloatField()
    recommendation = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
