import requests
import os

API_KEY = os.getenv("API_KEY")

def fetch_news_by_tag(TAGS):
    for each_tag in TAGS.split(','):
        TAG = each_tag.strip().lstrip('#')
        url = f"https://gnews.io/api/v4/search?q={TAG}&lang=en&token={API_KEY}"

        response = requests.get(url)
        data = response.json()

        for article in data.get("articles", []):
            print(article["title"])
            print(article["url"])
            print("------")
