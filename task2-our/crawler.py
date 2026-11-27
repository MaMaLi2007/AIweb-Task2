import os
import time
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urldefrag, urljoin
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, AndGroup, QueryParser



# where to start crawling
root = "https://en.wikipedia.org/wiki/Cognitive_science"
allowed_prefix = "https://en.wikipedia.org/wiki/"

agenda = [root]   # what to crawl next
visited = set()   # does not crawl what already was crawled

# unique -> no urls multiple times; stored -> readable, ID -> identificator
schema = Schema(
    title=TEXT(stored=True), 
    content=TEXT #(stored=True), 
    url= ID(stored=True, unique=True),
)

# create an index in the directory indexdr (the directory must already exist!)
if os.path.exists("indexdir"):
    shutil.rmtree("indexdir", ignore_errors=True)
if not os.path.exists("indexdir"):
    os.makedirs("indexdir")
ix = create_in("indexdir", schema)
writer = ix.writer()

max_pages = 50
pages_crawled = 0
in_memory_index = {}

while agenda and pages_crawled < max_pages:
    url = agenda.pop(0)   # bfs instead of dfs

    # checks if we have already crawled this URL
    if url in visited:
        continue
    visited.add(url)

    # get the page
    r = requests.get(
        url,
        headers={"User-Agent": "AIWebPageCheck/1.0"},
        timeout=15,
    )

    # check the status code and skip if not 200 OK or if it's not an HTML page
    print("Get", r.status_code, r.url)
    if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", "").lower():
        continue

    pages_crawled += 1   # 

    # parse the page and find all links
    soup = BeautifulSoup(r.content, "html.parser")

    # get title and text and teaser
    title = soup.title.get_text() if soup.title else ""#
    
    '''
    teaser = soup.find_all("p")
    text_list = []
    for p in teaser:
        text_list.append(p.get_text())
    '''
    content = soup.get_text()

    writer.add_document(
        title=title,
        content=content,
        url=r.url,
    )

    for link in soup.select("a[href]"):
        # get the absolute URL of the link, and remove any fragment (the part after #)
        target, _ = urldefrag(urljoin(r.url, link["href"]))
        if target.startswith(allowed_prefix):
            article_name = target[len(allowed_prefix):]
            if ":" not in article_name and target not in visited:
                #print("Found ", target)
                agenda.append(target)

try:
    writer.commit() 
except PermissionError:   # works around Error from windowsystem
    time.sleep(0.5)
    try:
        # deletes MAIN.tmp and tells python no to crash if folder doesn't exist
        shutil.rmtree("indexdir/MAIN.tmp", ignore_errors=True)
        writer.commit()
    except Exception:
        pass
