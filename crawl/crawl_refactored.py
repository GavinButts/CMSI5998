import os
import time
import mechanicalsoup
import redis
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase

class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_links(self, page, links):
        with self.driver.session() as session:
            session.write_transaction(self._create_links, page, links)

    def clear_db(self):
        print("Clearing Neo4j database")
        with self.driver.session() as session:
            session.write_transaction(self._clear_db)

    @staticmethod
    def _create_links(tx, page, links):
        page = page.decode('utf-8')
        tx.run("MERGE (p:Page {url: $page})", page=page)
        for link in links:
            tx.run("MERGE (l:Page {url: $link}) "
                   "MERGE (p)-[:LINKS_TO]->(l)",
                   link=link, page=page)

    @staticmethod
    def _clear_db(tx):
        tx.run("MATCH (n) DETACH DELETE n")


def index_to_elasticsearch(es, url, html):
    print(f"Indexing URL to Elasticsearch: {url}")
    es.index(index='scrape', document={'url': url, 'html': html})


def crawl_page(browser, redis_client, es, neo4j_handler, url):
    url_str = url.decode('utf-8')
    print(f"Downloading URL: {url_str}")
    browser.open(url_str)

    index_to_elasticsearch(es, url_str, str(browser.page))

    print("Extracting links")
    links = ["https://en.wikipedia.org" + a.get("href") for a in browser.page.find_all("a")
             if a.get("href") and a.get("href").startswith("/wiki/") and ':' not in a.get("href")]

    print(f"Pushing links to Redis: {links}")
    redis_client.lpush("links", *links)

    neo4j_handler.add_links(url, links)

    if "https://en.wikipedia.org/wiki/Jesus" in links:
        print("Found the target page!")
        return True
    return False

def main():
    start_time = time.time()

    NEO4J_URI = 0 #[Redacted]
    NEO4J_USERNAME = 0 #[Redacted]
    NEO4J_PASSWORD = 0 #[Redacted]

    neo4j_handler = Neo4jHandler(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    neo4j_handler.clear_db()

    ELASTICSEARCH_HOST = 0 #[Redacted]
    ELASTICSEARCH_API_KEY = 0 #[Redacted]

    print(f"Connecting to Elasticsearch: {ELASTICSEARCH_HOST}")
    es = Elasticsearch(
        hosts=[ELASTICSEARCH_HOST],
        api_key=ELASTICSEARCH_API_KEY
    )

    REDIS_HOST = 0 #[Redacted]
    REDIS_PORT = 0 #[Redacted]
    REDIS_USERNAME = 0 #[Redacted]
    REDIS_PASSWORD = 0 #[Redacted]

    print(f"Connecting to Redis: {REDIS_HOST}:{REDIS_PORT} with username: {REDIS_USERNAME}")
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USERNAME, password=REDIS_PASSWORD)
        redis_client.ping()
        redis_client.flushall()
    except redis.ConnectionError as e:
        print(f"Could not connect to Redis. Error: {e}")
        return

    browser = mechanicalsoup.StatefulBrowser()

    start_url = "https://en.wikipedia.org/wiki/Buddhism"
    print(f"Starting crawl with URL: {start_url}")
    redis_client.lpush("links", start_url)

    found_target = False
    try:
        while True:
            link = redis_client.rpop("links")
            if not link:
                break
            if crawl_page(browser, redis_client, es, neo4j_handler, link):
                found_target = True
                break

        if not found_target:
            print("Target page not found during crawl.")
    finally:
        neo4j_handler.close()
        redis_client.close()

    end_time = time.time()
    print(f"Process took {end_time - start_time} seconds")

if __name__ == "__main__":
    main()
