# API Source:

News API: https://newsapi.org

Provides articles relating to specific topics other various filters. Iterating through various filters, the data could then be transfered to a database. The resulting database could then be used to train some cool models.

See --proposal_img1-- for visualization of API in use.  

To use, 
- first install and connect to any relevant database systems needed.   
- Next, set API key and location of usage.   
- Set necessary filters.   
- Call API and move data to database.  


Here is example usage of the API:

```
import requests
import json

# Replace 'your_api_key' with your actual NewsAPI key
api_key = 'your_api_key'
url = 'https://newsapi.org/v2/top-headlines'

# Parameters for the API request
params = {
    'country': 'us',   # Fetches headlines from the US
    'apiKey': api_key  # Your API key
}

# Making the API request
response = requests.get(url, params=params)

# Checking if the request was successful
if response.status_code == 200:
    # Parsing the response JSON
    data = response.json()
    
    # Extracting articles
    articles = data.get('articles', [])
    
    # Creating a document to save the articles
    with open('news_articles.json', 'w') as file:
        json.dump(articles, file, indent=4)
    
    print(f"Collected {len(articles)} articles.")
else:
    print(f"Failed to fetch articles. Status code: {response.status_code}")
    print(response.text)
```
