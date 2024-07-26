import os
import time
import mechanicalsoup as ms
import redis
from elasticsearch import Elasticsearch, helpers
from neo4j import GraphDatabase

class Neo4JConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_links(self, page, links):
        with self.driver.session() as session:
            session.execute_write(self._create_links, page, links)

    def flush_db(self):
        print("clearing graph db")
        with self.driver.session() as session:
            session.execute_write(self._flush_db)

    @staticmethod
    def _create_links(tx, page, links):
        page = page.decode('utf-8')
        tx.run("MERGE (p:Page { url: $page })", page=page)
        for link in links:
            tx.run("MERGE (l:Page { url: $link }) "
                   "MERGE (p)-[:LINKS_TO]->(l)",
                   link=link, page=page)

    @staticmethod
    def _flush_db(tx):
        tx.run("MATCH (a) -[r]-> () DELETE a, r")
        tx.run("MATCH (a) DELETE a")


def write_to_elastic(es, url, html):
    print(f"Indexing URL to Elasticsearch: {url}")
    es.index(index='scrape', document={'url': url, 'html': html})


def crawl(browser, r, es, neo, url):
    url_str = url.decode('utf-8')
    print(f"Downloading URL: {url_str}")
    browser.open(url_str)

    write_to_elastic(es, url_str, str(browser.page))

    print("Parsing for more links")
    a_tags = browser.page.find_all("a")
    hrefs = [a.get("href") for a in a_tags]

    wikipedia_domain = "https://en.wikipedia.org"
    links = [wikipedia_domain + a for a in hrefs if a and a.startswith("/wiki/") and not ':' in a]

    print(f"Pushing links onto Redis: {links}")
    r.lpush("links", *links)

    neo.add_links(url, links)

    if "https://en.wikipedia.org/wiki/Jesus" in links:
        print("Found the target page!")
        return True
    return False

### MAIN ###

start_time = time.time()

# Update Neo4j connection details
NEO4J_URI = 0 #[Redacted]
NEO4J_USERNAME = 0 #[Redacted]
NEO4J_PASSWORD = 0 #[Redacted]

neo = Neo4JConnector(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
neo.flush_db()

ELASTICSEARCH_HOST = 0 #[Redacted]
ELASTICSEARCH_API_KEY = 0 #[Redacted]

print(f"Connecting to Elasticsearch: {ELASTICSEARCH_HOST}")
es = Elasticsearch(
    cloud_id=ELASTICSEARCH_HOST,
    api_key=ELASTICSEARCH_API_KEY
)

# Redis connection details
REDIS_HOST = 0 #[Redacted]
REDIS_PORT = 0 #[Redacted]
REDIS_USERNAME = 0 #[Redacted]
REDIS_PASSWORD = 0 #[Redacted]

print(f"Connecting to Redis: {REDIS_HOST}:{REDIS_PORT} with username: {REDIS_USERNAME}")
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USERNAME, password=REDIS_PASSWORD)
    r.ping()  # Test the connection to Redis
    r.flushall()
except redis.ConnectionError as e:
    print(f"Could not connect to Redis. Error: {e}")
    exit(1)

browser = ms.StatefulBrowser()

start_url = "https://en.wikipedia.org/wiki/Buddhism"
print(f"Starting crawl with URL: {start_url}")
r.lpush("links", start_url)

found_target = False
try:
    while link := r.rpop("links"):
        if crawl(browser, r, es, neo, link):
            found_target = True
            break

    if not found_target:
        print("Target page not found during crawl.")
finally:
    neo.close()
    try:
        if r:
            r.close()
    except Exception as e:
        print(f"Error closing Redis connection: {e}")

end_time = time.time()
print(f"Process took {end_time - start_time} seconds")
