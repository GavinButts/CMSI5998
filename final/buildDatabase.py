import os
from newsapi import NewsApiClient
from pymongo import MongoClient
import datetime

# Initialize NewsAPI client using environment variable
newsapi = NewsApiClient(api_key=os.getenv('NEWSAPI_KEY'))

# List of computer science-related terms
cs_terms = []
with open('cs_terms.txt', 'r') as file:
    for line in file:
        line = line.strip()
        cs_terms.append(line)
    print(cs_terms)

# Fetch articles on a specific term
def fetch_articles(query, from_date, to_date, language='en', page_size=100):
    all_articles = newsapi.get_everything(q=query,
                                          from_param=from_date,
                                          to=to_date,
                                          language=language,
                                          page_size=page_size)
    return all_articles['articles']

# Initialize MongoDB client using environment variable
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['news_db']
collection = db['articles']

# Fetch and store articles for each term
def store_articles(terms, from_date, to_date):
    for term in terms:
        print(f'Fetching articles for term: {term}')
        try:
            articles = fetch_articles(term, from_date, to_date)
            if articles:
                for article in articles:
                    article['query'] = term  # Add the query term to each article document
                    collection.update_one({'url': article['url']}, {'$set': article}, upsert=True)
                print(f'{len(articles)} articles stored/updated for term: {term}.')
            else:
                print(f'No articles found for term: {term}.')
        except Exception as e:
            print(f'Error fetching/storing articles for term: {term}. Error: {e}')

# Parameters
from_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
to_date = datetime.datetime.now().strftime('%Y-%m-%d')

# Fetch and store articles for each term in the list
store_articles(cs_terms, from_date, to_date)
