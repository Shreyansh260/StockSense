from django.contrib import admin
from django.contrib import admin
from .models import Stock, News, SentimentResult

admin.site.register(Stock)
admin.site.register(News)
admin.site.register(SentimentResult)
